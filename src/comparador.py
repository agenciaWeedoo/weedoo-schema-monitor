AUTHOR_OBRIGATORIO = {
    "@type": "Person",
    "name": "Carlos Macedo",
    "url": "https://www.weedoo.med.br/sobre/",
    "sameAs": [
        "https://agenciaweedoo.github.io/my-portifolio/",
        "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"
    ]
}

TIPOS_ALVO = [
    "Article", "WebSite", "Organization", "Person", "BreadcrumbList",
    "FAQ", "HowTo", "MedicalWebPage", "Physician", "VideoObject", "Review"
]

def achar_tipos(schemas_dict):
    tipos = set()
    if not schemas_dict:
        return tipos
    for formato, dados in schemas_dict.items():
        for item in dados:
            t = item.get('@type') or item.get('type')
            if t:
                tipos.add(t)
    return tipos

def validar_artigo_weedoo(schemas_dict):
    erros = []
    artigos = []
    for item in schemas_dict.get('jsonld', []):
        if item.get('@type') == 'Article':
            artigos.append(item)
    for art in artigos:
        author = art.get('author', {})
        if not author or author.get('name') != AUTHOR_OBRIGATORIO['name']:
            erros.append(f"Artigo sem autor Carlos Macedo: {art.get('headline', 'sem título')}")
    return erros

def comparar_schemas(dados_weedoo, dados_concorrentes):
    # Tipos usados pela Weedoo
    tipos_weedoo = set()
    for url, schemas in dados_weedoo.items():
        tipos_weedoo.update(achar_tipos(schemas))

    # Tipos usados por cada concorrente
    concorrentes_tipos = {}
    for nome, dados in dados_concorrentes.items():
        conc_tipos = set()
        for chave, schemas in dados.items():
            if chave == 'posts':
                for post_url, post_schemas in dados['posts'].items():
                    conc_tipos.update(achar_tipos(post_schemas))
            else:
                conc_tipos.update(achar_tipos(schemas))
        concorrentes_tipos[nome] = conc_tipos

    # Verificar erros na Weedoo
    erros = []
    for url, schemas in dados_weedoo.items():
        erros.extend(validar_artigo_weedoo(schemas))

    # Gerar recomendações
    recomendacoes = []
    for tipo in TIPOS_ALVO:
        if tipo not in tipos_weedoo:
            quem_usa = [nome for nome, t in concorrentes_tipos.items() if tipo in t]
            if quem_usa:
                recomendacoes.append({
                    'acao': f'Adicionar Schema "{tipo}"',
                    'concorrentes': quem_usa,
                    'impacto': 'Alto' if tipo in ['FAQ', 'HowTo', 'MedicalWebPage'] else 'Médio'
                })

    # Priorizar recomendações por impacto
    prioridade = {'Alto': 0, 'Médio': 1}
    recomendacoes.sort(key=lambda x: prioridade.get(x['impacto'], 2))

    return {
        'data': __import__('datetime').datetime.now().strftime('%d/%m/%Y'),
        'tipos_weedoo': sorted(tipos_weedoo),
        'tipos_concorrentes': {k: sorted(v) for k, v in concorrentes_tipos.items()},
        'erros': erros,
        'recomendacoes': recomendacoes[:5]
    }
