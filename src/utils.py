import time
import requests
from urllib.robotparser import RobotFileParser

HEADERS = {
    'User-Agent': 'Weedoo-Schema-Monitor/1.0 (E-E-A-T audit bot; +https://www.weedoo.med.br)'
}
DELAY = 2  # segundos

def pode_rastrear(url):
    """Verifica robots.txt antes de raspar."""
    try:
        dominio = '/'.join(url.split('/')[:3])
        rp = RobotFileParser()
        rp.set_url(f"{dominio}/robots.txt")
        rp.read()
        return rp.can_fetch(HEADERS['User-Agent'], url)
    except:
        return True  # se falhar, assume que pode

def fetch_pagina(url):
    """Busca o HTML da página com tratamento de erro."""
    if not pode_rastrear(url):
        print(f"[ROBOTS] Bloqueado: {url}")
        return None
    try:
        time.sleep(DELAY)
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERRO] {url}: {e}")
        return None

def extrair_links_blog(url_blog):
    """Extrai links de posts recentes da página do blog (limitado a 5)."""
    html = fetch_pagina(url_blog)
    if not html:
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        # filtra links que parecem ser posts (ajuste conforme estrutura do site)
        if '/blog/' in href and href != url_blog and not href.endswith('/blog/'):
            if href.startswith('/'):
                dominio = '/'.join(url_blog.split('/')[:3])
                href = dominio + href
            links.add(href)
    return list(links)[:5]
