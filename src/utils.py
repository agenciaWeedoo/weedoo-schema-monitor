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
    "Accept-Encoding": "gzip, deflate, br",
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
SITEMAP_URL = "https://www.weedoo.med.br/sitemap.xml"

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


def buscar_pagina(url: str, timeout: int = 20) -> str | None:
    """
    Busca o HTML de uma página com delay ético e respeitando robots.txt.

    Args:
        url: URL completa da página a ser buscada.
        timeout: Segundos máximos de espera pela resposta.

    Returns:
        String com o HTML da página, ou None em caso de erro/bloqueio.
    """
    if not checar_robots(url):
        logger.warning("Acesso bloqueado pelo robots.txt: %s", url)
        return None

    try:
        time.sleep(DELAY_SEGUNDOS)
        logger.debug("Buscando: %s", url)
        resposta = requests.get(url, headers=HEADERS_PADRAO, timeout=timeout)
        resposta.raise_for_status()

        # Detectar encoding para evitar problemas com caracteres especiais
        if resposta.encoding is None or resposta.encoding.lower() in ("iso-8859-1", "latin-1"):
            resposta.encoding = resposta.apparent_encoding or "utf-8"

        return resposta.text

    except requests.exceptions.Timeout:
        logger.error("Timeout ao buscar %s (>%ds)", url, timeout)
    except requests.exceptions.ConnectionError:
        logger.error("Erro de conexão ao buscar %s", url)
    except requests.exceptions.HTTPError as exc:
        logger.error("Erro HTTP %s ao buscar %s", exc.response.status_code, url)
    except requests.exceptions.RequestException as exc:
        logger.error("Erro inesperado ao buscar %s: %s", url, exc)

    return None


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
    Retorna o @type de um item de schema, normalizando listas para string.
    Ex.: ["Article", "NewsArticle"] → "Article"
    """
    tipo = item.get("@type", "Desconhecido")
    if isinstance(tipo, list):
        return tipo[0] if tipo else "Desconhecido"
    return str(tipo) if tipo else "Desconhecido"


def agrupar_schemas_por_tipo(items: list[dict]) -> dict[str, list[dict]]:
    """
    Agrupa uma lista de schemas pelo valor do @type.
    Útil para verificar rapidamente se um tipo específico está presente.
    """
    grupos: dict[str, list[dict]] = {}
    for item in items:
        tipo = obter_tipo_schema(item)
        grupos.setdefault(tipo, []).append(item)
    return grupos
