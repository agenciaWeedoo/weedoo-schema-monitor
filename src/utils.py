import time
import random
import requests

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
]

DELAY = 3  # segundos entre requisições

def nova_sessao():
    s = requests.Session()
    s.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    return s

def pode_rastrear(url):
    try:
        dominio = '/'.join(url.split('/')[:3])
        if 'weedoo.med.br' in dominio:
            return True  # você é o dono, ignore robots.txt
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.set_url(f"{dominio}/robots.txt")
        rp.read()
        return rp.can_fetch(random.choice(USER_AGENTS), url)
    except:
        return True

def fetch_pagina(url):
    if not pode_rastrear(url):
        print(f"[ROBOTS] Bloqueado: {url}")
        return None
    try:
        time.sleep(DELAY + random.uniform(0.5, 2.0))
        sess = nova_sessao()
        resp = sess.get(url, timeout=25)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.HTTPError as e:
        print(f"[HTTP] {url}: {e}")
    except Exception as e:
        print(f"[ERRO] {url}: {e}")
    return None

def extrair_links_blog(url_blog):
    html = fetch_pagina(url_blog)
    if not html:
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/blog/' in href and href != url_blog and not href.endswith('/blog/'):
            if href.startswith('/'):
                dominio = '/'.join(url_blog.split('/')[:3])
                href = dominio + href
            links.add(href)
    return list(links)[:5]
