# Weedoo Schema Monitor

Agente semanal que audita Schema Markup da Weedoo e compara com concorrentes, gerando recomendações de SEO/GEO/AEO.

## Como usar
1. Clone este repositório.
2. Substitua `{{LINKEDIN_URL}}` em `src/comparador.py` pela URL real do LinkedIn de Carlos Macedo.
3. Verifique as URLs em `config/`.
4. O GitHub Actions roda automaticamente toda segunda-feira.

## Execução manual
```bash
pip install -r requirements.txt
python src/monitor.py
