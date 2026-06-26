# 📋 Relatório de Schema Markup — Weedoo
> **Data:** 13/01/2025 &nbsp;|&nbsp; **Gerado por:** WeedooSEOMonitorBot &nbsp;|&nbsp; **Nicho:** Medicina Endocanabinoide

---

## 📊 Sumário Executivo

Auditoria realizada em **13/01/2025** cobrindo **8 páginas** da Weedoo (8 acessíveis) e **5 concorrentes** no nicho de Medicina Endocanabinoide no Brasil. Foram identificados **14 erros** e **9 avisos** nos dados estruturados da Weedoo. Do total de páginas analisadas, **3 possuem** schema de artigo (`Article`/`BlogPosting`) implementado — campo crítico para E-E-A-T em conteúdo YMYL (saúde). Em relação à concorrência, **2 de 5 concorrentes** já implementam campos básicos de E-E-A-T (autor + publisher estruturados). A Weedoo **não utiliza** 3 tipo(s) de schema já adotados por concorrentes: `FAQPage`, `MedicalWebPage`, `VideoObject`. As recomendações a seguir estão priorizadas pelo impacto esperado em rich snippets e autoridade de busca.

---

## 🔍 Cobertura de Schemas — Weedoo

| Página | Tipo | Schemas Encontrados | Erros | Avisos | Status |
|--------|------|---------------------|-------|--------|--------|
| `/` | home | `WebSite`, `Organization` | 2 | 1 | 🟡 Atenção |
| `/blog/` | blog_listagem | `WebSite` | 1 | 0 | 🟡 Atenção |
| `/nossos-servicos/` | servicos | ❌ Nenhum | 3 | 0 | 🔴 Crítico |
| `/sobre/` | sobre | `Person`, `WebPage` | 1 | 2 | 🟡 Atenção |
| `/blog/cannabis-medicinal-o-que-e/` | artigo | `Article`, `BreadcrumbList` | 3 | 4 | 🔴 Crítico |
| `/blog/cbd-ansiedade-evidencias/` | artigo | `Article` | 2 | 2 | 🟡 Atenção |
| `/blog/sistema-endocanabinoide/` | artigo | `Article`, `BreadcrumbList` | 2 | 0 | 🟡 Atenção |
| `/blog/anvisa-cannabis-regulamentacao/` | artigo | ❌ Nenhum | 0 | 0 | 🟢 OK |

### 📋 Detalhamento de Erros e Avisos por Página

#### `/`

- 🔴 **ERRO:** Organization.sameAs ausente — LinkedIn da Weedoo não vinculado
- 🔴 **ERRO:** WebSite.potentialAction.query-input ausente — Sitelinks Search Box não habilitado
- 🟡 **AVISO:** Organization.telephone ausente — recomendado para SEO local

#### `/nossos-servicos/`

- 🔴 **ERRO:** Nenhum dado estruturado encontrado nesta página. Isso prejudica severamente a visibilidade em rich snippets.
- 🔴 **ERRO:** Schema 'WebPage' ausente — esperado para páginas do tipo 'servicos'
- 🔴 **ERRO:** Schema 'BreadcrumbList' ausente — esperado para páginas do tipo 'servicos'

#### `/blog/cannabis-medicinal-o-que-e/`

- 🔴 **ERRO:** author.sameAs não contém o LinkedIn do Carlos Macedo.
  Adicionar: 'https://www.linkedin.com/in/carlos-henrique-lopes-macedo/'
- 🔴 **ERRO:** author.sameAs não contém o portfólio do Carlos Macedo.
  Adicionar: 'https://agenciaweedoo.github.io/my-portifolio/'
- 🔴 **ERRO:** publisher.logo ausente — obrigatório para exibição de rich snippets do tipo Article
- 🟡 **AVISO:** Campo 'speakable' ausente — melhora acessibilidade e pode favorecer featured snippets de voz
- 🟡 **AVISO:** Campo 'articleSection' ausente — ajuda o Google a categorizar o conteúdo
- 🟡 **AVISO:** Campo 'keywords' ausente — importante para relevância temática
- 🟡 **AVISO:** Campo 'image' ausente — recomendado para rich snippets de Article

---

## 🥊 Comparativo com Concorrentes

| Schema | Weedoo | Rocket Med | WeCann Academy | Cannabis & Saúde | Dr. Cannabis | Cannect |
|--------|--------|------------|----------------|------------------|--------------|---------|
| `Article` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `BreadcrumbList` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `FAQPage` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `HowTo` | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `MedicalWebPage` | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `Organization` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `Person` | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ |
| `VideoObject` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `WebSite` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 🏆 Análise de E-E-A-T e Autoridade Médica

| Critério | Weedoo | Rocket Med | WeCann Academy | Cannabis & Saúde | Dr. Cannabis | Cannect |
|----------|--------|------------|----------------|------------------|--------------|---------|
| Autor estruturado (E-E-A-T) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Publisher estruturado (E-E-A-T) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Schema médico (MedicalWebPage/Physician) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Rich snippets (FAQ/HowTo/Video) | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| BreadcrumbList | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |

### ⚠️ Tipos de Schema Usados por Concorrentes mas Ausentes na Weedoo

- `FAQPage` — usado por: Cannabis & Saúde, Dr. Cannabis, Cannect
- `MedicalWebPage` — usado por: Cannabis & Saúde, Dr. Cannabis, Cannect
- `VideoObject` — usado por: Dr. Cannabis

---

## 🎯 Top 5 Recomendações Priorizadas

> Cada recomendação inclui o **impacto esperado** e um **JSON-LD pronto para copiar e colar**.

---
### 1️⃣  Implementar/Corrigir Article Schema com E-E-A-T Completo em Todos os Artigos

**Prioridade:** 🔴 Crítica | **Impacto:** Autoridade E-E-A-T, elegibilidade para rich snippets de artigo

O Google usa os campos `author`, `publisher` e datas para avaliar Expertise, Authoritativeness e Trustworthiness (E-E-A-T). Para conteúdo YMYL como medicina, isso é **determinante** para ranqueamento. Todo artigo deve ter o schema abaixo:

```json
{
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
}
```

---
### 2️⃣  Adicionar FAQPage para Capturar Rich Snippets de Perguntas Frequentes

**Prioridade:** 🔴 Alta | **Impacto:** Rich snippets de FAQ no Google (aumenta CTR em 20–40%)

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "O uso de cannabis medicinal é legal no Brasil?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Sim. A Anvisa regulamenta o uso de produtos à base de canabis para fins medicinais pela RDC 327/2019. O paciente precisa de prescrição médica e pode importar ou adquirir produtos registrados pela Anvisa."
      }
    },
    {
      "@type": "Question",
      "name": "O que é o sistema endocanabinoide?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "O sistema endocanabinoide (SEC) é uma rede de receptores e moléculas sinalizadoras presente em todo o organismo humano, responsável por regular funções como dor, inflamação, sono, humor e imunidade."
      }
    }
  ]
}
```

---
### 3️⃣  Implementar MedicalWebPage em Artigos com Conteúdo Clínico

**Prioridade:** 🟡 Alta | **Impacto:** Schema especializado para saúde — reforça E-E-A-T em YMYL

```json
{
  "@context": "https://schema.org",
  "@type": "MedicalWebPage",
  "name": "Cannabis Medicinal para Epilepsia Refratária",
  "url": "https://www.weedoo.med.br/blog/cannabis-medicinal-epilepsia/",
  "lastReviewed": "2025-01-01",
  "reviewedBy": {
    "@type": "Person",
    "name": "Carlos Macedo",
    "url": "https://www.weedoo.med.br/sobre/"
  },
  "specialty": {
    "@type": "MedicalSpecialty",
    "name": "Neurologia"
  }
}
```

---
### 4️⃣  Implementar BreadcrumbList em Todas as Páginas

**Prioridade:** 🟡 Média | **Impacto:** Exibe caminho de navegação no SERP, melhora CTR

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Início", "item": "https://www.weedoo.med.br/" },
    { "@type": "ListItem", "position": 2, "name": "Blog", "item": "https://www.weedoo.med.br/blog/" },
    { "@type": "ListItem", "position": 3, "name": "Título do Artigo", "item": "https://www.weedoo.med.br/blog/slug/" }
  ]
}
```

---
### 5️⃣  Implementar WebSite (SearchAction) e Organization na Página Inicial

**Prioridade:** 🟡 Média | **Impacto:** Sitelinks Search Box + Knowledge Panel da Weedoo

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://www.weedoo.med.br/#website",
      "name": "Weedoo",
      "url": "https://www.weedoo.med.br/",
      "potentialAction": {
        "@type": "SearchAction",
        "target": { "@type": "EntryPoint", "urlTemplate": "https://www.weedoo.med.br/?s={search_term_string}" },
        "query-input": "required name=search_term_string"
      }
    },
    {
      "@type": "Organization",
      "@id": "https://www.weedoo.med.br/#organization",
      "name": "Weedoo",
      "url": "https://www.weedoo.med.br/",
      "logo": { "@type": "ImageObject", "url": "https://www.weedoo.med.br/wp-content/uploads/logo-weedoo.png" },
      "sameAs": ["https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"]
    }
  ]
}
```

---

## 🔧 Instruções de Correção

### Como Implementar as Correções

**Opção A — WordPress com Rank Math SEO (recomendado):**
1. Instale o plugin [Rank Math SEO](https://rankmath.com/) (gratuito).
2. Acesse cada artigo → aba **Schema** no editor → selecione o tipo → preencha os campos.
3. Para campos avançados (sameAs, MedicalWebPage), use o **Schema Builder** do Rank Math Pro.

**Opção B — JSON-LD manual via plugin:**
1. Instale [Insert Headers and Footers](https://wordpress.org/plugins/insert-headers-and-footers/).
2. Cole o JSON-LD gerado pelas recomendações acima dentro de uma tag `<script type='application/ld+json'>`.

**Validação pós-correção:**
- [Rich Results Test — Google](https://search.google.com/test/rich-results) ← **obrigatório**
- [Schema Markup Validator](https://validator.schema.org/)

**Prioridade de correção:** Páginas 🔴 Crítico → 🟡 Atenção → 🟢 OK

---
### Erros Específicos por Página

**`/nossos-servicos/`** (3 erro(s))

1. Nenhum dado estruturado encontrado nesta página.
2. Schema 'WebPage' ausente — esperado para páginas do tipo 'servicos'
3. Schema 'BreadcrumbList' ausente

**`/blog/cannabis-medicinal-o-que-e/`** (3 erro(s))

1. author.sameAs não contém o LinkedIn do Carlos Macedo. Adicionar: 'https://www.linkedin.com/in/carlos-henrique-lopes-macedo/'
2. author.sameAs não contém o portfólio do Carlos Macedo. Adicionar: 'https://agenciaweedoo.github.io/my-portifolio/'
3. publisher.logo ausente — obrigatório para exibição de rich snippets do tipo Article

---

## 🔗 Links Úteis para Validação e Referência

| Ferramenta | Link |
|------------|------|
| Rich Results Test (Google) | https://search.google.com/test/rich-results |
| Schema Markup Validator | https://validator.schema.org/ |
| Google Search Console | https://search.google.com/search-console |
| Schema.org — MedicalWebPage | https://schema.org/MedicalWebPage |
| Guia E-E-A-T Google | https://developers.google.com/search/docs/fundamentals/creating-helpful-content |

---
*Relatório gerado automaticamente em 13/01/2025 pelo WeedooSEOMonitorBot.*
*Repositório: https://github.com/agenciaweedoo — Contato: contato@weedoo.med.br*
