from datetime import datetime

EXEMPLOS_JSONLD = {
    "FAQ": """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "O que é o sistema endocanabinoide?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "É um sistema de sinalização celular presente em todos os mamíferos, descoberto em 1988 por Howlett."
    }
  }]
}
</script>""",
    "HowTo": """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "Como criar um plano de tratamento com CBD",
  "step": [{
    "@type": "HowToStep",
    "name": "Avaliação inicial",
    "text": "Realize anamnese completa e histórico do paciente."
  }]
}
</script>""",
    "MedicalWebPage": """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MedicalWebPage",
  "headline": "Guia de CBD para Dor Crônica",
  "datePublished": "2026-06-25",
  "reviewedBy": {
    "@type": "Physician",
    "name": "Carlos Macedo"
  }
}
</script>"""
}

def gerar_relatorio(analise):
    linhas = []
    linhas.append(f"# Relatório de Schema Markup — {analise['data']}\n")
    linhas.append("## 1. Sumário Executivo\n")
    linhas.append(f"Este relatório compara os dados estruturados do site Weedoo com os concorrentes Rocket Med, WeCann Academy e Cannabis & Saúde. Foram encontrados **{len(analise['erros'])} erros** e **{len(analise['recomendacoes'])} oportunidades** de melhoria para ganhar visibilidade em rich snippets e fortalecer E-E-A-T.\n")

    linhas.append("## 2. Cobertura de Schemas da Weedoo\n")
    linhas.append("| Tipo | Presente |")
    linhas.append("|------|----------|")
    for tipo in analise['tipos_weedoo']:
        linhas.append(f"| {tipo} | ✅ |")
    linhas.append("")

    linhas.append("## 3. Comparativo com Concorrentes\n")
    cabecalho = "| Schema | Weedoo | " + " | ".join(analise['tipos_concorrentes'].keys()) + " |"
    linhas.append(cabecalho)
    linhas.append("|" + "---|" * (len(analise['tipos_concorrentes']) + 2))
    todos_tipos = set(analise['tipos_weedoo'])
    for v in analise['tipos_concorrentes'].values():
        todos_tipos.update(v)
    for tipo in sorted(todos_tipos):
        coluna_weedoo = "✅" if tipo in analise['tipos_weedoo'] else "❌"
        colunas_conc = []
        for nome in analise['tipos_concorrentes']:
            colunas_conc.append("✅" if tipo in analise['tipos_concorrentes'][nome] else "❌")
        linhas.append(f"| {tipo} | {coluna_weedoo} | " + " | ".join(colunas_conc) + " |")
    linhas.append("")

    if analise['erros']:
        linhas.append("## 4. Erros Encontrados\n")
        for e in analise['erros']:
            linhas.append(f"- ❌ {e}")
        linhas.append("")

    if analise['recomendacoes']:
        linhas.append("## 5. Top Recomendações (Priorizadas)\n")
        for i, rec in enumerate(analise['recomendacoes'], 1):
            linhas.append(f"### {i}. {rec['acao']}")
            linhas.append(f"- **Concorrentes que já usam:** {', '.join(rec['concorrentes'])}")
            linhas.append(f"- **Impacto no tráfego:** {rec['impacto']}")
            # Exemplo de código se disponível
            tipo_limpo = rec['acao'].replace('Adicionar Schema "', '').replace('"', '')
            if tipo_limpo in EXEMPLOS_JSONLD:
                linhas.append("- **Exemplo de implementação:**\n")
                linhas.append("```html")
                linhas.append(EXEMPLOS_JSONLD[tipo_limpo].strip())
                linhas.append("```")
            linhas.append("")

    linhas.append("---")
    linhas.append("*Relatório gerado automaticamente pelo Weedoo Schema Monitor.*")

    conteudo = "\n".join(linhas)
    nome_arquivo = f"reports/{datetime.now().strftime('%Y-%m-%d')}-schema-report.md"
    with open(nome_arquivo, 'w') as f:
        f.write(conteudo)
    print(f"[RELATÓRIO] Salvo em {nome_arquivo}")
    return nome_arquivo
