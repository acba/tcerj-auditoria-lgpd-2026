# Formato SurveyMD

## Sumário

1. Estrutura geral
2. Front matter
3. Escalas
4. Grupos e perguntas
5. Tipos
6. Diretivas
7. Macro `adoption`
8. Condições `visible_if`
9. Evidências
10. Targets

## 1. Estrutura geral

```markdown
---
title: "Questionário de exemplo"
language: "pt-BR"
sid: 900001
admin: "Equipe responsável"
adminemail: "equipe@example.org"
format: G
template: fruity
welcome: |
  <p>Texto de abertura.</p>
endtext: |
  <p>Texto de encerramento.</p>
---

# Questionário de exemplo

## Escala: sim_nao
type: single
- sim | Sim
- nao | Não

## Grupo: g0100 | Identificação
> Descrição apresentada no início do grupo.

### q0101 [single]
question: **A organização possui responsável formalmente designado?**
mandatory: true
options:
- A | Sim
- B | Não
```

Use códigos ASCII estáveis, iniciados por letra e compostos por letras, números ou `_`. Evite renomeá-los depois que houver respostas exportadas.

## 2. Front matter

O bloco entre `---` aceita pares `chave: valor`. Textos longos podem usar `|` seguido de linhas indentadas.

Campos usuais:

- `title`: título do survey;
- `language`: idioma, normalmente `pt-BR`;
- `sid`: identificador numérico usado na geração;
- `admin` e `adminemail`: responsável;
- `format`: `G` para grupo por grupo, `S` para uma pergunta por página ou `A` para tudo em uma página;
- `template`: tema do LimeSurvey;
- `welcome` e `endtext`: abertura e encerramento, podendo conter HTML;
- `target`: lista separada por vírgulas para gerar variantes.

## 3. Escalas

```markdown
## Escala: concordancia
type: single
- 1 | Discordo totalmente
- 2 | Discordo parcialmente
- 3 | Nem concordo nem discordo
- 4 | Concordo parcialmente
- 5 | Concordo totalmente
```

Uma pergunta referencia a escala com `scale: concordancia`.

As escalas internas `adocao` e `nao_aplicabilidade` são disponibilizadas automaticamente pelo conversor.

## 4. Grupos e perguntas

Declare grupos assim:

```markdown
## Grupo: g0200 | Governança e responsabilidades
> Explique o objetivo do grupo sem sugerir respostas.
>
> Separe parágrafos com uma linha contendo apenas `>`.
>
> **Referências úteis:**
>
> - [Lei ou documento de referência](https://example.org/documento)
> - Norma técnica, item específico
```

As descrições de grupo aceitam parágrafos, `**negrito**`, `*itálico*`,
`` `código` ``, listas numeradas ou não numeradas e links Markdown. O conversor
preserva essas estruturas tanto no HTML do LSS quanto no guia DOCX.

Declare perguntas assim:

```markdown
### q0201 [single]
question: **Quem aprova a política?**
mandatory: true
help: Considere a versão vigente na data-base da coleta.
options:
- A | Autoridade máxima
- B | Comitê delegado
- C | Outra autoridade
- D | Não há política aprovada
```

`options:` define alternativas/colunas. `subquestions:` ou `rows:` define subquestões/linhas.

## 5. Tipos

| SurveyMD | LimeSurvey | Uso |
|---|---|---|
| `single` | lista | uma alternativa |
| `multi` | múltipla escolha | zero ou mais alternativas |
| `short` | texto curto | identificador ou resposta curta |
| `long` | texto longo | justificativa ou descrição |
| `upload` | arquivo | documento anexado |
| `multi_text` | vários textos | textos por subquestão |
| `array` | matriz | uma opção por linha |
| `array_numbers` | matriz numérica | valor numérico por célula |
| `adoption` | macro | escala, justificativa, detalhamento e evidência |

## 6. Diretivas

- `question:`: enunciado;
- `mandatory:`: `true` ou `false`;
- `help:`: instrução operacional;
- `explain:`: explicação exibida com o enunciado;
- `scale:`: escala declarada;
- `visible_if:`: condição de exibição;
- `other:`: habilita alternativa “Outro”;
- `subgroup:`: rótulo auxiliar;
- `evidence_text:`: cria upload associado;
- `evidence_if:`: condição explícita do upload;
- `target:`: restringe a pergunta a variantes do survey.

Atributos técnicos adicionais do LimeSurvey podem ser informados como diretivas e são preservados quando suportados pelo conversor.

## 7. Macro `adoption`

```markdown
### q0301 [adoption]
question: **A organização mantém processo de gestão de incidentes?**
mandatory: true
help: Considere o processo vigente na data-base.
evidence_text: Envie norma, fluxo, registros de incidentes ou relatório equivalente.

subquestions:
- A | há papéis e responsabilidades definidos
- B | os incidentes são registrados e classificados
- C | existem prazos de tratamento
- D | os resultados são monitorados
```

A macro gera:

- `q0301`: nível de adoção;
- `q0301nsa`: motivo de não aplicabilidade;
- `q0301lei`, `q0301est` ou `q0301raz`: justificativa específica;
- `q0301ext`: detalhamento, exibido para adoção parcial ou maior;
- `q0301evi`: upload obrigatório, exibido para adoção parcial ou maior.

É possível desligar componentes com `nsa: false`, `detail: false`, `lei: false`, `est: false` ou `raz: false`.

## 8. Condições `visible_if`

Formas aceitas:

```text
visible_if: q0101 == A
visible_if: q0101 in [A, B]
visible_if: q0101 != D
visible_if: q0201.A == Y
visible_if: q0201[A] == Y
visible_if: (q0101 == A and q0201 in [B, C]) or q0301.A == Y
```

Use `raw:` somente quando precisar fornecer uma expressão LimeSurvey completa e souber os IDs técnicos:

```text
visible_if: raw: ((900001X1000X10000.NAOK == "A"))
```

Prefira referências por código porque o conversor resolve SID, GID e QID.

## 9. Evidências

`evidence_text` cria uma pergunta de upload. Para perguntas comuns, use `evidence_if` quando a condição não puder ser inferida com segurança:

```markdown
evidence_if: q0101 in [A, B]
evidence_text: Envie o ato vigente que sustenta a resposta.
```

O padrão aceita um arquivo `pdf`, `docx` ou `zip`. Ajuste a descrição ao conteúdo realmente necessário e evite solicitar documentos integrais quando um extrato suficiente reduzir exposição de dados pessoais.

## 10. Targets

Targets geram versões destinadas a públicos diferentes:

```yaml
target: estadual, municipal
```

```markdown
### q1001 [single]
target: estadual
question: **Pergunta exclusiva das organizações estaduais.**
```

Perguntas sem `target` aparecem em todas as versões. O conversor falha quando uma condição referencia pergunta removida do target.
