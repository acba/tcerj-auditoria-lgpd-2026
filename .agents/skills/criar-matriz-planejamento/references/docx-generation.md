# Geração do DOCX

A skill é autocontida. O gerador usa `scripts/matrix_engine.py` e o template de `assets/`.

## Metadados recomendados

No início de `matriz_planejamento.md`:

```yaml
---
title: "Fiscalização ..."
fiscalizacao: "22/2026"
jurisdicionados: "órgãos ou entidades auditadas"
objetivo_auditoria: "Verificar ..."
---
```

## Validar

```bash
python scripts/validate_matrix.py matriz_planejamento.md
```

## Gerar

```bash
python scripts/build_matrix.py matriz_planejamento.md
```

Saída padrão:

`matriz_planejamento.docx`

no mesmo diretório da matriz.

O gerador bloqueia erros. Por padrão também bloqueia avisos para forçar revisão consciente. Depois de revisar os avisos, use:

```bash
python scripts/build_matrix.py matriz_planejamento.md --allow-warnings
```

## Overrides

É possível substituir metadados sem alterar o arquivo:

```bash
python scripts/build_matrix.py matriz_planejamento.md \
  --fiscalizacao "22/2026" \
  --jurisdicionados "órgãos ou entidades auditadas" \
  --objetivo-auditoria "Verificar ..."
```

Para usar outro template institucional:

```bash
python scripts/build_matrix.py matriz_planejamento.md --template outro-template.docx
```

O template deve manter a estrutura tabular esperada: linha de questão, linha de riscos e tabela de seis colunas para fontes, informações requeridas, critérios, procedimentos, evidências e achados/análise.

Na renderização de uma questão declarada como `natureza: levantamento`, a linha de riscos e a coluna de critérios são omitidas do DOCX, pois o levantamento não formula risco de achado nem critério de conformidade.
