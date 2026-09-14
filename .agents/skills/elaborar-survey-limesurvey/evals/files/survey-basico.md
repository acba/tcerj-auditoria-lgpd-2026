---
title: "Diagnóstico de governança de dados"
language: "pt-BR"
sid: 910001
admin: "Equipe de Auditoria"
adminemail: "auditoria@example.org"
welcome: |
  <p>Responda considerando a situação vigente em 31/12/2025.</p>
endtext: |
  <p>Obrigado pela participação.</p>
---

# Diagnóstico de governança de dados

## Grupo: g0100 | Responsabilidades
> Este grupo identifica responsabilidades institucionalizadas.

### q0101 [single]
question: **Existe unidade formalmente responsável pela governança de dados?**
mandatory: true
options:
- A | Sim
- B | Não
- C | Não foi possível informar

### q0102 [short]
question: **Informe o nome da unidade responsável.**
mandatory: true
visible_if: q0101 == A

