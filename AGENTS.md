# Geração de documentos

Os arquivos Markdown são as fontes canônicas; nunca edite diretamente os produtos gerados.

```bash
# Matriz: valida e gera o DOCX com o template fixo da skill.
python3 .agents/skills/criar-matriz-planejamento/scripts/build_matrix.py "01-Planejamento/02-Matriz_de_Planejamento/matriz_planejamento.md"

# Questionário: valida/gera o LSS e gera o DOCX institucional.
python3 .agents/skills/elaborar-survey-limesurvey/scripts/survey_tool.py build "02-Execução/01-Questionário/questionario_lgpd_2026.md" "02-Execução/01-Questionário/questionario_lgpd_2026.lss" --strict
python3 98-scripts/gera_questionario_docx.py "02-Execução/01-Questionário/questionario_lgpd_2026.md" "02-Execução/01-Questionário/questionario_lgpd_2026.docx" --reference-docx "/home/acba/workspace/fiscalizacoes/202601-igovti/01-Planejamento/02-Metodologia_iGovTI/igovti_2026.docx"
```

Corrija erros ou avisos no Markdown e execute novamente o comando correspondente.
