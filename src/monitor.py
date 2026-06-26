import os
import json
from datetime import datetime
from extruct import extract as extrair_dados_estruturados
from utils import fetch_pagina, extrair_links_blog
from comparador import comparar_schemas
from relatorio import gerar_relatorio

with open('config/urls_weedoo.txt') as f:
    urls_weedoo = [linha.strip() for linha in f if linha.strip()]

links_blog = extrair_links_blog('https://www.weedoo.med.br/blog/')
urls_weedoo.extend(links_blog[:5])

with open('config/concorrentes.json') as f:
    concorrentes = json.load(f)

def extrair_schemas(url):
    html = fetch_pagina(url)
    if not html:
        return None
    try:
        schemas = extrair_dados_estruturados(html, url)
        schemas['jsonld'] = schemas.pop('json-ld', [])
        return schemas
    except Exception as e:
        print(f"[AVISO] Falha ao extrair schemas de {url}: {e}")
        return None

# Weedoo
dados_weedoo = {}
for url in urls_weedoo:
    print(f"[WEEDOO] Processando: {url}")
    dados_weedoo[url] = extrair_schemas(url)

# Concorrentes
dados_concorrentes = {}
for conc in concorrentes:
    print(f"[CONCORRENTE] {conc['nome']}")
    home_schemas = extrair_schemas(conc['home'])
    blog_schemas = extrair_schemas(conc['blog'])
    posts = extrair_links_blog(conc['blog'])[:3]
    posts_schemas = {}
    for p in posts:
        posts_schemas[p] = extrair_schemas(p)
    dados_concorrentes[conc['nome']] = {
        'home': home_schemas,
        'blog': blog_schemas,
        'posts': posts_schemas
    }

# Relatório
relatorio = comparar_schemas(dados_weedoo, dados_concorrentes)
relatorio_path = gerar_relatorio(relatorio)

# Issue
github_token = os.environ.get('GITHUB_TOKEN')
if github_token:
    from github import Github
    g = Github(github_token)
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    with open(relatorio_path, 'r') as f:
        conteudo = f.read()
    titulo = f"📊 Relatório Schema Markup - {datetime.now().strftime('%d/%m/%Y')}"
    repo.create_issue(title=titulo, body=conteudo, labels=['schema-report'])
    print(f"[OK] Issue criada: {titulo}")
else:
    print("[AVISO] GITHUB_TOKEN não encontrado. Issue não criada.")
