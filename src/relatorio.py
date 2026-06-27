"""
relatorio.py — Geração do relatório Markdown e publicação no GitHub
Weedoo Marketing Digital | Medicina Endocanabinoide

Gera schemas JSON-LD PERSONALIZADOS por página — prontos para copiar e colar.
"""

import json
import logging
import os
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger("relatorio")

# ─── Dados fixos do autor e organização ───────────────────────────────────────
AUTOR = {
    "@type": "Person",
    "name": "Carlos Macedo",
    "url": "https://www.weedoo.med.br/sobre/",
    "sameAs": [
        "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/",
        "https://agenciaweedoo.github.io/my-portifolio/",
    ],
}

PUBLISHER = {
    "@type": "Organization",
    "name": "Weedoo",
    "url": "https://www.weedoo.med.br/",
    "logo": {
        "@type": "ImageObject",
        "url": "https://www.weedoo.med.br/wp-content/uploads/logo-weedoo.png",
        "width": 600,
        "height": 60,
    },
}

# ─── Palavras-chave para detectar conteúdo clínico (MedicalWebPage) ───────────
PALAVRAS_CLINICAS = {
    "epilepsia": ("Neurologia", "Epilepsia"),
    "dor crónica": ("Dor e Cuidados Paliativos", "Dor Crônica"),
    "dor crônica": ("Dor e Cuidados Paliativos", "Dor Crônica"),
    "ansiedade": ("Psiquiatria", "Transtorno de Ansiedade"),
    "depressão": ("Psiquiatria", "Depressão"),
    "insônia": ("Medicina do Sono", "Insônia"),
    "cancer": ("Oncologia", "Câncer"),
    "câncer": ("Oncologia", "Câncer"),
    "esclerose": ("Neurologia", "Esclerose Múltipla"),
    "parkinson": ("Neurologia", "Doença de Parkinson"),
    "alzheimer": ("Neurologia", "Doença de Alzheimer"),
    "autismo": ("Neuropediatria", "Transtorno do Espectro Autista"),
    "inflamação": ("Reumatologia", "Inflamação Crônica"),
    "nausea": ("Oncologia", "Náuseas Induzidas por Quimioterapia"),
    "náusea": ("Oncologia", "Náuseas Induzidas por Quimioterapia"),
    "espasticidade": ("Neurologia", "Espasticidade"),
    "fibromialgia": ("Reumatologia", "Fibromialgia"),
}

# ─── FAQs padrão para cannabis medicinal (fallback sem API) ───────────────────
FAQS_PADRAO = [
    (
        "O uso de cannabis medicinal é legal no Brasil?",
        "Sim. A Anvisa regulamenta o uso terapêutico de produtos à base de canabis pela RDC 327/2019. "
        "O paciente precisa de prescrição médica e pode importar ou adquirir produtos de fabricantes "
        "autorizados pela Anvisa, sempre com acompanhamento médico especializado.",
    ),
    (
        "Quais condições de saúde podem ser tratadas com cannabis medicinal?",
        "A evidência científica apoia o uso em epilepsia refratária, dor crônica, espasticidade, "
        "náuseas por quimioterapia, ansiedade e transtornos do sono, entre outras condições. "
        "Toda indicação exige avaliação médica individualizada conforme as diretrizes do CFM.",
    ),
    (
        "O que é o sistema endocanabinoide?",
        "O sistema endocanabinoide (SEC) é uma rede de receptores e moléculas sinalizadoras "
        "presente em todo o organismo, que regula funções como dor, inflamação, sono, humor e imunidade. "
        "Compostos como CBD e THC interagem com este sistema, fundamentando a medicina endocanabinoide.",
    ),
    (
        "CBD e THC são a mesma coisa?",
        "Não. O CBD (canabidiol) é não psicoativo e tem ampla aprovação regulatória para fins medicinais. "
        "O THC (tetrahidrocanabinol) é o principal composto psicoativo da cannabis. "
        "Ambos têm indicações terapêuticas distintas e são prescritos em doses e formulações diferentes.",
    ),
    (
        "Como obter prescrição de cannabis medicinal no Brasil?",
        "Consulte um médico habilitado que avaliará seu quadro clínico e, se indicado, emitirá a prescrição. "
        "Com ela, é possível importar produtos via Anvisa ou adquirir de fabricantes nacionais autorizados. "
        "A Weedoo auxilia clínicas e médicos a comunicar esses tratamentos dentro das normas do CFM.",
    ),
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _sim_nao(cond: bool) -> str:
    return "✅" if cond else "❌"

def _nivel_criticidade(n: int) -> str:
    if n == 0: return "🟢 OK"
    if n <= 2: return "🟡 Atenção"
    return "🔴 Crítico"

def _url_curta(url: str) -> str:
    return url.replace("https://www.weedoo.med.br", "").rstrip("/") or "/"

def _bloco_html(dados: dict, comentario: str = "") -> str:
    """
    Envolve um dict JSON-LD em uma tag <script> HTML pronta para copiar e colar.
    Formato compatível com qualquer CMS (WordPress, Webflow, Wix, etc.).
    """
    json_str = json.dumps(dados, ensure_ascii=False, indent=2)
    linhas = ["```html"]
    if comentario:
        linhas.append(f"<!-- {comentario} -->")
    linhas += [
        '<script type="application/ld+json">',
        json_str,
        "</script>",
        "```",
    ]
    return "\n".join(linhas)


def _detectar_conteudo_clinico(titulo: str, conteudo: str) -> tuple[str, str] | None:
    """
    Detecta se a página tem conteúdo clínico com base em palavras-chave.
    Retorna (especialidade, condicao) ou None se não for clínico.
    """
    texto = (titulo + " " + conteudo).lower()
    for palavra, (especialidade, condicao) in PALAVRAS_CLINICAS.items():
        if palavra in texto:
            return especialidade, condicao
    # Detecção genérica para artigos médicos
    if any(t in texto for t in ["cannabis", "cbd", "canabidiol", "endocanabinoide", "medicinal"]):
        return "Medicina Endocanabinoide", "Saúde e Bem-estar"
    return None


def _heading_para_pergunta(heading: str) -> str:
    """Converte um heading em uma pergunta natural se ainda não for."""
    h = heading.strip()
    if h.endswith("?"):
        return h
    h_lower = h.lower()
    if h_lower.startswith(("o que é", "o que são", "como", "qual", "quais", "quando", "por que", "porque")):
        return h + "?"
    if len(h) < 50:
        return f"O que é {h.lower()}?"
    return f"{h}: como funciona na prática?"


def gerar_faqs_para_artigo(titulo: str, headings: list[str], conteudo: str) -> list[dict]:
    """
    Gera 5 FAQs para um artigo.
    Usa a API Claude se ANTHROPIC_API_KEY estiver disponível; caso contrário, usa heurísticas.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        faqs = _gerar_faqs_com_claude(titulo, headings, conteudo, api_key)
        if faqs:
            return faqs[:5]

    # Fallback heurístico
    faqs: list[dict] = []

    # 1. Derivar perguntas dos headings do artigo
    for h in headings:
        if len(faqs) >= 3:
            break
        pergunta = _heading_para_pergunta(h)
        resposta = (
            f"Este artigo aborda em detalhes {h.lower()}. "
            f"No contexto da medicina endocanabinoide, é fundamental entender este tema "
            f"para tomar decisões informadas, sempre com orientação médica especializada "
            f"e dentro das normas da Anvisa e CFM."
        )
        faqs.append({"pergunta": pergunta, "resposta": resposta})

    # 2. Completar com FAQs padrão até 5
    for pergunta, resposta in FAQS_PADRAO:
        if len(faqs) >= 5:
            break
        if not any(f["pergunta"] == pergunta for f in faqs):
            faqs.append({"pergunta": pergunta, "resposta": resposta})

    return faqs[:5]


def _gerar_faqs_com_claude(titulo: str, headings: list[str], conteudo: str, api_key: str) -> list[dict]:
    """Chama a API do Claude para gerar FAQs contextualizadas para o artigo."""
    import requests as _req

    headings_str = "\n".join(f"- {h}" for h in headings[:6]) if headings else "Não disponível"
    conteudo_str = conteudo[:500] if conteudo else "Não disponível"

    prompt = f"""Você é especialista em medicina endocanabinoide e SEO para saúde no Brasil.
Crie exatamente 5 pares de pergunta-resposta (FAQ Schema) para o artigo: "{titulo}"

Subtítulos do artigo:
{headings_str}

Contexto do conteúdo:
{conteudo_str}

Regras obrigatórias:
- Perguntas devem ser exatamente como usuários pesquisariam no Google
- Respostas: 2-3 frases, científicas mas acessíveis, mencionar Anvisa/CFM quando relevante
- Nunca recomendar uso sem prescrição médica
- Responda APENAS com JSON válido, sem nenhum texto antes ou depois:
[
  {{"pergunta": "...", "resposta": "..."}},
  {{"pergunta": "...", "resposta": "..."}},
  {{"pergunta": "...", "resposta": "..."}},
  {{"pergunta": "...", "resposta": "..."}},
  {{"pergunta": "...", "resposta": "..."}}
]"""

    try:
        resp = _req.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        texto = resp.json()["content"][0]["text"].strip()
        # Remover markdown se houver
        if "```" in texto:
            match = re.search(r"```(?:json)?\s*([\s\S]+?)```", texto)
            texto = match.group(1).strip() if match else texto.split("```")[1].replace("json", "", 1).strip()
        return json.loads(texto)
    except Exception as exc:
        logger.warning("Erro ao gerar FAQs via Claude API: %s. Usando heurísticas.", exc)
        return []


# ─── Seção 1: Sumário Executivo ────────────────────────────────────────────────

def gerar_sumario_executivo(resultados_weedoo: list[dict], comparacao: list[dict]) -> str:
    total_urls = len(resultados_weedoo)
    acessiveis = sum(1 for r in resultados_weedoo if r.get("acessivel"))
    total_erros = sum(len(r.get("todos_erros", [])) for r in resultados_weedoo)
    total_avisos = sum(len(r.get("todos_avisos", [])) for r in resultados_weedoo)
    artigos = sum(1 for r in resultados_weedoo if r.get("tipo_pagina") == "artigo")
    artigos_com_schema = sum(
        1 for r in resultados_weedoo
        if r.get("tipo_pagina") == "artigo"
        and any(t in r.get("tipos_presentes", []) for t in ("Article", "BlogPosting", "NewsArticle"))
    )

    tipos_weedoo: set[str] = set()
    for r in resultados_weedoo:
        tipos_weedoo.update(r.get("tipos_presentes", []))
    tipos_weedoo.discard("Desconhecido")

    tipos_concorrentes: set[str] = set()
    for c in comparacao:
        tipos_concorrentes.update(c.get("tipos_unicos", []))

    lacunas = sorted(tipos_concorrentes - tipos_weedoo - {"Desconhecido"})
    conc_com_eeeat = sum(1 for c in comparacao if c.get("tem_eeeat"))

    if lacunas:
        txt_lacunas = f"A Weedoo **não utiliza** {len(lacunas)} tipo(s) de schema já adotados por concorrentes: `{'`, `'.join(lacunas)}`."
    else:
        txt_lacunas = "A Weedoo cobre **todos os tipos** de schema utilizados pelos concorrentes monitorados."

    return f"""## 📊 Sumário Executivo

Auditoria de **{date.today().strftime('%d/%m/%Y')}** — **{total_urls} páginas** ({acessiveis} acessíveis) e **{len(comparacao)} concorrentes** analisados. Encontrados **{total_erros} erros** e **{total_avisos} avisos**. Dos **{artigos} artigos** do blog, **{artigos_com_schema} possuem** schema de artigo implementado. Em relação à concorrência, **{conc_com_eeeat} de {len(comparacao)} concorrentes** implementam E-E-A-T básico (autor + publisher). {txt_lacunas} Os schemas abaixo já estão **preenchidos com os dados reais de cada página** — basta copiar, colar e publicar.

"""


# ─── Seção 2: Tabela de cobertura ─────────────────────────────────────────────

def gerar_tabela_cobertura(resultados_weedoo: list[dict]) -> str:
    linhas = ["## 🔍 Cobertura de Schemas — Weedoo\n"]
    linhas.append("| Página | Tipo | Schemas Encontrados | Erros | Avisos | Status |")
    linhas.append("|--------|------|---------------------|-------|--------|--------|")

    for r in resultados_weedoo:
        url = _url_curta(r["url"])
        tipo = r.get("tipo_pagina", "—")
        tipos = ", ".join(r.get("tipos_presentes", [])) or "❌ Nenhum"
        erros = len(r.get("todos_erros", []))
        avisos = len(r.get("todos_avisos", []))
        status = "⚫ Inacessível" if not r.get("acessivel") else _nivel_criticidade(erros)
        linhas.append(f"| `{url}` | {tipo} | {tipos} | {erros} | {avisos} | {status} |")

    linhas.append("")

    # Detalhar erros
    linhas.append("### 📋 Erros e Avisos por Página\n")
    problemas = [r for r in resultados_weedoo if r.get("todos_erros") or r.get("todos_avisos")]
    if not problemas:
        linhas.append("🎉 **Nenhum erro encontrado!**\n")
    else:
        for r in problemas:
            url = _url_curta(r["url"])
            linhas.append(f"#### `{url}`\n")
            for e in r.get("todos_erros", []):
                linhas.append(f"- 🔴 **ERRO:** {e}")
            for a in r.get("todos_avisos", []):
                linhas.append(f"- 🟡 **AVISO:** {a}")
            linhas.append("")

    return "\n".join(linhas)


# ─── Seção 3: Tabela comparativa ──────────────────────────────────────────────

def gerar_tabela_comparativa(resultados_weedoo: list[dict], comparacao: list[dict]) -> str:
    linhas = ["## 🥊 Comparativo com Concorrentes\n"]

    tipos_weedoo: set[str] = set()
    for r in resultados_weedoo:
        tipos_weedoo.update(r.get("tipos_presentes", []))
    tipos_weedoo.discard("Desconhecido")

    todos_tipos: set[str] = set(tipos_weedoo)
    for c in comparacao:
        todos_tipos.update(c.get("tipos_unicos", []))
    todos_tipos.discard("Desconhecido")

    nomes = [c["nome"] for c in comparacao]
    sep = " | ".join(["--------"] * len(nomes))

    linhas.append(f"| Schema | Weedoo | {' | '.join(nomes)} |")
    linhas.append(f"|--------|--------|{sep}|")

    for tipo in sorted(todos_tipos):
        w = _sim_nao(tipo in tipos_weedoo)
        cols = [_sim_nao(tipo in c.get("tipos_unicos", [])) for c in comparacao]
        linhas.append(f"| `{tipo}` | {w} | {' | '.join(cols)} |")

    linhas.append("")

    # Concorrentes bloqueados por robots.txt
    bloqueados = [
        c["nome"] for c in comparacao
        if all(p.get("motivo_inacessivel") == "robots_txt" for p in c.get("paginas", []) if p)
    ]
    if bloqueados:
        linhas.append(
            f"> ⚠️ **Concorrentes com robots.txt restritivo** (dados indisponíveis para análise automática): "
            f"{', '.join(bloqueados)}. O agente respeita o robots.txt conforme boas práticas de scraping. "
            f"Recomenda-se verificação manual periódica desses sites.\n"
        )

    # Análise E-E-A-T
    linhas.append("### 🏆 E-E-A-T e Autoridade Médica\n")
    linhas.append(f"| Critério | Weedoo | {' | '.join(nomes)} |")
    linhas.append(f"|----------|--------|{sep}|")

    w_article = _sim_nao(any(t in r.get("tipos_presentes", []) for r in resultados_weedoo for t in ("Article", "BlogPosting")))
    w_breadcrumb = _sim_nao(any("BreadcrumbList" in r.get("tipos_presentes", []) for r in resultados_weedoo))
    w_faq = _sim_nao(any("FAQPage" in r.get("tipos_presentes", []) for r in resultados_weedoo))
    w_medical = _sim_nao(any(t in r.get("tipos_presentes", []) for r in resultados_weedoo for t in ("MedicalWebPage", "Physician")))

    for descricao, weedoo_val, campo in [
        ("Autor estruturado (E-E-A-T)", w_article, "tem_eeeat"),
        ("Publisher estruturado", w_article, "tem_eeeat"),
        ("Schema médico (MedicalWebPage/Physician)", w_medical, "tem_medical_schema"),
        ("Rich snippets (FAQ/HowTo/Video)", w_faq, "tem_rich_snippets"),
        ("BreadcrumbList", w_breadcrumb, None),
    ]:
        cols = [_sim_nao(c.get(campo, False)) if campo else _sim_nao("BreadcrumbList" in c.get("tipos_unicos", [])) for c in comparacao]
        linhas.append(f"| {descricao} | {weedoo_val} | {' | '.join(cols)} |")

    linhas.append("")
    return "\n".join(linhas)


# ─── Seção 4: Recomendações PERSONALIZADAS ────────────────────────────────────

def gerar_recomendacoes(resultados_weedoo: list[dict], comparacao: list[dict]) -> str:
    linhas = ["## 🎯 Top 5 Recomendações — Schemas Prontos por Página"]
    linhas.append("")
    linhas.append(
        "> **Todos os blocos abaixo são HTML prontos para copiar e colar.** "
        "Adicione ao final de cada página no WordPress via **Insert Headers and Footers** "
        "ou pelo campo de código customizado do Rank Math (Schema → Custom Schema)."
    )
    linhas.append("")

    artigos = [r for r in resultados_weedoo if r.get("tipo_pagina") == "artigo" and r.get("acessivel")]
    sem_article = [
        r for r in artigos
        if not any(t in r.get("tipos_presentes", []) for t in ("Article", "BlogPosting", "NewsArticle"))
    ]
    sem_faq = [r for r in artigos if "FAQPage" not in r.get("tipos_presentes", [])]
    sem_breadcrumb = [
        r for r in resultados_weedoo
        if "BreadcrumbList" not in r.get("tipos_presentes", []) and r.get("acessivel")
    ]
    # Artigos com erros de autor (tem Article mas com dados incorretos)
    com_erro_autor = [
        r for r in artigos
        if any(t in r.get("tipos_presentes", []) for t in ("Article", "BlogPosting"))
        and any("author" in e.lower() or "carlos" in e.lower() or "publisher" in e.lower()
                for e in r.get("todos_erros", []))
    ]
    # Para REC1, combinar sem_article + com_erro_autor
    paginas_article_corrigir = sem_article + [r for r in com_erro_autor if r not in sem_article]

    # ── REC 1: Article Schema E-E-A-T ─────────────────────────────────────────
    linhas += [
        "---",
        "### 1️⃣  Article Schema com E-E-A-T — Copiar e Colar por Artigo",
        "",
        "**Prioridade:** 🔴 Crítica | **Impacto:** Campo determinante para ranqueamento de conteúdo YMYL (saúde)",
        "",
    ]

    if not paginas_article_corrigir:
        linhas.append("✅ Todos os artigos já possuem Article schema com dados corretos.\n")
    else:
        linhas.append(f"**{len(paginas_article_corrigir)} artigo(s) precisam de correção:**\n")
        for r in paginas_article_corrigir:
            meta = r.get("metadados", {})
            url = r["url"]
            titulo = meta.get("titulo") or url.split("/")[-2].replace("-", " ").title()
            descricao = meta.get("descricao") or f"Artigo sobre {titulo.lower()} por Carlos Macedo."
            imagem = meta.get("imagem") or "https://www.weedoo.med.br/wp-content/uploads/imagem-artigo.jpg"
            data_pub = meta.get("data_publicacao") or date.today().strftime("%Y-%m-%dT08:00:00-03:00")
            data_mod = meta.get("data_modificacao") or data_pub

            schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": titulo[:110],
                "description": descricao[:160] if descricao else f"Artigo sobre {titulo.lower()}.",
                "image": {
                    "@type": "ImageObject",
                    "url": imagem,
                    "width": 1200,
                    "height": 630,
                },
                "datePublished": data_pub,
                "dateModified": data_mod,
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "author": AUTOR,
                "publisher": PUBLISHER,
                "articleSection": "Cannabis Medicinal",
                "keywords": "cannabis medicinal, CBD, medicina endocanabinoide, Anvisa",
                "inLanguage": "pt-BR",
            }

            linhas.append(f"#### `{_url_curta(url)}`\n")
            linhas.append(_bloco_html(schema, f"Article Schema — {_url_curta(url)}"))
            linhas.append("")

    # ── REC 2: FAQPage por artigo ─────────────────────────────────────────────
    linhas += [
        "---",
        "### 2️⃣  FAQPage — 5 Perguntas Específicas por Artigo",
        "",
        "**Prioridade:** 🔴 Alta | **Impacto:** Rich snippets de FAQ no Google — aumenta CTR em 20–40% e ocupa mais espaço no SERP",
        "",
    ]

    if not sem_faq:
        linhas.append("✅ Todos os artigos já possuem FAQPage.\n")
    else:
        linhas.append(f"**{len(sem_faq)} artigo(s) sem FAQPage:**\n")
        api_disponivel = bool(os.environ.get("ANTHROPIC_API_KEY"))
        if api_disponivel:
            linhas.append("> ✨ *FAQs geradas com IA (Claude API) — contextualizadas para o conteúdo de cada artigo.*\n")
        else:
            linhas.append("> 💡 *Para FAQs ainda mais personalizadas, adicione `ANTHROPIC_API_KEY` como secret no GitHub Actions.*\n")

        for r in sem_faq:
            meta = r.get("metadados", {})
            url = r["url"]
            titulo = meta.get("titulo") or url.split("/")[-2].replace("-", " ").title()
            headings = meta.get("headings", [])
            conteudo = meta.get("conteudo", "")

            faqs = gerar_faqs_para_artigo(titulo, headings, conteudo)

            schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": faq["pergunta"],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": faq["resposta"],
                        },
                    }
                    for faq in faqs
                ],
            }

            linhas.append(f"#### `{_url_curta(url)}`\n")
            linhas.append(_bloco_html(schema, f"FAQPage — {_url_curta(url)}"))
            linhas.append("")

    # ── REC 3: MedicalWebPage para conteúdo clínico ───────────────────────────
    linhas += [
        "---",
        "### 3️⃣  MedicalWebPage — Para Artigos com Conteúdo Clínico",
        "",
        "**Prioridade:** 🟡 Alta | **Impacto:** Schema específico de saúde — reforça E-E-A-T em conteúdo YMYL",
        "",
    ]

    artigos_clinicos = []
    for r in artigos:
        if "MedicalWebPage" in r.get("tipos_presentes", []):
            continue
        meta = r.get("metadados", {})
        titulo = meta.get("titulo", "")
        conteudo = meta.get("conteudo", "")
        deteccao = _detectar_conteudo_clinico(titulo, conteudo)
        if deteccao:
            artigos_clinicos.append((r, deteccao))

    if not artigos_clinicos:
        linhas.append("✅ Nenhum artigo clínico identificado sem MedicalWebPage, ou todos já o possuem.\n")
    else:
        linhas.append(f"**{len(artigos_clinicos)} artigo(s) clínico(s) identificados:**\n")
        for r, (especialidade, condicao) in artigos_clinicos:
            meta = r.get("metadados", {})
            url = r["url"]
            titulo = meta.get("titulo") or url.split("/")[-2].replace("-", " ").title()
            descricao = meta.get("descricao") or f"Artigo clínico sobre {condicao.lower()}."
            data_mod = meta.get("data_modificacao") or date.today().strftime("%Y-%m-%d")

            schema = {
                "@context": "https://schema.org",
                "@type": "MedicalWebPage",
                "name": titulo,
                "url": url,
                "description": descricao[:200] if descricao else f"Conteúdo clínico sobre {condicao.lower()}.",
                "inLanguage": "pt-BR",
                "lastReviewed": data_mod[:10] if data_mod else date.today().isoformat(),
                "reviewedBy": AUTOR,
                "specialty": {
                    "@type": "MedicalSpecialty",
                    "name": especialidade,
                },
                "about": {
                    "@type": "MedicalCondition",
                    "name": condicao,
                },
                "publisher": PUBLISHER,
            }

            linhas.append(f"#### `{_url_curta(url)}` — {especialidade}\n")
            linhas.append(_bloco_html(schema, f"MedicalWebPage — {_url_curta(url)}"))
            linhas.append("")

    # ── REC 4: BreadcrumbList por página ──────────────────────────────────────
    linhas += [
        "---",
        "### 4️⃣  BreadcrumbList — Schema por Página",
        "",
        "**Prioridade:** 🟡 Média | **Impacto:** Exibe o caminho de navegação no SERP, melhora CTR",
        "",
    ]

    if not sem_breadcrumb:
        linhas.append("✅ Todas as páginas já possuem BreadcrumbList.\n")
    else:
        linhas.append(f"**{len(sem_breadcrumb)} página(s) sem BreadcrumbList:**\n")
        for r in sem_breadcrumb:
            url = r["url"]
            meta = r.get("metadados", {})
            titulo_pg = meta.get("titulo") or url.split("/")[-2].replace("-", " ").title()
            tipo_pg = r.get("tipo_pagina", "pagina_generica")

            # Construir items do breadcrumb conforme tipo de página
            items = [{"@type": "ListItem", "position": 1, "name": "Início", "item": "https://www.weedoo.med.br/"}]

            if tipo_pg == "artigo":
                items.append({"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://www.weedoo.med.br/blog/"})
                items.append({"@type": "ListItem", "position": 3, "name": titulo_pg, "item": url})
            elif tipo_pg == "blog_listagem":
                items.append({"@type": "ListItem", "position": 2, "name": "Blog", "item": url})
            elif tipo_pg == "servicos":
                items.append({"@type": "ListItem", "position": 2, "name": "Nossos Serviços", "item": url})
            elif tipo_pg == "sobre":
                items.append({"@type": "ListItem", "position": 2, "name": "Sobre", "item": url})
            else:
                items.append({"@type": "ListItem", "position": 2, "name": titulo_pg, "item": url})

            schema = {
                "@context": "https://schema.org",
                "@type": "BreadcrumbList",
                "itemListElement": items,
            }

            linhas.append(f"#### `{_url_curta(url)}`\n")
            linhas.append(_bloco_html(schema, f"BreadcrumbList — {_url_curta(url)}"))
            linhas.append("")

    # ── REC 5: WebSite + Organization na Home ─────────────────────────────────
    home_result = next((r for r in resultados_weedoo if r.get("tipo_pagina") == "home"), None)
    home_tem_website = home_result and "WebSite" in home_result.get("tipos_presentes", [])
    home_tem_org = home_result and "Organization" in home_result.get("tipos_presentes", [])

    linhas += [
        "---",
        "### 5️⃣  WebSite + Organization na Página Inicial",
        "",
        "**Prioridade:** 🟡 Média | **Impacto:** Habilita Sitelinks Search Box e Knowledge Panel da Weedoo no Google",
        "",
    ]

    if home_tem_website and home_tem_org:
        linhas.append("✅ Página inicial já possui WebSite e Organization configurados.\n")
    else:
        schema_home = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": "https://www.weedoo.med.br/#website",
                    "name": "Weedoo — Marketing Digital para Medicina Endocanabinoide",
                    "url": "https://www.weedoo.med.br/",
                    "description": (
                        "A primeira agência de marketing digital especializada em medicina "
                        "endocanabinoide no Brasil. Unindo ciência comprovada e engenharia de marketing."
                    ),
                    "inLanguage": "pt-BR",
                    "publisher": {"@id": "https://www.weedoo.med.br/#organization"},
                    "potentialAction": {
                        "@type": "SearchAction",
                        "target": {
                            "@type": "EntryPoint",
                            "urlTemplate": "https://www.weedoo.med.br/?s={search_term_string}",
                        },
                        "query-input": "required name=search_term_string",
                    },
                },
                {
                    "@type": "Organization",
                    "@id": "https://www.weedoo.med.br/#organization",
                    "name": "Weedoo",
                    "url": "https://www.weedoo.med.br/",
                    "description": (
                        "Agência de marketing digital especializada em medicina endocanabinoide, "
                        "compliance Anvisa/CFM e estratégias E-E-A-T para clínicas e médicos."
                    ),
                    "logo": PUBLISHER["logo"],
                    "sameAs": ["https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"],
                    "foundingDate": "2023",
                    "areaServed": "BR",
                    "knowsAbout": [
                        "Marketing Digital", "Medicina Endocanabinoide",
                        "Cannabis Medicinal", "SEO para Saúde", "E-E-A-T", "Compliance Anvisa",
                    ],
                },
            ],
        }
        linhas.append("#### `/` — Página Inicial\n")
        linhas.append(_bloco_html(schema_home, "WebSite + Organization — Página Inicial"))
        linhas.append("")

    return "\n".join(linhas)


# ─── Seção 5: Instruções de correção como blocos HTML ─────────────────────────

def gerar_instrucoes_correcao(resultados_weedoo: list[dict]) -> str:
    linhas = ["## 🔧 Como Adicionar os Schemas no WordPress\n"]

    linhas += [
        "### Método 1 — Plugin Insert Headers and Footers (recomendado para todos)",
        "1. Instale: **Plugins → Adicionar Novo → buscar 'Insert Headers and Footers'**",
        "2. Acesse: **Configurações → Insert Headers and Footers**",
        "3. Cole o bloco HTML na seção **Scripts in Footer**",
        "4. Para schemas específicos por página: use o plugin **WPCode** (versão gratuita) com regras de exibição por URL",
        "",
        "### Método 2 — Rank Math SEO (recomendado para artigos)",
        "1. Instale o **Rank Math SEO** (gratuito)",
        "2. Edite o artigo → painel lateral **Schema** → **Custom Schema**",
        "3. Cole apenas o conteúdo interno do JSON (sem a tag `<script>`)",
        "",
        "### Validação após adicionar",
        "- [Rich Results Test (Google)](https://search.google.com/test/rich-results) ← **obrigatório antes de publicar**",
        "- [Schema Markup Validator](https://validator.schema.org/)",
        "",
        "---",
        "### Checklist de Correção por Página\n",
    ]

    paginas_com_erros = [r for r in resultados_weedoo if r.get("todos_erros") and r.get("acessivel")]
    if not paginas_com_erros:
        linhas.append("✅ **Nenhum erro crítico restante!** Continue monitorando semanalmente.\n")
        return "\n".join(linhas)

    for r in paginas_com_erros:
        url = _url_curta(r["url"])
        erros = r.get("todos_erros", [])
        meta = r.get("metadados", {})
        titulo = meta.get("titulo", url)

        linhas.append(f"#### `{url}` — {_nivel_criticidade(len(erros))}\n")
        linhas.append(f"**{len(erros)} erro(s) a corrigir:**\n")

        for i, erro in enumerate(erros, 1):
            linhas.append(f"{i}. {erro}")
        linhas.append("")

        # Gerar bloco HTML de correção focado nos erros
        erros_autor = [e for e in erros if "author" in e.lower() or "carlos" in e.lower() or "sameas" in e.lower()]
        erros_publisher = [e for e in erros if "publisher" in e.lower()]

        if erros_autor or erros_publisher:
            linhas.append("**Bloco HTML de correção — adicione ao final desta página:**\n")
            tipo_pg = r.get("tipo_pagina", "artigo")
            data_pub = meta.get("data_publicacao") or date.today().strftime("%Y-%m-%dT08:00:00-03:00")
            schema_correcao = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": (meta.get("titulo") or titulo)[:110],
                "mainEntityOfPage": {"@type": "WebPage", "@id": r["url"]},
                "datePublished": data_pub,
                "dateModified": meta.get("data_modificacao") or data_pub,
                "author": AUTOR,
                "publisher": PUBLISHER,
            }
            if meta.get("imagem"):
                schema_correcao["image"] = {"@type": "ImageObject", "url": meta["imagem"]}

            linhas.append(_bloco_html(schema_correcao, f"Correção E-E-A-T — {url}"))
            linhas.append("")

    return "\n".join(linhas)


# ─── Montagem do relatório completo ───────────────────────────────────────────

def gerar_relatorio(resultados_weedoo: list[dict], comparacao: list[dict]) -> str:
    hoje_fmt = date.today().strftime("%d/%m/%Y")

    cabecalho = f"""# 📋 Relatório de Schema Markup — Weedoo
> **Data:** {hoje_fmt} &nbsp;|&nbsp; **Gerado por:** WeedooSEOMonitorBot &nbsp;|&nbsp; **Nicho:** Medicina Endocanabinoide
>
> ⚡ **Os schemas das seções 1–5 já estão preenchidos com os dados reais de cada página.**

---

"""

    rodape = f"""
---

## 🔗 Links Úteis

| Ferramenta | Link |
|------------|------|
| Rich Results Test | https://search.google.com/test/rich-results |
| Schema Markup Validator | https://validator.schema.org/ |
| Google Search Console | https://search.google.com/search-console |
| Schema.org MedicalWebPage | https://schema.org/MedicalWebPage |
| Guia E-E-A-T Google | https://developers.google.com/search/docs/fundamentals/creating-helpful-content |

---
*Relatório gerado em {hoje_fmt} pelo WeedooSEOMonitorBot — contato@weedoo.med.br*
"""

    return "\n".join([
        cabecalho,
        gerar_sumario_executivo(resultados_weedoo, comparacao),
        gerar_tabela_cobertura(resultados_weedoo),
        gerar_tabela_comparativa(resultados_weedoo, comparacao),
        gerar_recomendacoes(resultados_weedoo, comparacao),
        gerar_instrucoes_correcao(resultados_weedoo),
        rodape,
    ])


# ─── Salvar e publicar ────────────────────────────────────────────────────────

def salvar_relatorio(relatorio_md: str, reports_dir: Path) -> Path:
    nome = f"{date.today().isoformat()}-schema-report.md"
    caminho = reports_dir / nome
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(relatorio_md)
    logger.info("✅ Relatório salvo: %s", caminho)
    return caminho


def publicar_issue_github(relatorio_md: str) -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo_name:
        logger.warning("GITHUB_TOKEN ou GITHUB_REPOSITORY não encontrados.")
        return

    try:
        from github import Github, GithubException  # type: ignore[import]
        gh = Github(token)
        repo = gh.get_repo(repo_name)

        label_name = "schema-report"
        try:
            repo.get_label(label_name)
        except GithubException:
            try:
                repo.create_label(name=label_name, color="0075ca",
                                  description="Relatório automático de Schema Markup — WeedooSEOBot")
            except GithubException:
                pass

        titulo = f"📊 Schema Markup Report — {date.today().strftime('%d/%m/%Y')}"
        corpo = relatorio_md[:64_800] + "\n\n> *[truncado — ver arquivo completo em /reports/]*" if len(relatorio_md) > 64_800 else relatorio_md
        issue = repo.create_issue(title=titulo, body=corpo, labels=[label_name])
        logger.info("✅ Issue criada: %s", issue.html_url)
    except ImportError:
        logger.error("PyGithub não instalado.")
    except Exception as exc:
        logger.error("Erro ao criar Issue: %s", exc)
