"""
comparador.py — Análise e comparação de schemas dos concorrentes
Weedoo Marketing Digital | Medicina Endocanabinoide

Este módulo:
1. Carrega a lista de concorrentes do arquivo de configuração.
2. Faz scraping ético da home, blog e até 3 artigos recentes de cada concorrente.
3. Extrai todos os tipos de schema utilizados por cada um.
4. Detecta presença de campos E-E-A-T (author, publisher) e schemas médicos.
"""

import json
import logging
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from utils import (
    DELAY_SEGUNDOS,
    HEADERS_PADRAO,
    agrupar_schemas_por_tipo,
    buscar_pagina,
    buscar_via_wayback,
    extrair_schemas,
    obter_tipo_schema,
)

logger = logging.getLogger("comparador")

# ─── Configuração ──────────────────────────────────────────────────────────────
CONFIG_DIR = Path(__file__).parent.parent / "config"
CONCORRENTES_FILE = CONFIG_DIR / "concorrentes.json"

# Tipos de schema que são relevantes para a análise comparativa
TIPOS_MEDICOS = frozenset({"MedicalWebPage", "Physician", "MedicalCondition", "Drug", "DietarySupplement"})
TIPOS_EEEAT = frozenset({"Person", "Organization"})
TIPOS_RICH_SNIPPETS = frozenset({"FAQPage", "HowTo", "VideoObject", "Recipe", "Event", "BreadcrumbList"})


# ─── Carregamento de configuração ─────────────────────────────────────────────

def carregar_concorrentes() -> list[dict]:
    """
    Carrega a lista de concorrentes do arquivo config/concorrentes.json.
    Retorna lista vazia (com log de erro) se o arquivo não existir.
    """
    if not CONCORRENTES_FILE.exists():
        logger.error("Arquivo de concorrentes não encontrado: %s", CONCORRENTES_FILE)
        return []

    try:
        with open(CONCORRENTES_FILE, "r", encoding="utf-8") as f:
            concorrentes = json.load(f)
        logger.info("✅ %d concorrentes carregados de %s", len(concorrentes), CONCORRENTES_FILE.name)
        return concorrentes
    except json.JSONDecodeError as exc:
        logger.error("Erro ao parsear %s: %s", CONCORRENTES_FILE.name, exc)
        return []


# ─── Extração de links de artigos ─────────────────────────────────────────────

def extrair_links_artigos_recentes(
    html: str,
    base_url: str,
    limite: int = 3,
) -> list[str]:
    """
    Extrai URLs dos artigos mais recentes de uma página de listagem de blog.
    Usa múltiplas heurísticas para ser compatível com diferentes CMSs
    (WordPress, Webflow, Wix, Squarespace, etc.).

    Args:
        html: HTML da página de listagem do blog.
        base_url: URL base para resolução de links relativos.
        limite: Número máximo de artigos a retornar.

    Returns:
        Lista de URLs de artigos únicos (até `limite`).
    """
    soup = BeautifulSoup(html, "html.parser")
    dominio_base = urlparse(base_url).netloc
    urls_encontradas: list[str] = []
    vistas: set[str] = set()

    # Seletores CSS em ordem de especificidade (do mais específico ao mais genérico)
    # Cobre os padrões mais comuns de CMSs
    seletores = [
        "article a[href]",           # WordPress padrão
        "h2.entry-title a[href]",    # WordPress clássico
        "h2.post-title a[href]",     # Temas populares WordPress
        ".post-title a[href]",
        ".entry-title a[href]",
        ".blog-post-title a[href]",
        ".card-title a[href]",       # Bootstrap / Webflow
        "h2.title a[href]",
        "h3.title a[href]",
        ".article-title a[href]",
        "a.post-link[href]",
        ".blog-list-item a[href]",
        "h2 > a[href]",              # Genérico — h2 com link direto
        "h3 > a[href]",
    ]

    # Fragmentos de URL que indicam que o link NÃO é um artigo
    excluir_padroes = [
        "/tag/", "/tags/",
        "/category/", "/categoria/",
        "/autor/", "/author/",
        "/page/", "/pagina/",
        "?",
        "#",
        ".jpg", ".jpeg", ".png", ".gif", ".pdf",
    ]

    for seletor in seletores:
        for link in soup.select(seletor):
            href = link.get("href", "").strip()

            # Resolver URL relativa
            if href.startswith("/"):
                href = urljoin(base_url, href)
            elif not href.startswith("http"):
                continue

            # Validações
            if urlparse(href).netloc != dominio_base:
                continue  # Link externo
            if href == base_url or href.rstrip("/") == base_url.rstrip("/"):
                continue  # Link para a própria página de listagem
            if any(p in href for p in excluir_padroes):
                continue  # Link de tag, categoria ou arquivo
            if href in vistas:
                continue  # Duplicata

            vistas.add(href)
            urls_encontradas.append(href)

            if len(urls_encontradas) >= limite:
                return urls_encontradas

    logger.debug(
        "Encontrados %d links de artigos em %s",
        len(urls_encontradas),
        base_url,
    )
    return urls_encontradas[:limite]


# ─── Análise de página do concorrente ─────────────────────────────────────────

# Caminhos alternativos comuns para blogs em diferentes CMSs
CAMINHOS_BLOG_ALTERNATIVOS = [
    "/blog", "/artigos", "/conteudo", "/noticias", "/posts",
    "/insights", "/recursos", "/aprenda", "/saude",
]


def _tentar_url_blog(home_url: str, blog_url: str, nome: str) -> str | None:
    """
    Tenta achar a URL real do blog de um concorrente quando a URL configurada
    retorna 404. Testa caminhos alternativos comuns antes de desistir.
    """
    import requests as _req
    from urllib.parse import urlparse as _up

    base = _up(home_url).scheme + "://" + _up(home_url).netloc
    for caminho in CAMINHOS_BLOG_ALTERNATIVOS:
        tentativa = f"{base}{caminho}/"
        if tentativa == blog_url.rstrip("/") + "/":
            continue  # já tentamos essa
        try:
            import time
            time.sleep(DELAY_SEGUNDOS)
            r = _req.get(tentativa, headers=HEADERS_PADRAO, timeout=10, allow_redirects=True)
            if r.status_code == 200:
                logger.info(
                    "  🔄 [%s] URL de blog corrigida: %s → %s",
                    nome, blog_url, tentativa,
                )
                return tentativa
        except Exception:
            pass
    return None


def analisar_pagina_concorrente(url: str, nome_concorrente: str) -> dict:
    """
    Extrai e resume os schemas de uma única página do concorrente.

    Args:
        url: URL da página a analisar.
        nome_concorrente: Nome do concorrente (para logs e relatório).

    Returns:
        Dicionário com tipos encontrados, flags de E-E-A-T e schemas médicos.
    """
    logger.info("  🔍 [%s] %s", nome_concorrente, url)

    resultado: dict = {
        "url": url,
        "concorrente": nome_concorrente,
        "acessivel": False,
        "motivo_inacessivel": None,   # "robots_txt" | "http_erro" | "timeout"
        "tipos_encontrados": [],
        "schemas_detalhados": {},
        "tem_author": False,
        "tem_publisher": False,
        "tem_eeeat_completo": False,   # author + publisher
        "tem_medical_schema": False,   # MedicalWebPage ou Physician
        "tem_rich_snippets": False,    # FAQPage, HowTo, VideoObject, etc.
    }

    # Verificar robots.txt — se bloqueado, tentar Wayback Machine como fallback
    from utils import checar_robots
    html = None
    if not checar_robots(url):
        resultado["motivo_inacessivel"] = "robots_txt"
        logger.warning(
            "  ⚠️  [%s] Bloqueado por robots.txt: %s — tentando Wayback Machine...",
            nome_concorrente, url,
        )
        html = buscar_via_wayback(url)
        if html:
            resultado["motivo_inacessivel"] = None
            resultado["fonte"] = "wayback_machine"
            logger.info("  📦 [%s] Dados obtidos via Wayback Machine (snapshot arquivado)", nome_concorrente)
        else:
            logger.warning("  ❌ [%s] Wayback Machine também indisponível: %s", nome_concorrente, url)
            return resultado
    else:
        html = buscar_pagina(url)
        if not html:
            resultado["motivo_inacessivel"] = "http_erro"
            logger.warning("  ⚠️  [%s] Página inacessível (HTTP): %s", nome_concorrente, url)
            return resultado

    resultado["acessivel"] = True
    dados = extrair_schemas(html, url)
    todos_items = dados.get("json-ld", []) + dados.get("microdata", [])

    tipos_vistos: set[str] = set()
    for item in todos_items:
        tipo = obter_tipo_schema(item)
        tipos_vistos.add(tipo)

        # Registrar campos presentes por tipo (para análise comparativa)
        resultado["schemas_detalhados"][tipo] = {
            "campos": [k for k in item.keys() if not k.startswith("@")],
            "tem_author": "author" in item,
            "tem_publisher": "publisher" in item,
            "tem_datePublished": "datePublished" in item,
            "tem_dateModified": "dateModified" in item,
        }

        # Flags de alto nível
        if "author" in item:
            resultado["tem_author"] = True
        if "publisher" in item:
            resultado["tem_publisher"] = True

    resultado["tipos_encontrados"] = sorted(tipos_vistos)
    resultado["tem_eeeat_completo"] = resultado["tem_author"] and resultado["tem_publisher"]
    resultado["tem_medical_schema"] = bool(tipos_vistos & TIPOS_MEDICOS)
    resultado["tem_rich_snippets"] = bool(tipos_vistos & TIPOS_RICH_SNIPPETS)

    logger.info(
        "    → %d tipos: %s | E-E-A-T: %s | Médico: %s",
        len(resultado["tipos_encontrados"]),
        resultado["tipos_encontrados"],
        "✅" if resultado["tem_eeeat_completo"] else "❌",
        "✅" if resultado["tem_medical_schema"] else "❌",
    )
    return resultado


# ─── Análise completa de todos os concorrentes ────────────────────────────────

def comparar_concorrentes() -> list[dict]:
    """
    Analisa home, blog e artigos recentes de cada concorrente configurado.

    Para cada concorrente:
    - Analisa a página inicial (home).
    - Analisa a página de listagem do blog.
    - Extrai e analisa até 3 artigos recentes.
    - Consolida tipos únicos e flags de autoridade.

    Returns:
        Lista de dicionários com resultado de análise por concorrente.
    """
    concorrentes = carregar_concorrentes()
    if not concorrentes:
        logger.warning("Nenhum concorrente configurado. Pulando comparação.")
        return []

    resultados: list[dict] = []

    for concorrente in concorrentes:
        nome = concorrente.get("nome", "Desconhecido")
        home_url = concorrente.get("home", "")
        blog_url = concorrente.get("blog", "")

        logger.info("\n🥊 Analisando: %s", nome)

        resultado_concorrente: dict = {
            "nome": nome,
            "home_url": home_url,
            "blog_url": blog_url,
            "paginas_analisadas": 0,
            "paginas": [],
            "tipos_unicos": set(),
            "tem_eeeat": False,
            "tem_medical_schema": False,
            "tem_rich_snippets": False,
        }

        # ── Home ──────────────────────────────────────────────────────────────
        if home_url:
            pagina = analisar_pagina_concorrente(home_url, nome)
            resultado_concorrente["paginas"].append(pagina)
            resultado_concorrente["tipos_unicos"].update(pagina["tipos_encontrados"])
            resultado_concorrente["paginas_analisadas"] += 1

        # ── Blog + artigos recentes ────────────────────────────────────────────
        if blog_url:
            pagina_blog = analisar_pagina_concorrente(blog_url, nome)

            # Se o blog retornou 404, tentar URLs alternativas
            if not pagina_blog["acessivel"] and pagina_blog.get("motivo_inacessivel") == "http_erro":
                url_alternativa = _tentar_url_blog(home_url, blog_url, nome)
                if url_alternativa:
                    blog_url = url_alternativa
                    pagina_blog = analisar_pagina_concorrente(blog_url, nome)

            resultado_concorrente["paginas"].append(pagina_blog)
            resultado_concorrente["tipos_unicos"].update(pagina_blog["tipos_encontrados"])
            resultado_concorrente["paginas_analisadas"] += 1

            # Tentar extrair artigos recentes da listagem do blog
            html_blog = buscar_pagina(blog_url)
            if html_blog:
                urls_artigos = extrair_links_artigos_recentes(html_blog, blog_url, limite=3)
                logger.info(
                    "  📰 %d artigos recentes encontrados em %s",
                    len(urls_artigos), blog_url,
                )
                for url_artigo in urls_artigos:
                    pagina_artigo = analisar_pagina_concorrente(url_artigo, nome)
                    resultado_concorrente["paginas"].append(pagina_artigo)
                    resultado_concorrente["tipos_unicos"].update(pagina_artigo["tipos_encontrados"])
                    resultado_concorrente["paginas_analisadas"] += 1

        # ── Consolidar flags ───────────────────────────────────────────────────
        for pagina in resultado_concorrente["paginas"]:
            if pagina.get("tem_eeeat_completo"):
                resultado_concorrente["tem_eeeat"] = True
            if pagina.get("tem_medical_schema"):
                resultado_concorrente["tem_medical_schema"] = True
            if pagina.get("tem_rich_snippets"):
                resultado_concorrente["tem_rich_snippets"] = True

        # Converter set → list para serialização JSON/relatório
        resultado_concorrente["tipos_unicos"] = sorted(
            t for t in resultado_concorrente["tipos_unicos"] if t != "Desconhecido"
        )

        logger.info(
            "  ✅ %s: %d páginas | %d tipos únicos | E-E-A-T: %s | Médico: %s",
            nome,
            resultado_concorrente["paginas_analisadas"],
            len(resultado_concorrente["tipos_unicos"]),
            "✅" if resultado_concorrente["tem_eeeat"] else "❌",
            "✅" if resultado_concorrente["tem_medical_schema"] else "❌",
        )
        resultados.append(resultado_concorrente)

    return resultados
