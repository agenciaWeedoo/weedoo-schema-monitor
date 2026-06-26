"""
relatorio.py — Geração do relatório Markdown e publicação no GitHub
Weedoo Marketing Digital | Medicina Endocanabinoide

Estrutura do relatório:
  1. Cabeçalho com data e metadados
  2. Sumário executivo (1 parágrafo)
  3. Tabela de cobertura de schemas da Weedoo
  4. Tabela comparativa com concorrentes
  5. Top 5 recomendações priorizadas (com JSON-LD prontos)
  6. Instruções de correção para erros encontrados
  7. Rodapé com links úteis
"""

import logging
import os
from datetime import date
from pathlib import Path

logger = logging.getLogger("relatorio")


# ─── Helpers visuais ──────────────────────────────────────────────────────────

def _sim_nao(condicao: bool) -> str:
    """Retorna ✅ ou ❌ baseado na condição (para tabelas Markdown)."""
    return "✅" if condicao else "❌"


def _nivel_criticidade(qtd_erros: int) -> str:
    """Classifica severidade com base no número de erros."""
    if qtd_erros == 0:
        return "🟢 OK"
    if qtd_erros <= 2:
        return "🟡 Atenção"
    return "🔴 Crítico"


def _url_curta(url: str) -> str:
    """Remove o domínio base para exibição compacta nas tabelas."""
    curta = url.replace("https://www.weedoo.med.br", "").rstrip("/")
    return curta or "/"


# ─── Seção 1: Sumário Executivo ────────────────────────────────────────────────

def gerar_sumario_executivo(
    resultados_weedoo: list[dict],
    comparacao: list[dict],
) -> str:
    """Gera um parágrafo de sumário executivo orientado a dados."""
    total_urls = len(resultados_weedoo)
    total_erros = sum(len(r.get("todos_erros", [])) for r in resultados_weedoo)
    total_avisos = sum(len(r.get("todos_avisos", [])) for r in resultados_weedoo)
    paginas_acessiveis = sum(1 for r in resultados_weedoo if r.get("acessivel"))
    paginas_com_article = sum(
        1 for r in resultados_weedoo
        if any(t in r.get("tipos_presentes", []) for t in ("Article", "BlogPosting", "NewsArticle"))
    )

    # Tipos únicos da Weedoo
    tipos_weedoo: set[str] = set()
    for r in resultados_weedoo:
        tipos_weedoo.update(r.get("tipos_presentes", []))
    tipos_weedoo.discard("Desconhecido")

    # Tipos únicos dos concorrentes
    tipos_concorrentes: set[str] = set()
    for c in comparacao:
        tipos_concorrentes.update(c.get("tipos_unicos", []))

    lacunas = sorted(tipos_concorrentes - tipos_weedoo - {"Desconhecido"})
    conc_com_eeeat = sum(1 for c in comparacao if c.get("tem_eeeat"))

    if lacunas:
        texto_lacunas = f"A Weedoo **não utiliza** {len(lacunas)} tipo(s) de schema já adotados por concorrentes: `{'`, `'.join(lacunas)}`."
    else:
        texto_lacunas = "A Weedoo **cobre todos os tipos de schema** utilizados pelos concorrentes monitorados — excelente cobertura!"

    return f"""## 📊 Sumário Executivo

Auditoria realizada em **{date.today().strftime('%d/%m/%Y')}** cobrindo **{total_urls} páginas** da Weedoo ({paginas_acessiveis} acessíveis) e **{len(comparacao)} concorrentes** no nicho de Medicina Endocanabinoide no Brasil. Foram identificados **{total_erros} erros** e **{total_avisos} avisos** nos dados estruturados da Weedoo. Do total de páginas analisadas, **{paginas_com_article} possuem** schema de artigo (`Article`/`BlogPosting`) implementado — campo crítico para E-E-A-T em conteúdo YMYL (saúde). Em relação à concorrência, **{conc_com_eeeat} de {len(comparacao)} concorrentes** já implementam campos básicos de E-E-A-T (autor + publisher estruturados). {texto_lacunas} As recomendações a seguir estão priorizadas pelo impacto esperado em rich snippets e autoridade de busca.

"""


# ─── Seção 2: Tabela de cobertura da Weedoo ────────────────────────────────────

def gerar_tabela_cobertura(resultados_weedoo: list[dict]) -> str:
    """Gera tabela de cobertura de schemas da Weedoo com detalhamento de erros."""
    linhas = ["## 🔍 Cobertura de Schemas — Weedoo\n"]
    linhas.append("| Página | Tipo | Schemas Encontrados | Erros | Avisos | Status |")
    linhas.append("|--------|------|---------------------|-------|--------|--------|")

    for r in resultados_weedoo:
        url = _url_curta(r["url"])
        tipo_pg = r.get("tipo_pagina", "—")
        tipos = ", ".join(r.get("tipos_presentes", [])) if r.get("tipos_presentes") else "❌ Nenhum"
        erros = len(r.get("todos_erros", []))
        avisos = len(r.get("todos_avisos", []))
        status = _nivel_criticidade(erros)
        if not r.get("acessivel"):
            status = "⚫ Inacessível"
        linhas.append(f"| `{url}` | {tipo_pg} | {tipos} | {erros} | {avisos} | {status} |")

    linhas.append("")

    # Detalhamento de erros por página
    linhas.append("### 📋 Detalhamento de Erros e Avisos por Página\n")
    paginas_com_problemas = [
        r for r in resultados_weedoo
        if r.get("todos_erros") or r.get("todos_avisos")
    ]

    if not paginas_com_problemas:
        linhas.append("🎉 **Nenhum erro ou aviso encontrado!** Excelente cobertura de schemas.\n")
    else:
        for r in paginas_com_problemas:
            url = _url_curta(r["url"])
            linhas.append(f"#### `{url}`\n")
            for e in r.get("todos_erros", []):
                linhas.append(f"- 🔴 **ERRO:** {e}")
            for a in r.get("todos_avisos", []):
                linhas.append(f"- 🟡 **AVISO:** {a}")
            linhas.append("")

    return "\n".join(linhas)


# ─── Seção 3: Tabela comparativa ──────────────────────────────────────────────

def gerar_tabela_comparativa(
    resultados_weedoo: list[dict],
    comparacao: list[dict],
) -> str:
    """Gera tabela comparativa de schemas entre a Weedoo e todos os concorrentes."""
    linhas = ["## 🥊 Comparativo com Concorrentes\n"]

    # Coletar todos os tipos únicos (Weedoo + todos concorrentes)
    tipos_weedoo: set[str] = set()
    for r in resultados_weedoo:
        tipos_weedoo.update(r.get("tipos_presentes", []))
    tipos_weedoo.discard("Desconhecido")

    todos_tipos: set[str] = set(tipos_weedoo)
    for c in comparacao:
        todos_tipos.update(c.get("tipos_unicos", []))
    todos_tipos.discard("Desconhecido")
    todos_tipos_sorted = sorted(todos_tipos)

    nomes_conc = [c["nome"] for c in comparacao]

    # Tabela principal de cobertura por tipo de schema
    separador_col = " | ".join(["--------"] * len(nomes_conc))
    linhas.append(
        f"| Schema | Weedoo | {' | '.join(nomes_conc)} |"
    )
    linhas.append(
        f"|--------|--------|{separador_col}|"
    )

    for tipo in todos_tipos_sorted:
        weedoo_tem = _sim_nao(tipo in tipos_weedoo)
        cols_conc = [_sim_nao(tipo in c.get("tipos_unicos", [])) for c in comparacao]
        linhas.append(
            f"| `{tipo}` | {weedoo_tem} | {' | '.join(cols_conc)} |"
        )

    linhas.append("")

    # Tabela de critérios E-E-A-T e autoridade médica
    linhas.append("### 🏆 Análise de E-E-A-T e Autoridade Médica\n")
    linhas.append(
        f"| Critério | Weedoo | {' | '.join(nomes_conc)} |"
    )
    linhas.append(
        f"|----------|--------|{separador_col}|"
    )

    weedoo_tem_article = any(
        t in r.get("tipos_presentes", [])
        for r in resultados_weedoo
        for t in ("Article", "BlogPosting", "NewsArticle")
    )
    weedoo_tem_breadcrumb = any("BreadcrumbList" in r.get("tipos_presentes", []) for r in resultados_weedoo)
    weedoo_tem_faq = any("FAQPage" in r.get("tipos_presentes", []) for r in resultados_weedoo)
    weedoo_tem_medical = any(
        t in r.get("tipos_presentes", [])
        for r in resultados_weedoo
        for t in ("MedicalWebPage", "Physician")
    )

    criterios = [
        ("Autor estruturado (E-E-A-T)", weedoo_tem_article, "tem_eeeat"),
        ("Publisher estruturado (E-E-A-T)", weedoo_tem_article, "tem_eeeat"),
        ("Schema médico (MedicalWebPage/Physician)", weedoo_tem_medical, "tem_medical_schema"),
        ("Rich snippets (FAQ/HowTo/Video)", weedoo_tem_faq, "tem_rich_snippets"),
        ("BreadcrumbList", weedoo_tem_breadcrumb, None),
    ]

    for descricao, weedoo_val, campo_conc in criterios:
        weedoo_sim = _sim_nao(weedoo_val)
        if campo_conc:
            cols = [_sim_nao(c.get(campo_conc, False)) for c in comparacao]
        else:
            cols = [_sim_nao("BreadcrumbList" in c.get("tipos_unicos", [])) for c in comparacao]
        linhas.append(f"| {descricao} | {weedoo_sim} | {' | '.join(cols)} |")

    linhas.append("")

    # Sumário de tipos exclusivos dos concorrentes (lacunas da Weedoo)
    lacunas = sorted(
        t for t in todos_tipos
        if t not in tipos_weedoo and t != "Desconhecido"
    )
    if lacunas:
        linhas.append("### ⚠️ Tipos de Schema Usados por Concorrentes mas Ausentes na Weedoo\n")
        for t in lacunas:
            concorrentes_com_tipo = [c["nome"] for c in comparacao if t in c.get("tipos_unicos", [])]
            linhas.append(f"- `{t}` — usado por: {', '.join(concorrentes_com_tipo)}")
        linhas.append("")

    return "\n".join(linhas)


# ─── Seção 4: Recomendações ────────────────────────────────────────────────────

def gerar_recomendacoes(
    resultados_weedoo: list[dict],
    comparacao: list[dict],
) -> str:
    """Gera as top 5 recomendações priorizadas com exemplos de JSON-LD prontos."""
    linhas = ["## 🎯 Top 5 Recomendações Priorizadas\n"]
    linhas.append("> Cada recomendação inclui o **impacto esperado** e um **JSON-LD pronto para copiar e colar**.\n")

    # ── REC 1: Article com E-E-A-T completo ────────────────────────────────────
    linhas += [
        "---",
        "### 1️⃣  Implementar/Corrigir Article Schema com E-E-A-T Completo em Todos os Artigos",
        "",
        "**Prioridade:** 🔴 Crítica | **Impacto:** Autoridade E-E-A-T, elegibilidade para rich snippets de artigo",
        "",
        "O Google usa os campos `author`, `publisher` e datas para avaliar Expertise, "
        "Authoritativeness e Trustworthiness (E-E-A-T). Para conteúdo YMYL como medicina, "
        "isso é **determinante** para ranqueamento. Todo artigo deve ter o schema abaixo:",
        "",
        "```json",
        """{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Título Exato do Artigo (máx. 110 caracteres)",
  "description": "Resumo do artigo em até 160 caracteres para SEO.",
  "image": {
    "@type": "ImageObject",
    "url": "https://www.weedoo.med.br/wp-content/uploads/imagem-destaque.jpg",
    "width": 1200,
    "height": 630
  },
  "datePublished": "2025-01-01T08:00:00-03:00",
  "dateModified": "2025-01-15T10:00:00-03:00",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://www.weedoo.med.br/blog/slug-do-artigo/"
  },
  "author": {
    "@type": "Person",
    "name": "Carlos Macedo",
    "url": "https://www.weedoo.med.br/sobre/",
    "sameAs": [
      "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/",
      "https://agenciaweedoo.github.io/my-portifolio/"
    ]
  },
  "publisher": {
    "@type": "Organization",
    "name": "Weedoo",
    "url": "https://www.weedoo.med.br/",
    "logo": {
      "@type": "ImageObject",
      "url": "https://www.weedoo.med.br/wp-content/uploads/logo-weedoo.png",
      "width": 600,
      "height": 60
    }
  },
  "articleSection": "Cannabis Medicinal",
  "keywords": "cannabis medicinal, CBD, medicina endocanabinoide, Anvisa"
}""",
        "```",
        "",
    ]

    # ── REC 2: FAQPage ─────────────────────────────────────────────────────────
    linhas += [
        "---",
        "### 2️⃣  Adicionar FAQPage para Capturar Rich Snippets de Perguntas Frequentes",
        "",
        "**Prioridade:** 🔴 Alta | **Impacto:** Rich snippets de FAQ no Google (aumenta CTR em 20–40%), "
        "ocupa mais espaço no SERP e responde dúvidas do usuário sem clicar",
        "",
        "Adicione ao final de artigos informativos uma seção de FAQ com este schema:",
        "",
        "```json",
        """{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "O uso de cannabis medicinal é legal no Brasil?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sim. A Anvisa regulamenta o uso de produtos à base de canabis para fins medicinais pela RDC 327/2019. O paciente precisa de prescrição médica e pode importar ou adquirir produtos registrados pela Anvisa. A Weedoo orienta médicos e clínicas a comunicar esses tratamentos dentro das normas do CFM e Anvisa."
      }
    },
    {
      "@type": "Question",
      "name": "O que é o sistema endocanabinoide?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "O sistema endocanabinoide (SEC) é uma rede de receptores e moléculas sinalizadoras presente em todo o organismo humano, responsável por regular funções como dor, inflamação, sono, humor e imunidade. Compostos como CBD e THC interagem com este sistema, o que fundamenta a medicina endocanabinoide."
      }
    },
    {
      "@type": "Question",
      "name": "Quais condições podem ser tratadas com cannabis medicinal?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A literatura científica apoia o uso em epilepsia refratária, dor crônica, espasticidade na esclerose múltipla, náuseas e vômitos por quimioterapia, ansiedade e transtornos do sono. No Brasil, qualquer indicação exige avaliação médica individualizada conforme as diretrizes do CFM."
      }
    }
  ]
}""",
        "```",
        "",
    ]

    # ── REC 3: MedicalWebPage ─────────────────────────────────────────────────
    linhas += [
        "---",
        "### 3️⃣  Implementar MedicalWebPage em Artigos com Conteúdo Clínico",
        "",
        "**Prioridade:** 🟡 Alta | **Impacto:** Schema especializado para saúde — "
        "reforça E-E-A-T em YMYL, aumenta relevância para buscas médicas",
        "",
        "```json",
        """{
  "@context": "https://schema.org",
  "@type": "MedicalWebPage",
  "name": "Cannabis Medicinal para Epilepsia Refratária: Evidências e Protocolo",
  "url": "https://www.weedoo.med.br/blog/cannabis-medicinal-epilepsia/",
  "description": "Guia baseado em evidências científicas sobre o uso de canabidiol (CBD) no tratamento de epilepsia refratária, conforme protocolos Anvisa/CFM.",
  "inLanguage": "pt-BR",
  "lastReviewed": "2025-01-01",
  "reviewedBy": {
    "@type": "Person",
    "name": "Carlos Macedo",
    "url": "https://www.weedoo.med.br/sobre/",
    "sameAs": [
      "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"
    ]
  },
  "specialty": {
    "@type": "MedicalSpecialty",
    "name": "Neurologia"
  },
  "about": {
    "@type": "MedicalCondition",
    "name": "Epilepsia Refratária",
    "alternateName": "Epilepsia Farmacorresistente"
  },
  "mentions": {
    "@type": "Drug",
    "name": "Canabidiol",
    "alternateName": "CBD"
  }
}""",
        "```",
        "",
    ]

    # ── REC 4: BreadcrumbList ─────────────────────────────────────────────────
    linhas += [
        "---",
        "### 4️⃣  Implementar BreadcrumbList em Todas as Páginas",
        "",
        "**Prioridade:** 🟡 Média | **Impacto:** Exibe o caminho de navegação no SERP "
        "(ex.: Início › Blog › Artigo), melhora CTR e organização para o Googlebot",
        "",
        "```json",
        """{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Início",
      "item": "https://www.weedoo.med.br/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Blog",
      "item": "https://www.weedoo.med.br/blog/"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Cannabis Medicinal para Epilepsia Refratária",
      "item": "https://www.weedoo.med.br/blog/cannabis-medicinal-epilepsia/"
    }
  ]
}""",
        "```",
        "",
    ]

    # ── REC 5: WebSite + Organization na Home ─────────────────────────────────
    linhas += [
        "---",
        "### 5️⃣  Implementar WebSite (SearchAction) e Organization na Página Inicial",
        "",
        "**Prioridade:** 🟡 Média | **Impacto:** Habilita o Sitelinks Search Box da Weedoo "
        "no Google, consolida o Knowledge Panel da organização",
        "",
        "```json",
        """{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://www.weedoo.med.br/#website",
      "name": "Weedoo — Marketing Digital para Medicina Endocanabinoide",
      "url": "https://www.weedoo.med.br/",
      "description": "A primeira agência de marketing digital especializada em medicina endocanabinoide no Brasil. Unindo ciência comprovada e engenharia de marketing.",
      "inLanguage": "pt-BR",
      "potentialAction": {
        "@type": "SearchAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://www.weedoo.med.br/?s={search_term_string}"
        },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "Organization",
      "@id": "https://www.weedoo.med.br/#organization",
      "name": "Weedoo",
      "url": "https://www.weedoo.med.br/",
      "description": "Agência de marketing digital especializada em medicina endocanabinoide, compliance Anvisa/CFM e estratégias E-E-A-T para clínicas e médicos.",
      "logo": {
        "@type": "ImageObject",
        "url": "https://www.weedoo.med.br/wp-content/uploads/logo-weedoo.png",
        "width": 600,
        "height": 60
      },
      "sameAs": [
        "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"
      ],
      "foundingDate": "2023",
      "areaServed": "BR",
      "knowsAbout": [
        "Marketing Digital",
        "Medicina Endocanabinoide",
        "Cannabis Medicinal",
        "SEO para Saúde",
        "E-E-A-T",
        "Compliance Anvisa"
      ]
    }
  ]
}""",
        "```",
        "",
    ]

    return "\n".join(linhas)


# ─── Seção 5: Instruções de correção ──────────────────────────────────────────

def gerar_instrucoes_correcao(resultados_weedoo: list[dict]) -> str:
    """Gera instruções práticas de correção para os erros encontrados."""
    linhas = ["## 🔧 Instruções de Correção\n"]

    paginas_com_erros = {
        _url_curta(r["url"]): r.get("todos_erros", [])
        for r in resultados_weedoo
        if r.get("todos_erros")
    }

    if not paginas_com_erros:
        linhas.append(
            "✅ **Nenhum erro crítico encontrado!** "
            "Continue monitorando semanalmente para manter a qualidade.\n"
        )
        return "\n".join(linhas)

    linhas += [
        "### Como Implementar as Correções",
        "",
        "**Opção A — WordPress com Rank Math SEO (recomendado):**",
        "1. Instale o plugin [Rank Math SEO](https://rankmath.com/) (gratuito).",
        "2. Acesse cada artigo → aba **Schema** no editor → selecione o tipo → preencha os campos.",
        "3. Para campos avançados (sameAs, MedicalWebPage), use o **Schema Builder** do Rank Math Pro.",
        "",
        "**Opção B — JSON-LD manual via plugin:**",
        "1. Instale [Insert Headers and Footers](https://wordpress.org/plugins/insert-headers-and-footers/).",
        "2. Cole o JSON-LD gerado pelas recomendações acima dentro de uma tag `<script type='application/ld+json'>`.",
        "3. Para cada post, use o campo de código personalizado do Rank Math (aba Schema → Custom Schema).",
        "",
        "**Validação pós-correção:**",
        "- [Rich Results Test — Google](https://search.google.com/test/rich-results) ← **obrigatório**",
        "- [Schema Markup Validator](https://validator.schema.org/)",
        "",
        "**Prioridade de correção:** Páginas 🔴 Crítico → 🟡 Atenção → 🟢 OK",
        "",
        "---",
        "### Erros Específicos por Página\n",
    ]

    for url_curta, erros in paginas_com_erros.items():
        linhas.append(f"**`{url_curta}`** ({len(erros)} erro(s))\n")
        for i, erro in enumerate(erros, 1):
            linhas.append(f"{i}. {erro}")
        linhas.append("")

    return "\n".join(linhas)


# ─── Montagem do relatório completo ───────────────────────────────────────────

def gerar_relatorio(
    resultados_weedoo: list[dict],
    comparacao: list[dict],
) -> str:
    """
    Monta o relatório Markdown completo com todas as seções.

    Args:
        resultados_weedoo: Lista de resultados de análise das páginas da Weedoo.
        comparacao: Lista de resultados de análise dos concorrentes.

    Returns:
        String Markdown do relatório completo.
    """
    hoje_fmt = date.today().strftime("%d/%m/%Y")
    hoje_iso = date.today().isoformat()

    cabecalho = f"""# 📋 Relatório de Schema Markup — Weedoo
> **Data:** {hoje_fmt} &nbsp;|&nbsp; **Gerado por:** WeedooSEOMonitorBot &nbsp;|&nbsp; **Nicho:** Medicina Endocanabinoide

---

"""

    rodape = f"""
---

## 🔗 Links Úteis para Validação e Referência

| Ferramenta | Link |
|------------|------|
| Rich Results Test (Google) | https://search.google.com/test/rich-results |
| Schema Markup Validator | https://validator.schema.org/ |
| Google Search Console | https://search.google.com/search-console |
| Schema.org — MedicalWebPage | https://schema.org/MedicalWebPage |
| Schema.org — Article | https://schema.org/Article |
| Guia E-E-A-T Google | https://developers.google.com/search/docs/fundamentals/creating-helpful-content |
| Diretrizes YMYL Google | https://developers.google.com/search/docs/fundamentals/creating-helpful-content |
| Regulamentação Anvisa Cannabis | https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa/2019/anvisa-aprova-resolucao-sobre-produtos-a-base-de-canabis |

---
*Relatório gerado automaticamente em {hoje_fmt} pelo WeedooSEOMonitorBot.*
*Repositório: https://github.com/agenciaweedoo — Contato: contato@weedoo.med.br*
"""

    secoes = [
        cabecalho,
        gerar_sumario_executivo(resultados_weedoo, comparacao),
        gerar_tabela_cobertura(resultados_weedoo),
        gerar_tabela_comparativa(resultados_weedoo, comparacao),
        gerar_recomendacoes(resultados_weedoo, comparacao),
        gerar_instrucoes_correcao(resultados_weedoo),
        rodape,
    ]

    return "\n".join(secoes)


# ─── Salvar e publicar ────────────────────────────────────────────────────────

def salvar_relatorio(relatorio_md: str, reports_dir: Path) -> Path:
    """
    Salva o relatório Markdown no diretório /reports.

    Args:
        relatorio_md: Conteúdo Markdown do relatório.
        reports_dir: Caminho do diretório /reports.

    Returns:
        Caminho completo do arquivo salvo.
    """
    nome_arquivo = f"{date.today().isoformat()}-schema-report.md"
    caminho = reports_dir / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(relatorio_md)

    logger.info("✅ Relatório salvo: %s", caminho)
    return caminho


def publicar_issue_github(relatorio_md: str) -> None:
    """
    Publica o relatório como Issue no GitHub via PyGithub.

    Usa as variáveis de ambiente GITHUB_TOKEN e GITHUB_REPOSITORY,
    que são injetadas automaticamente pelo GitHub Actions.
    A label 'schema-report' é criada automaticamente se não existir.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo_name = os.environ.get("GITHUB_REPOSITORY")

    if not token:
        logger.warning("GITHUB_TOKEN não encontrado — Issue não será criada.")
        return
    if not repo_name:
        logger.warning("GITHUB_REPOSITORY não encontrado — Issue não será criada.")
        return

    try:
        from github import Github, GithubException  # type: ignore[import]

        gh = Github(token)
        repo = gh.get_repo(repo_name)

        # Garantir que a label existe
        label_name = "schema-report"
        try:
            repo.get_label(label_name)
        except GithubException:
            try:
                repo.create_label(
                    name=label_name,
                    color="0075ca",
                    description="Relatório automático semanal de Schema Markup — WeedooSEOBot",
                )
                logger.info("Label '%s' criada no repositório.", label_name)
            except GithubException as exc:
                logger.warning("Não foi possível criar a label '%s': %s", label_name, exc)

        # Criar a Issue
        titulo = f"📊 Schema Markup Report — {date.today().strftime('%d/%m/%Y')}"

        # GitHub limita o corpo da issue a 65.536 caracteres
        corpo = relatorio_md
        if len(relatorio_md) > 65_000:
            corpo = relatorio_md[:64_800]
            corpo += (
                "\n\n---\n"
                "> ⚠️ *Relatório truncado por limite do GitHub Issues. "
                "Consulte o arquivo completo em `/reports/`.*"
            )

        issue = repo.create_issue(
            title=titulo,
            body=corpo,
            labels=[label_name],
        )
        logger.info("✅ Issue criada com sucesso: %s", issue.html_url)

    except ImportError:
        logger.error(
            "PyGithub não instalado. Execute: pip install PyGithub"
        )
    except Exception as exc:
        logger.error("Erro ao criar Issue no GitHub: %s", exc)
