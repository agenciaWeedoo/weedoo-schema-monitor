"""
monitor.py — Script principal do agente de monitoramento de Schema Markup
Weedoo Marketing Digital | Medicina Endocanabinoide

Execução: toda segunda-feira às 06:00 BRT via GitHub Actions.
Fluxo: lê URLs → busca sitemap → valida schemas → compara concorrentes
       → gera relatório Markdown → salva em /reports → publica Issue GitHub.
"""

import os
import sys
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date

import requests
from bs4 import BeautifulSoup

# Garantir que o diretório src esteja no path de importação
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    AUTOR_NOME,
    AUTOR_PORTFOLIO,
    AUTOR_URL_SOBRE,
    AUTOR_LINKEDIN,
    DELAY_SEGUNDOS,
    HEADERS_PADRAO,
    ORG_NOME,
    ORG_URL,
    SITEMAP_URL,
    agrupar_schemas_por_tipo,
    buscar_pagina,
    checar_robots,
    extrair_schemas,
    obter_tipo_schema,
)
from comparador import comparar_concorrentes
from relatorio import gerar_relatorio, publicar_issue_github, salvar_relatorio

# ─── Configuração de logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("monitor")

# ─── Caminhos de arquivos ──────────────────────────────────────────────────────
RAIZ = Path(__file__).parent.parent
CONFIG_DIR = RAIZ / "config"
REPORTS_DIR = RAIZ / "reports"
URLS_FILE = CONFIG_DIR / "urls_weedoo.txt"

# ─── Schemas esperados por tipo de página ─────────────────────────────────────
# Usado para detectar schemas ausentes onde deveriam estar presentes
SCHEMAS_ESPERADOS: dict[str, list[str]] = {
    "home": ["WebSite", "Organization"],
    "blog_listagem": ["WebSite", "BreadcrumbList"],
    "artigo": ["Article", "BreadcrumbList"],
    "servicos": ["WebPage", "BreadcrumbList", "Organization"],
    "sobre": ["Person", "WebPage", "BreadcrumbList"],
}

# ─── Campos obrigatórios por tipo de Schema ────────────────────────────────────
# Baseados na documentação oficial do Google para rich results
CAMPOS_OBRIGATORIOS: dict[str, list[str]] = {
    "Article": [
        "headline", "author", "datePublished",
        "dateModified", "publisher", "mainEntityOfPage", "image",
    ],
    "WebSite": ["name", "url", "potentialAction"],
    "Organization": ["name", "url", "logo", "sameAs"],
    "Person": ["name", "url", "sameAs"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "HowTo": ["step", "name"],
    "MedicalWebPage": ["name", "url", "specialty"],
    "Physician": ["name", "url", "medicalSpecialty"],
    "VideoObject": ["name", "description", "thumbnailUrl", "uploadDate"],
    "WebPage": ["name", "url"],
    "NewsArticle": ["headline", "author", "datePublished", "publisher"],
    "BlogPosting": ["headline", "author", "datePublished", "publisher"],
}


# ─── Leitura de URLs ───────────────────────────────────────────────────────────

def ler_urls_weedoo() -> list[str]:
    """
    Lê as URLs base da Weedoo do arquivo config/urls_weedoo.txt.
    Ignora linhas em branco e comentários (linhas que começam com #).
    """
    if not URLS_FILE.exists():
        logger.error("Arquivo de URLs não encontrado: %s", URLS_FILE)
        return []

    urls = []
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        for linha in f:
            url = linha.strip()
            if url and not url.startswith("#"):
                urls.append(url)

    logger.info("✅ %d URLs base carregadas de %s", len(urls), URLS_FILE.name)
    return urls


def obter_urls_sitemap(
    sitemap_url: str,
    visitados: set[str] | None = None,
    max_artigos: int = 10,
) -> list[str]:
    """
    Extrai URLs de posts do sitemap.xml de forma recursiva.
    Suporta sitemap index (que aponta para outros sitemaps).
    Filtra apenas URLs de artigos do blog (/blog/<slug>/).

    Args:
        sitemap_url: URL do sitemap ou sitemap index.
        visitados: Conjunto de sitemaps já visitados (evita loops).
        max_artigos: Número máximo de artigos a retornar.

    Returns:
        Lista de URLs de artigos do blog.
    """
    if visitados is None:
        visitados = set()

    if sitemap_url in visitados:
        return []
    visitados.add(sitemap_url)

    logger.info("📄 Processando sitemap: %s", sitemap_url)
    urls: list[str] = []

    try:
        import time
        time.sleep(DELAY_SEGUNDOS)
        resposta = requests.get(sitemap_url, headers=HEADERS_PADRAO, timeout=20)
        resposta.raise_for_status()

        root = ET.fromstring(resposta.content)
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Verifica se é um sitemap index (contém referências a outros sitemaps)
        sitemaps_filhos = root.findall("sm:sitemap", ns)
        if sitemaps_filhos:
            for sm in sitemaps_filhos:
                loc = sm.find("sm:loc", ns)
                if loc is not None and loc.text:
                    urls.extend(
                        obter_urls_sitemap(loc.text.strip(), visitados, max_artigos)
                    )
                    if len(urls) >= max_artigos:
                        break
        else:
            # Sitemap de URLs comuns
            # Detectar se este é um sitemap específico de posts do WordPress
            # (ex.: post-sitemap1.xml, post-sitemap2.xml) — contém apenas posts
            eh_post_sitemap = "post-sitemap" in sitemap_url.lower()

            # Padrões de URL que NÃO são artigos (taxonomias, arquivos, admin)
            excluir_padroes = [
                "/wp-admin/", "/feed/", "/author/", "/tag/", "/tags/",
                "/category/", "/categoria/", "/page/", "?",
            ]

            for url_el in root.findall("sm:url", ns):
                loc = url_el.find("sm:loc", ns)
                if loc is not None and loc.text:
                    url = loc.text.strip()

                    # Pular URLs com padrões de não-artigo
                    if any(p in url for p in excluir_padroes):
                        continue

                    if eh_post_sitemap:
                        # Sitemap de posts: incluir todos (são todos artigos por definição)
                        urls.append(url)
                    elif "/blog/" in url and url.rstrip("/") not in (
                        "https://www.weedoo.med.br/blog",
                        "https://www.weedoo.med.br/blog/",
                    ):
                        # Sitemap geral: filtrar por prefixo /blog/ no URL
                        urls.append(url)

    except ET.ParseError as exc:
        logger.error("Erro ao parsear XML do sitemap %s: %s", sitemap_url, exc)
    except requests.exceptions.RequestException as exc:
        logger.error("Erro ao buscar sitemap %s: %s", sitemap_url, exc)

    logger.info("  → %d URLs de artigos encontradas em %s", len(urls), sitemap_url)
    return urls[:max_artigos]


# ─── Validações específicas de E-E-A-T ────────────────────────────────────────

def validar_autor(author_data: dict | list | None, url_pagina: str) -> tuple[list[str], list[str]]:
    """
    Valida os dados do autor Carlos Macedo segundo os critérios E-E-A-T.
    Verifica: nome, URL da página Sobre, LinkedIn e Portfólio no sameAs.

    Returns:
        Tupla (erros, avisos) — erros bloqueiam rich snippets, avisos são recomendações.
    """
    erros: list[str] = []
    avisos: list[str] = []

    if not author_data:
        erros.append("Campo 'author' está ausente no schema Article")
        return erros, avisos

    # Normalizar: author pode ser objeto único ou lista de objetos
    autores = author_data if isinstance(author_data, list) else [author_data]

    encontrou_carlos = False
    for autor in autores:
        if not isinstance(autor, dict):
            avisos.append(
                f"'author' contém um valor não-objeto: {str(autor)[:60]!r}. "
                "Deve ser um objeto Person."
            )
            continue

        nome = autor.get("name", "")
        if "Carlos" in nome and "Macedo" in nome:
            encontrou_carlos = True

            # ── Verificar @type ────────────────────────────────────────────────
            tipo_autor = str(autor.get("@type", ""))
            if "Person" not in tipo_autor:
                erros.append(
                    f"author.@type deve ser 'Person', encontrado: {tipo_autor!r}"
                )

            # ── Verificar URL da página Sobre ──────────────────────────────────
            url_autor = autor.get("url", "")
            if not url_autor:
                erros.append(
                    "author.url ausente — deve apontar para a página Sobre do autor: "
                    f"'{AUTOR_URL_SOBRE}'"
                )
            elif url_autor.rstrip("/") != AUTOR_URL_SOBRE.rstrip("/"):
                erros.append(
                    f"author.url incorreta.\n"
                    f"  Esperado : {AUTOR_URL_SOBRE!r}\n"
                    f"  Encontrado: {url_autor!r}"
                )

            # ── Verificar sameAs (LinkedIn e Portfólio) ────────────────────────
            same_as_raw = autor.get("sameAs", [])
            same_as: list[str] = (
                [same_as_raw] if isinstance(same_as_raw, str) else same_as_raw
            )

            if AUTOR_LINKEDIN not in same_as:
                erros.append(
                    f"author.sameAs não contém o LinkedIn do {AUTOR_NOME}.\n"
                    f"  Adicionar: {AUTOR_LINKEDIN!r}"
                )
            if AUTOR_PORTFOLIO not in same_as:
                erros.append(
                    f"author.sameAs não contém o portfólio do {AUTOR_NOME}.\n"
                    f"  Adicionar: {AUTOR_PORTFOLIO!r}"
                )

    if not encontrou_carlos:
        nomes = [
            a.get("name", "?") if isinstance(a, dict) else str(a)
            for a in autores
        ]
        erros.append(
            f"Autor '{AUTOR_NOME}' não encontrado no campo 'author'. "
            f"Autores presentes: {nomes}"
        )

    return erros, avisos


def validar_publisher(publisher_data: dict | list | None) -> tuple[list[str], list[str]]:
    """
    Valida os dados do publisher (Organization Weedoo).
    Campos críticos: name, logo, @type.
    """
    erros: list[str] = []
    avisos: list[str] = []

    if not publisher_data:
        erros.append("Campo 'publisher' ausente (obrigatório para Article rich snippets)")
        return erros, avisos

    # Normalizar: pode ser lista
    if isinstance(publisher_data, list):
        publisher_data = publisher_data[0] if publisher_data else {}

    if not isinstance(publisher_data, dict):
        erros.append(
            f"'publisher' não é um objeto válido: {str(publisher_data)[:60]!r}"
        )
        return erros, avisos

    # Verificar @type
    tipo = str(publisher_data.get("@type", ""))
    if "Organization" not in tipo:
        avisos.append(
            f"publisher.@type deve ser 'Organization', encontrado: {tipo!r}"
        )

    # Verificar nome
    nome = publisher_data.get("name", "")
    if ORG_NOME.lower() not in nome.lower():
        erros.append(
            f"publisher.name não contém '{ORG_NOME}'. Encontrado: {nome!r}"
        )

    # Verificar logo (essencial para rich snippets de Article)
    logo = publisher_data.get("logo")
    if not logo:
        erros.append(
            "publisher.logo ausente — "
            "obrigatório para exibição de rich snippets do tipo Article"
        )
    elif isinstance(logo, dict) and not logo.get("url"):
        erros.append(
            "publisher.logo.url ausente — "
            "a logo deve ser um ImageObject com a URL da imagem"
        )

    return erros, avisos


# ─── Validação de schema individual ───────────────────────────────────────────

def validar_schema_item(item: dict, tipo: str, url: str) -> dict:
    """
    Valida um único item de schema contra campos obrigatórios e regras de negócio.

    Args:
        item: Dicionário com os dados do schema extraído.
        tipo: @type do schema (ex.: 'Article', 'Organization').
        url: URL da página de origem (para contexto nas mensagens de erro).

    Returns:
        Dicionário com: tipo, erros, avisos, campos_presentes, completude_pct.
    """
    erros: list[str] = []
    avisos: list[str] = []
    campos_presentes: list[str] = []

    # ── Verificar campos obrigatórios genéricos ────────────────────────────────
    campos_req = CAMPOS_OBRIGATORIOS.get(tipo, [])
    for campo in campos_req:
        valor = item.get(campo)
        if valor is not None and valor not in ("", [], {}):
            campos_presentes.append(campo)
        else:
            erros.append(f"Campo obrigatório ausente ou vazio: '{campo}'")

    # ── Validações específicas por tipo de schema ──────────────────────────────

    if tipo in ("Article", "BlogPosting", "NewsArticle"):
        # Validar autor E-E-A-T (regra de ouro da Weedoo)
        erros_autor, avisos_autor = validar_autor(item.get("author"), url)
        erros.extend(erros_autor)
        avisos.extend(avisos_autor)

        # Validar publisher
        erros_pub, avisos_pub = validar_publisher(item.get("publisher"))
        erros.extend(erros_pub)
        avisos.extend(avisos_pub)

        # Campos recomendados (não obrigatórios, mas melhoram E-E-A-T)
        if not item.get("speakable"):
            avisos.append(
                "Campo 'speakable' ausente — melhora acessibilidade e pode "
                "favorecer featured snippets de voz"
            )
        if not item.get("articleSection"):
            avisos.append(
                "Campo 'articleSection' ausente — ajuda o Google a categorizar o conteúdo"
            )
        if not item.get("keywords"):
            avisos.append(
                "Campo 'keywords' ausente — importante para relevância temática"
            )

    elif tipo == "Organization":
        same_as_raw = item.get("sameAs", [])
        same_as = [same_as_raw] if isinstance(same_as_raw, str) else same_as_raw
        if not any("linkedin" in s.lower() for s in same_as):
            avisos.append(
                "Organization.sameAs não inclui o LinkedIn da Weedoo"
            )
        if not item.get("address"):
            avisos.append(
                "Organization.address ausente — recomendado para SEO local"
            )
        if not item.get("telephone"):
            avisos.append(
                "Organization.telephone ausente — recomendado para SEO local e contato"
            )

    elif tipo == "WebSite":
        action = item.get("potentialAction")
        if isinstance(action, dict):
            if not action.get("query-input"):
                erros.append(
                    "WebSite.potentialAction.query-input ausente — "
                    "necessário para Sitelinks Search Box do Google"
                )
        elif not action:
            erros.append(
                "WebSite.potentialAction ausente — "
                "impede a exibição da Sitelinks Search Box"
            )

    elif tipo == "BreadcrumbList":
        items_lista = item.get("itemListElement", [])
        if not items_lista:
            erros.append(
                "BreadcrumbList.itemListElement está vazio — "
                "nenhum nível de navegação definido"
            )
        elif not isinstance(items_lista, list):
            erros.append(
                "BreadcrumbList.itemListElement deve ser uma lista de ListItem"
            )

    elif tipo == "FAQPage":
        main_entity = item.get("mainEntity", [])
        if not main_entity:
            erros.append(
                "FAQPage.mainEntity está vazio — "
                "deve conter ao menos uma Question com Answer"
            )

    elif tipo == "MedicalWebPage":
        if not item.get("reviewedBy"):
            avisos.append(
                "MedicalWebPage.reviewedBy ausente — "
                "essencial para E-E-A-T em conteúdo de saúde (YMYL)"
            )
        if not item.get("lastReviewed"):
            avisos.append(
                "MedicalWebPage.lastReviewed ausente — "
                "data da última revisão médica aumenta confiabilidade"
            )

    # ── Calcular completude ────────────────────────────────────────────────────
    total_req = len(campos_req)
    completude = round(len(campos_presentes) / total_req * 100) if total_req else 100

    return {
        "tipo": tipo,
        "presente": True,
        "erros": erros,
        "avisos": avisos,
        "campos_presentes": campos_presentes,
        "campos_obrigatorios": campos_req,
        "completude_pct": completude,
    }


# ─── Análise de uma página da Weedoo ──────────────────────────────────────────

def extrair_metadados_pagina(html: str, url: str) -> dict:
    """
    Extrai metadados ricos da página para personalizar os schemas recomendados.
    Coleta: título, descrição, imagem, datas, headings e excerto do conteúdo.
    """
    soup = BeautifulSoup(html, "html.parser")

    def _meta(prop: str | None = None, name: str | None = None) -> str:
        if prop:
            el = soup.find("meta", property=prop)
        else:
            el = soup.find("meta", attrs={"name": name})
        return (el.get("content") or "").strip() if el else ""

    # Título: prioridade og:title > <title> > <h1>
    titulo = _meta(prop="og:title")
    if not titulo and soup.title:
        titulo = soup.title.get_text()
        for sep in [" | Weedoo", " - Weedoo", "| Weedoo", "– Weedoo", " — Weedoo"]:
            titulo = titulo.replace(sep, "").strip()
    if not titulo:
        h1 = soup.find("h1")
        titulo = h1.get_text().strip() if h1 else ""

    descricao = _meta(prop="og:description") or _meta(name="description")
    imagem = _meta(prop="og:image")
    data_pub = (
        _meta(prop="article:published_time")
        or _meta(name="article:published_time")
        or _meta(prop="og:article:published_time")
    )
    data_mod = (
        _meta(prop="article:modified_time")
        or _meta(name="article:modified_time")
        or _meta(prop="og:article:modified_time")
        or data_pub  # fallback para data de publicação
    )

    # Headings do artigo (H2 e H3) para geração de FAQs
    headings = [
        h.get_text().strip()
        for h in soup.find_all(["h2", "h3"])
        if len(h.get_text().strip()) > 5
    ][:8]

    # Excerto do conteúdo para contexto das FAQs
    paragrafos = [
        p.get_text().strip()
        for p in soup.find_all("p")
        if len(p.get_text().strip()) > 80
    ][:5]

    return {
        "titulo": titulo.strip(),
        "descricao": descricao,
        "imagem": imagem,
        "data_publicacao": data_pub,
        "data_modificacao": data_mod,
        "headings": headings,
        "conteudo": " ".join(paragrafos)[:800],
    }



def _classificar_tipo_pagina(url: str) -> str:
    """Classifica o tipo de página com base na URL para definir schemas esperados."""
    url_lower = url.lower().rstrip("/")
    base = ORG_URL.rstrip("/")

    if url_lower == base:
        return "home"
    if url_lower == f"{base}/blog":
        return "blog_listagem"
    if "/blog/" in url_lower:
        return "artigo"
    if "/nossos-servicos" in url_lower or "/servicos" in url_lower:
        return "servicos"
    if "/sobre" in url_lower:
        return "sobre"
    return "pagina_generica"


def analisar_pagina_weedoo(url: str) -> dict:
    """
    Analisa todos os dados estruturados de uma página da Weedoo.
    Valida campos, verifica schemas esperados e retorna resultado completo.

    Args:
        url: URL completa da página a analisar.

    Returns:
        Dicionário com schemas encontrados, erros, avisos e metadados.
    """
    logger.info("🔍 Analisando: %s", url)
    tipo_pagina = _classificar_tipo_pagina(url)

    resultado: dict = {
        "url": url,
        "tipo_pagina": tipo_pagina,
        "acessivel": False,
        "schemas_encontrados": {},
        "todos_erros": [],
        "todos_avisos": [],
        "tipos_presentes": [],
        "metadados": {},
    }

    # Buscar HTML
    html = buscar_pagina(url)
    if not html:
        resultado["todos_erros"].append(f"Página inacessível (falha na requisição HTTP): {url}")
        return resultado

    resultado["acessivel"] = True

    # Extrair schemas
    dados = extrair_schemas(html, url)
    todos_items = dados.get("json-ld", []) + dados.get("microdata", [])

    if not todos_items:
        resultado["todos_erros"].append(
            "Nenhum dado estruturado (JSON-LD ou Microdata) encontrado nesta página. "
            "Isso prejudica severamente a visibilidade em rich snippets."
        )
        return resultado

    # Validar cada schema encontrado
    for item in todos_items:
        tipo = obter_tipo_schema(item)
        validacao = validar_schema_item(item, tipo, url)
        resultado["schemas_encontrados"][tipo] = validacao
        resultado["todos_erros"].extend(validacao["erros"])
        resultado["todos_avisos"].extend(validacao["avisos"])

    resultado["tipos_presentes"] = list(resultado["schemas_encontrados"].keys())

    # Verificar schemas esperados mas ausentes para este tipo de página
    esperados = SCHEMAS_ESPERADOS.get(tipo_pagina, ["BreadcrumbList"])
    for tipo_esperado in esperados:
        if tipo_esperado not in resultado["tipos_presentes"]:
            resultado["todos_erros"].append(
                f"Schema '{tipo_esperado}' ausente — "
                f"esperado para páginas do tipo '{tipo_pagina}'"
            )

    logger.info(
        "  → Tipos: %s | Erros: %d | Avisos: %d",
        resultado["tipos_presentes"],
        len(resultado["todos_erros"]),
        len(resultado["todos_avisos"]),
    )
    return resultado


# ─── Ponto de entrada ──────────────────────────────────────────────────────────

def main() -> None:
    """
    Função principal do agente de monitoramento.
    Orquestra todas as etapas: coleta → análise → comparação → relatório → publicação.
    """
    logger.info("=" * 65)
    logger.info("🚀  WEEDOO SEO BOT — Monitoramento Semanal de Schema Markup")
    logger.info("📅  Data: %s", date.today().strftime("%d/%m/%Y"))
    logger.info("=" * 65)

    # ── ETAPA 1: Coletar URLs da Weedoo ───────────────────────────────────────
    logger.info("\n📋 ETAPA 1/6 — Coletando URLs base da Weedoo...")
    urls_base = ler_urls_weedoo()
    if not urls_base:
        logger.critical("Nenhuma URL base encontrada. Verifique config/urls_weedoo.txt.")
        sys.exit(1)

    # ── ETAPA 2: Extrair posts do sitemap ─────────────────────────────────────
    logger.info("\n🗺️  ETAPA 2/6 — Extraindo posts do sitemap.xml...")
    urls_sitemap = obter_urls_sitemap(SITEMAP_URL, max_artigos=8)
    # Consolidar URLs únicas, preservando a ordem (base primeiro, depois sitemap)
    todas_urls = list(dict.fromkeys(urls_base + urls_sitemap))
    logger.info("📊 Total de URLs a analisar: %d", len(todas_urls))

    # ── ETAPA 3: Analisar schemas da Weedoo ───────────────────────────────────
    logger.info("\n🔬 ETAPA 3/6 — Analisando schemas das páginas Weedoo...")
    resultados_weedoo: list[dict] = []
    for url in todas_urls:
        resultado = analisar_pagina_weedoo(url)
        resultados_weedoo.append(resultado)

    erros_total = sum(len(r["todos_erros"]) for r in resultados_weedoo)
    logger.info("  → Análise Weedoo concluída: %d erros encontrados", erros_total)

    # ── ETAPA 4: Comparar com concorrentes ────────────────────────────────────
    logger.info("\n🥊 ETAPA 4/6 — Analisando schemas dos concorrentes...")
    resultados_concorrentes = comparar_concorrentes()

    # ── ETAPA 5: Gerar relatório ───────────────────────────────────────────────
    logger.info("\n📝 ETAPA 5/6 — Gerando relatório Markdown...")
    relatorio_md = gerar_relatorio(resultados_weedoo, resultados_concorrentes)

    # ── ETAPA 6a: Salvar relatório em /reports ─────────────────────────────────
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    caminho_salvo = salvar_relatorio(relatorio_md, REPORTS_DIR)
    logger.info("💾 Relatório salvo em: %s", caminho_salvo)

    # ── ETAPA 6b: Publicar Issue no GitHub ────────────────────────────────────
    logger.info("\n🐙 ETAPA 6/6 — Publicando Issue no GitHub...")
    publicar_issue_github(relatorio_md)

    logger.info("\n✅ Monitoramento semanal concluído com sucesso!")
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
