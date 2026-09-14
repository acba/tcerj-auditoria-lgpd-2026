# Modelo canônico da matriz

## Front matter

```yaml
---
title: "Título da fiscalização"
fiscalizacao: "00/2026"
jurisdicionados: "órgãos ou entidades auditadas"
objetivo_auditoria: "Objetivo geral do trabalho"
---
```

Depois do front matter:

```markdown
# Matriz de Planejamento

## Questão Geral de Auditoria

questao_geral: [pergunta geral]
```

## Questão normativa

```yaml
## Questão 01 - Tema

questao: Q1. [pergunta avaliativa]?

subquestoes:
- [subquestão testável]

riscos:
- R1.1: Devido a [causa], poderá ocorrer [evento], levando a [efeito] e impactando [consequência].

fontes_de_informacao:
- F1: [ator, unidade, órgão, sistema, base ou repositório].

informacoes_requeridas:
- IR1: [informação necessária]; [F1]

criterios:
- id: C1
  descricao: >-
    [norma/referencial], [dispositivo específico] — [requisito concreto a testar].
  natureza_fundamento: [opcional]
  apto_a_fundamentar_determinacao: false

procedimentos:
- P1: [ação específica + objeto + atributos/teste + universo/amostra/período quando relevante]; [IR1]

evidencias:
- E1: [elemento observável esperado]; [P1]

possiveis_achados:
- A1: [hipótese estruturante]
  situacoes_encontradas:
  - S1.1:
      descricao: [condição negativa específica]
      referencias_matriz: [R1.1, P1, E1]
      criterios: [C1]
```

`natureza_fundamento`, `apto_a_fundamentar_determinacao`, `severidade`, `regra_de_identificacao`, encaminhamentos e variantes são opcionais. Preserve-os quando necessários ao fluxo local.

## Questão de levantamento

```yaml
## Questão Transversal - Tema descritivo

natureza: levantamento
gera_achado: false
questao: QT1. [pergunta descritiva]?

subquestoes:
- [subquestão]

fontes_de_informacao:
- F1: [ator, unidade, órgão, sistema ou base].

informacoes_requeridas:
- IR1: [informação necessária]; [F1]

procedimentos:
- P1: [procedimento analítico específico]; [IR1]

evidencias:
- E1: [tabela, painel, base consolidada, resultado de cálculo ou outra saída]; [P1]

o_que_a_analise_permite_dizer:
- [conclusão descritiva possível]

limitacoes_e_cautelas:
- [limitação metodológica ou de dados]
```

Não inclua `possiveis_achados` numa questão de levantamento.
