"""
utils.py — Utilitários compartilhados para o agente de monitoramento de Schema Markup
Weedoo Marketing Digital | Medicina Endocanabinoide
"""

import time
import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

try:
    import extruct
    from w3lib.html import get_base_url
except ImportError as exc:
    raise ImportError(
        f"Dependência não encontrada: {exc}. "
        "Execute: pip install extruct w3lib"
    ) from exc

logger = logging.getLogger(__name__)

# ─── Constantes de configuração ────────────────────────────────────────────────

DELAY_SEGUNDOS: float = 2.0  # Delay ético entre requisições (segundos)

USER_AGENT = (
    "WeedooSEOMonitorBot/1.0 "
    "(+https://www.weedoo.med.br/sobre/; "
    "bot de auditoria SEO para uso interno; "
    "contato: contato@weedoo.med.br)"
)

HEADERS_PADRAO: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.5",
    # Sem "br": o requests só descomprime Brotli com o pacote brotli instalado.
    # Com "br", o Cloudflare devolvia HTML comprimido ilegível e o monitor
    # concluía (errado) que as páginas não tinham dados estruturados.
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ─── Dados do autor para validação E-E-A-T ────────────────────────────────────

AUTOR_NOME = "Carlos Macedo"
AUTOR_URL_SOBRE = "https://www.weedoo.med.br/sobre/"
AUTOR_LINKEDIN = "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"
AUTOR_PORTFOLIO = "https://agenciaweedoo.github.io/my-portifolio/"

# ─── Dados da organização ─────────────────────────────────────────────────────

ORG_NOME = "Weedoo"
ORG_URL = "https://www.weedoo.med.br/"
SITEMAP_URL = "https://www.weedoo.med.br/sitemaps.xml"  # URL correta conforme robots.txt

# ─── Cache de robots.txt (evita múltiplas leituras do mesmo domínio) ──────────
_cache_robots: dict[str, RobotFileParser] = {}


def checar_robots(url: str) -> bool:
    """
    Verifica se o bot tem permissão para acessar a URL via robots.txt.
    Retorna True se o acesso for permitido, False caso contrário.
    O resultado por domínio é armazenado em cache para evitar requisições redundantes.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    if robots_url not in _cache_robots:
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            import urllib.request as _req
            opener = _req.build_opener()
            opener.addheaders = [("User-Agent", USER_AGENT)]
            _req.install_opener(opener)
            rp.read()
            _cache_robots[robots_url] = rp
            logger.debug("robots.txt carregado: %s", robots_url)
        except Exception as exc:
            logger.warning(
                "Não foi possível ler robots.txt de %s: %s. "
                "Assumindo acesso permitido.",
                robots_url, exc
            )
            # Se não for possível ler, assume acesso permitido (padrão seguro)
            return True

    return _cache_robots[robots_url].can_fetch(USER_AGENT, url)


_SINAIS_DESAFIO_CLOUDFLARE = (
    "cf-chl-",              # formulário/JS do desafio
    "Just a moment...",     # título da página de desafio
    "Attention Required! | Cloudflare",
)


def buscar_pagina_info(url: str, timeout: int = 20) -> dict:
    """
    Busca uma página com delay ético e respeitando robots.txt, e devolve
    o contexto da resposta — não só o HTML.

    Returns:
        Dicionário com:
          html      — HTML da página, ou None
          status    — código HTTP (None se não houve resposta)
          url_final — URL depois dos redirecionamentos
          bloqueio  — None | "robots_txt" | "cloudflare" | "http_erro" | "timeout" | "conexao"
    """
    info: dict = {"html": None, "status": None, "url_final": url, "bloqueio": None}

    if not checar_robots(url):
        logger.warning("Acesso bloqueado pelo robots.txt: %s", url)
        info["bloqueio"] = "robots_txt"
        return info

    try:
        time.sleep(DELAY_SEGUNDOS)
        logger.debug("Buscando: %s", url)
        resposta = requests.get(url, headers=HEADERS_PADRAO, timeout=timeout)
        info["status"] = resposta.status_code
        info["url_final"] = resposta.url

        # Detectar encoding para evitar problemas com caracteres especiais
        if resposta.encoding is None or resposta.encoding.lower() in ("iso-8859-1", "latin-1"):
            resposta.encoding = resposta.apparent_encoding or "utf-8"

        # Página de desafio do Cloudflare: não é a página real, então não pode
        # ser lida como "página sem dados estruturados".
        if resposta.status_code in (403, 503) and any(
            s in resposta.text for s in _SINAIS_DESAFIO_CLOUDFLARE
        ):
            logger.error(
                "Desafio do Cloudflare em %s — a página real não foi lida. "
                "Libere o User-Agent WeedooSEOMonitorBot numa regra do WAF.", url,
            )
            info["bloqueio"] = "cloudflare"
            return info

        resposta.raise_for_status()
        info["html"] = resposta.text

    except requests.exceptions.Timeout:
        logger.error("Timeout ao buscar %s (>%ds)", url, timeout)
        info["bloqueio"] = "timeout"
    except requests.exceptions.ConnectionError:
        logger.error("Erro de conexão ao buscar %s", url)
        info["bloqueio"] = "conexao"
    except requests.exceptions.HTTPError as exc:
        codigo = exc.response.status_code
        dica = ""
        if codigo in (403, 503):
            dica = " — possível bloqueio Cloudflare (desative Browser Integrity Check no painel)"
        elif codigo == 404:
            dica = " — URL não encontrada, verifique config/urls_weedoo.txt"
        elif codigo == 429:
            dica = " — rate limit, aumente DELAY_SEGUNDOS em utils.py"
        logger.error("Erro HTTP %d ao buscar %s%s", codigo, url, dica)
        info["bloqueio"] = "http_erro"
    except requests.exceptions.RequestException as exc:
        logger.error("Erro inesperado ao buscar %s: %s", url, exc)
        info["bloqueio"] = "conexao"

    return info


def buscar_pagina(url: str, timeout: int = 20) -> str | None:
    """
    Busca o HTML de uma página com delay ético e respeitando robots.txt.
    Atalho para buscar_pagina_info() quando só o HTML interessa.

    Returns:
        String com o HTML da página, ou None em caso de erro/bloqueio.
    """
    return buscar_pagina_info(url, timeout)["html"]


def extrair_schemas(html: str, url: str) -> dict:
    """
    Extrai todos os dados estruturados de uma página HTML usando extruct.
    Suporta JSON-LD, Microdata, RDFa e Open Graph.

    Args:
        html: Conteúdo HTML da página.
        url: URL original (necessária para resolver URLs relativas).

    Returns:
        Dicionário com listas de schemas por sintaxe (json-ld, microdata, etc.).
    """
    try:
        base_url = get_base_url(html, url)
        dados = extruct.extract(
            html,
            base_url=base_url,
            syntaxes=["json-ld", "microdata", "rdfa", "opengraph"],
            uniform=True,
        )
        return dados
    except Exception as exc:
        logger.error("Erro ao extrair schemas de %s: %s", url, exc)
        return {"json-ld": [], "microdata": [], "rdfa": [], "opengraph": []}


def obter_tipo_schema(item: dict) -> str:
    """
    Retorna o @type principal de um item de schema.
    Ex.: ["Article", "NewsArticle"] → "Article". Para todos, use obter_tipos_schema().
    """
    return obter_tipos_schema(item)[0]


def agrupar_schemas_por_tipo(items: list[dict]) -> dict[str, list[dict]]:
    """
    Agrupa uma lista de schemas pelo valor do @type.
    Útil para verificar rapidamente se um tipo específico está presente.
    """
    grupos: dict[str, list[dict]] = {}
    for item in expandir_itens(items):
        for tipo in obter_tipos_schema(item):
            grupos.setdefault(tipo, []).append(item)
    return grupos


# ─── Normalização dos itens extraídos ─────────────────────────────────────────

# Tipos do schema.org que descrevem a moldura da página (cabeçalho, rodapé,
# bloco de anúncio) e não rendem rich result. Ficam fora das comparações.
TIPOS_ESTRUTURAIS = frozenset({"WPAdBlock", "WPHeader", "WPFooter", "WPSideBar", "SiteNavigationElement"})


def expandir_itens(items: list) -> list[dict]:
    """
    Abre os blocos com @graph (formato usado por Yoast, RankMath e pelo tema
    da Weedoo) em itens individuais. Sem isso, um @graph inteiro com
    Organization, WebSite, Person, FAQPage etc. vira um único item sem @type
    e nada dentro dele é validado.
    """
    saida: list[dict] = []
    pilha = list(items)
    while pilha:
        item = pilha.pop(0)
        if isinstance(item, list):
            pilha[0:0] = item
            continue
        if not isinstance(item, dict):
            continue
        grafo = item.get("@graph")
        if isinstance(grafo, list):
            pilha[0:0] = grafo
            if not item.get("@type"):
                continue
        saida.append(item)
    return saida


def obter_tipos_schema(item: dict) -> list[str]:
    """
    Todos os @type de um item, sem prefixo de URL.
    Ex.: ["Organization", "ProfessionalService"] → os dois, não só o primeiro.
    """
    tipo = item.get("@type")
    tipos = tipo if isinstance(tipo, list) else [tipo]
    limpos = []
    for t in tipos:
        if not t:
            continue
        t = str(t).rsplit("/", 1)[-1]  # "http://schema.org/Article" → "Article"
        if t not in limpos:
            limpos.append(t)
    return limpos or ["Desconhecido"]


def mesclar_por_id(items: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    """
    Junta nós que declaram o mesmo @id (no JSON-LD eles são o MESMO objeto,
    como o Google também entende) e devolve (itens, índice por @id).

    Itens sem nenhuma propriedade além de @type (ex.: o <body itemscope
    itemtype="WebPage"> de muitos temas) são descartados: não dizem nada.
    """
    indice: dict[str, dict] = {}
    saida: list[dict] = []
    for item in items:
        if not any(k for k in item if not k.startswith("@")) and "@id" not in item:
            continue
        ident = item.get("@id")
        if not ident:
            saida.append(dict(item))
            continue
        if ident not in indice:
            novo = dict(item)
            indice[ident] = novo
            saida.append(novo)
            continue
        alvo = indice[ident]
        tipos = obter_tipos_schema(alvo) + [t for t in obter_tipos_schema(item) if t not in obter_tipos_schema(alvo)]
        tipos = [t for t in tipos if t != "Desconhecido"]
        for k, v in item.items():
            if k not in alvo or alvo[k] in ("", [], {}, None):
                alvo[k] = v
        if tipos:
            alvo["@type"] = tipos if len(tipos) > 1 else tipos[0]
    return saida, indice


def resolver_referencia(valor, indice: dict[str, dict]):
    """
    Troca {"@id": "..."} pelo nó completo do índice, quando existir.
    Funciona com objeto único ou lista. Mantém o valor original se não achar.
    """
    def _um(v):
        if isinstance(v, dict) and set(v.keys()) <= {"@id", "@type"} and v.get("@id") in indice:
            return indice[v["@id"]]
        return v
    if isinstance(valor, list):
        return [_um(v) for v in valor]
    return _um(valor)
