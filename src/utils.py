import time
import random
import requests

# Pool de User-Agents reais de navegadores para evitar bloqueio 403
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
]

DELAY = 2  # segundos entre requisições

def get_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def pode_rastrear(url):
    """Verifica robots.txt antes de raspar."""
    try:
        dominio = '/'.join(url.split('/')[:3])
        # Para o próprio site da Weedoo, ignorar robots.txt (você é o dono)
        if 'weedoo.med.br' in dominio:
            return True
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.set_url(f"{dominio}/robots.txt")
        rp.read()
        return rp.can_fetch(get_headers()['User-Agent'], url)
    except:
        return True  # se falhar, assume que pode

def fetch_pagina(url):
    """Busca o HTML da página com tratamento de erro e headers de navegador."""
    if not pode_rastrear(url):
        print(f"[ROBOTS] Bloqueado: {url}")
        return None
    try:
        time.sleep(DELAY + random.uniform(0.5, 1.5))  # delay com variação humana
        resp = requests.get(url, headers=get_headers(), timeout=20)
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
