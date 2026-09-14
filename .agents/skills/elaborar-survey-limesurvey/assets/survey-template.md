---
title: "Título do questionário"
language: "pt-BR"
sid: 900001
admin: "Equipe responsável"
adminemail: "equipe@example.org"
format: G
template: fruity
welcome: |
  <p>Explique a finalidade, a população respondente, a data-base e como obter ajuda.</p>
endtext: |
  <p>Agradeça a participação e informe os próximos passos.</p>
---

# Título do questionário

## Escala: sim_nao
type: single
- sim | Sim
- nao | Não

## Grupo: g0100 | Identificação e contexto
> Explique por que estas informações são necessárias.

### q0101 [single]
question: **A organização possui responsável formalmente designado pelo tema avaliado?**
mandatory: true
help: Considere a situação vigente na data-base informada na abertura.
options:
- A | Sim
- B | Não
- C | Não foi possível informar

### q0102 [short]
question: **Informe o cargo ou a unidade do responsável, sem registrar dados pessoais desnecessários.**
mandatory: false
visible_if: q0101 == A

## Grupo: g0200 | Prática avaliada
> Responda considerando a prática institucional e os registros vigentes.

### q0201 [adoption]
question: **A organização mantém processo formal para a prática avaliada?**
mandatory: true
help: Considere processo aprovado, implementado e utilizado pela organização.
evidence_text: Envie o ato, procedimento ou registro vigente que sustenta a resposta, ocultando dados pessoais não necessários.

subquestions:
- A | há papéis e responsabilidades definidos
- B | há procedimento documentado
- C | a execução produz registros
- D | os resultados são monitorados

