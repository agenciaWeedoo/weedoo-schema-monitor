# 🌿 Weedoo Schema Monitor

> Agente autônomo de monitoramento semanal de Schema Markup para [Weedoo.med.br](https://www.weedoo.med.br/)  
> Medicina Endocanabinoide | E-E-A-T máximo | Compliance Anvisa/CFM

[![Schema Monitor](https://github.com/agenciaweedoo/weedoo-schema-monitor/actions/workflows/weekly-schema-check.yml/badge.svg)](https://github.com/agenciaweedoo/weedoo-schema-monitor/actions)

---

## O que este agente faz

Toda **segunda-feira às 06:00 BRT** (via GitHub Actions, 100% gratuito), o bot:

1. **Extrai e valida** todos os dados estruturados (JSON-LD, Microdata) das páginas da Weedoo
2. **Verifica E-E-A-T** do autor Carlos Macedo em todos os artigos (nome, URL Sobre, LinkedIn, Portfólio)
3. **Compara** com 5 concorrentes (home + blog + 3 artigos recentes de cada)
4. **Gera relatório** em Markdown com erros, avisos, tabelas comparativas e JSON-LDs prontos
5. **Salva** o relatório em `/reports/YYYY-MM-DD-schema-report.md`
6. **Publica** o relatório como Issue no GitHub com a label `schema-report`

---

## Estrutura do Projeto

```
/
├── .github/
│   └── workflows/
│       └── weekly-schema-check.yml   ← Workflow do GitHub Actions
├── src/
│   ├── monitor.py                    ← Script principal (orquestrador)
│   ├── comparador.py                 ← Análise dos concorrentes
│   ├── relatorio.py                  ← Geração do relatório + Issue GitHub
│   └── utils.py                      ← Utilitários compartilhados
├── config/
│   ├── urls_weedoo.txt               ← URLs das páginas da Weedoo a monitorar
│   └── concorrentes.json             ← Lista de concorrentes a comparar
├── reports/
│   └── YYYY-MM-DD-schema-report.md  ← Relatórios gerados automaticamente
└── README.md
```

---

## ⚡ Configuração Inicial (5 minutos)

### 1. Fork ou clone este repositório

```bash
git clone https://github.com/agenciaweedoo/weedoo-schema-monitor.git
cd weedoo-schema-monitor
```

### 2. Verificar os arquivos de configuração

**`config/urls_weedoo.txt`** — URLs das páginas da Weedoo a monitorar:
```
https://www.weedoo.med.br/
https://www.weedoo.med.br/blog/
https://www.weedoo.med.br/nossos-servicos/
https://www.weedoo.med.br/sobre/
```
➕ Adicione URLs de artigos específicos conforme necessário.

**`config/concorrentes.json`** — Lista de concorrentes (já configurado com 5 concorrentes):
- Rocket Med
- WeCann Academy
- Cannabis & Saúde
- **Dr. Cannabis** ← adicionado
- **Cannect** ← adicionado

### 3. Ativar o GitHub Actions

O workflow roda automaticamente no repositório. Verifique se Actions está habilitado:
- Vá em `Settings → Actions → General → Allow all actions`

### 4. Verificar permissões do GITHUB_TOKEN

Vá em `Settings → Actions → General → Workflow permissions`:
- Selecione **"Read and write permissions"**
- Marque **"Allow GitHub Actions to create and approve pull requests"**

> ✅ O `GITHUB_TOKEN` já é injetado automaticamente pelo GitHub Actions — **não é necessário criar nenhum segredo adicional**.

---

## 🖥️ Execução Local (desenvolvimento/testes)

### Instalar dependências

```bash
pip install requests beautifulsoup4 extruct lxml w3lib PyGithub
```

### Executar o monitor

```bash
# A partir da raiz do repositório
python src/monitor.py
```

> Para execução local, o relatório será salvo em `/reports/` mas a Issue do GitHub não será criada (sem `GITHUB_TOKEN`).

### Executar manualmente via GitHub Actions

Vá em `Actions → Monitoramento Semanal de Schema Markup → Run workflow`.

---

## 🔧 Personalização

### Alterar a URL do LinkedIn do Carlos Macedo

Edite a constante `AUTOR_LINKEDIN` em `src/utils.py`:
```python
AUTOR_LINKEDIN = "https://www.linkedin.com/in/carlos-henrique-lopes-macedo/"
```

### Adicionar novos concorrentes

Edite `config/concorrentes.json` adicionando um novo objeto:
```json
{
  "nome": "Nome do Concorrente",
  "home": "https://exemplo.com.br",
  "blog": "https://exemplo.com.br/blog",
  "notas": "Descrição opcional"
}
```

### Adicionar URLs específicas para monitoramento

Edite `config/urls_weedoo.txt`, adicionando uma URL por linha.

### Alterar o horário de execução

Edite o cron em `.github/workflows/weekly-schema-check.yml`:
```yaml
- cron: '0 9 * * 1'   # Toda segunda-feira às 09:00 UTC (06:00 BRT)
```
Use [crontab.guru](https://crontab.guru/) para gerar outros horários.

---

## 📊 Lendo os Relatórios

Os relatórios são gerados em `/reports/YYYY-MM-DD-schema-report.md` e publicados como Issues com a label `schema-report`.

**Legenda de status:**
| Símbolo | Significado |
|---------|-------------|
| 🟢 OK | Nenhum erro encontrado |
| 🟡 Atenção | 1–2 erros (corrija em breve) |
| 🔴 Crítico | 3+ erros (corrija imediatamente) |
| ⚫ Inacessível | Página retornou erro HTTP |

---

## 🛡️ Scraping Ético

O agente segue boas práticas de scraping:
- **Delay de 2 segundos** entre cada requisição
- **Respeita robots.txt** de todos os domínios
- **User-Agent identificado** como WeedooSEOMonitorBot
- **Sem acesso forçado** a páginas bloqueadas

---

## Schemas Validados

| Tipo | Campos Verificados |
|------|--------------------|
| `Article` | headline, author (Carlos Macedo + 3 links), datePublished, dateModified, publisher, image |
| `WebSite` | name, url, potentialAction (SearchAction) |
| `Organization` | name, url, logo, sameAs |
| `Person` | name, url, sameAs |
| `BreadcrumbList` | itemListElement |
| `FAQPage` | mainEntity |
| `MedicalWebPage` | name, url, specialty, reviewedBy |
| `HowTo` | name, step |
| `Physician` | name, url, medicalSpecialty |
| `VideoObject` | name, description, thumbnailUrl, uploadDate |

---

## 📝 Campos E-E-A-T Obrigatórios (Regra de Ouro)

Todo artigo do blog **deve** ter o autor Carlos Macedo com os três links abaixo no campo `sameAs`:

| Campo | Valor Esperado |
|-------|----------------|
| `author.name` | `Carlos Macedo` |
| `author.url` | `https://www.weedoo.med.br/sobre/` |
| `author.sameAs[0]` | `https://www.linkedin.com/in/carlos-henrique-lopes-macedo/` |
| `author.sameAs[1]` | `https://agenciaweedoo.github.io/my-portifolio/` |

---

## Dependências

| Biblioteca | Versão | Uso |
|------------|--------|-----|
| `requests` | 2.31.0 | Requisições HTTP |
| `beautifulsoup4` | 4.12.3 | Parsing de HTML para extração de links |
| `extruct` | 0.16.0 | Extração de schemas (JSON-LD, Microdata, RDFa) |
| `lxml` | 5.2.2 | Parser HTML de alta performance (dependência do extruct) |
| `w3lib` | 2.1.2 | Resolução de URLs base |
| `PyGithub` | 2.3.0 | Publicação de Issues no GitHub |

---

*Desenvolvido para Weedoo Marketing Digital | Medicina Endocanabinoide*  
*Contato: contato@weedoo.med.br | https://www.weedoo.med.br/*
