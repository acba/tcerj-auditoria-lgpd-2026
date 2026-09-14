# Geração de documentos

Os arquivos Markdown são as fontes canônicas; nunca edite diretamente os produtos gerados.

```bash
# Matriz: valida e gera o DOCX com o template fixo da skill.
python3 .agents/skills/criar-matriz-planejamento/scripts/build_matrix.py "01-Planejamento/02-Matriz_de_Planejamento/matriz_planejamento.md"

# Questionário: valida e gera LSS e DOCX; o mecanismo explícito evita variação entre ambientes.
python3 .agents/skills/elaborar-survey-limesurvey/scripts/survey_tool.py build-all "02-Execução/01-Questionário/questionario_lgpd_2026.md" "02-Execução/01-Questionário/questionario_lgpd_2026" --engine python-docx --strict
```

Corrija erros ou avisos no Markdown e execute novamente o comando correspondente.
