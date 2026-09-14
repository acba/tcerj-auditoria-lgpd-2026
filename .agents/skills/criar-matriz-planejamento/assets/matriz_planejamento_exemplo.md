---
title: "Exemplo de Matriz de Planejamento"
fiscalizacao: "00/2026"
jurisdicionados: "Organizações auditadas"
objetivo_auditoria: "Avaliar o objeto selecionado e produzir diagnóstico complementar."
---

# Matriz de Planejamento

## Questão Geral de Auditoria

questao_geral: Em que medida o objeto auditado atende aos requisitos selecionados e qual é o seu perfil de implementação?

## Questão 01 - Controle normativo

questao: Q1. A organização formalizou e acompanha o controle selecionado conforme o dispositivo aplicável?

subquestoes:
- O controle foi formalmente instituído e aprovado?
- Há acompanhamento periódico de sua implementação?

riscos:
- R1.1: Devido à ausência de formalização e acompanhamento, o controle poderá ser executado de forma inconsistente, comprometendo o alcance de seus objetivos.

fontes_de_informacao:
- F1: Gestor responsável pelo processo auditado.
- F2: Sistema eletrônico de processos administrativos da organização.

informacoes_requeridas:
- IR1: ato de instituição, autoridade aprovadora, vigência e responsabilidades; [F1, F2]
- IR2: registros de acompanhamento, responsáveis, prazos e status das ações; [F1, F2]

criterios:
- id: C1
  descricao: >-
    Norma interna de exemplo, item 4.2 — requisito específico de formalização, aprovação e definição de responsabilidades a ser testado.

procedimentos:
- P1: Examinar o ato de instituição e a versão vigente do documento de controle para confirmar aprovação por autoridade competente, vigência, escopo e responsabilidades definidas; [IR1]
- P2: Examinar os registros de acompanhamento produzidos nos últimos 12 meses para verificar responsáveis, prazos, status e evidências de monitoramento das ações previstas; [IR2]

evidencias:
- E1: ato formal e documento vigente contendo aprovação, escopo e responsabilidades; [P1]
- E2: registros periódicos de acompanhamento com responsáveis, prazos, status e evidências de monitoramento; [P2]

possiveis_achados:
- A1: Fragilidade na formalização ou no acompanhamento do controle selecionado.
  situacoes_encontradas:
  - S1.1:
      descricao: Ausência de formalização válida do controle selecionado.
      referencias_matriz: [R1.1, P1, E1]
      criterios: [C1]
  - S1.2:
      descricao: Ausência de acompanhamento periódico da implementação do controle.
      referencias_matriz: [R1.1, P2, E2]
      criterios: [C1]

---

## Questão Transversal - Diagnóstico descritivo

natureza: levantamento
gera_achado: false
questao: QT1. Qual é o perfil de implementação do objeto entre as organizações avaliadas?

subquestoes:
- Como se distribuem os níveis de implementação?
- Quais fatores são mais frequentemente associados às diferenças observadas?

fontes_de_informacao:
- F1: Gestores das organizações avaliadas, por meio do instrumento de coleta.
- F2: Base consolidada de respostas mantida pela equipe de auditoria.

informacoes_requeridas:
- IR1: respostas e indicadores necessários à classificação do nível de implementação; [F1, F2]
- IR2: justificativas e fatores associados às diferenças observadas; [F1, F2]

procedimentos:
- P1: Calcular a distribuição dos níveis de implementação segundo a regra definida na metodologia e estratificar os resultados por grupo de organizações; [IR1]
- P2: Tabular e categorizar as justificativas apresentadas pelos gestores, identificando frequência e concentração dos fatores reportados; [IR2]

evidencias:
- E1: tabela consolidada de distribuição dos níveis de implementação por grupo; [P1]
- E2: matriz temática de fatores reportados e respectivas frequências; [P2]

o_que_a_analise_permite_dizer:
- O perfil agregado de implementação do objeto avaliado.
- Os fatores mais frequentemente associados às diferenças observadas.

limitacoes_e_cautelas:
- Informações autodeclaradas devem ser interpretadas segundo a qualidade e a consistência dos dados disponíveis.
