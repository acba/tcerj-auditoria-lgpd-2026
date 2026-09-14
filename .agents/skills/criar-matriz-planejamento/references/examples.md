# Exemplos rápidos

## Fonte

Ruim:

`F1: Respostas ao questionário.`

Melhor:

`F1: Gestores responsáveis pelo processo auditado, por meio do questionário eletrônico.`

## Critério

Ruim:

`C1: ABNT NBR ISO/IEC 27001:2022.`

Melhor:

`C1: [norma aplicável], cláusula/item confirmado — [requisito concreto que será testado].`

## Procedimento

Ruim:

`P1: Verificar a conformidade do plano; [IR1]`

Melhor:

`P1: Examinar a versão vigente do plano e o ato de aprovação para verificar autoridade aprovadora, período de vigência, objetivos, responsáveis, prazos e mecanismo de acompanhamento; [IR1]`

## Rastreabilidade

```yaml
IR1: plano vigente, aprovação, responsáveis e prazos; [F1]
P1: Examinar plano e ato de aprovação para verificar vigência, aprovação, responsáveis e prazos; [IR1]
E1: Plano vigente e ato de aprovação contendo os atributos testados; [P1]
...
S1.1:
  descricao: Ausência de plano formal vigente.
  referencias_matriz: [R1.1, P1, E1]
  criterios: [C1]
```
