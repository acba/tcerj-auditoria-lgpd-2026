---
name: elaborar-survey-limesurvey
description: Elabora, revisa, corrige, valida e converte questionários em Markdown SurveyMD para arquivos LSS importáveis no LimeSurvey e guias DOCX legíveis enviados aos respondentes com o link eletrônico. Use sempre que o usuário pedir para criar ou avaliar survey, questionário eletrônico ou formulário de auditoria; editar `.md`; gerar ou validar `.lss`; produzir DOCX/PDF auxiliar de preenchimento; ou conferir escalas de adoção, perguntas condicionais, uploads de evidência, grupos, tokens, clareza, neutralidade, obrigatoriedade, minimização de dados e rastreabilidade. Não use para responder um questionário como participante nem para operar uma instância remota do LimeSurvey sem autorização e credenciais.
compatibility: Python 3.10 ou superior. LSS usa somente biblioteca padrão; DOCX prefere Pandoc/pypandoc e usa python-docx como fallback.
---

# Elaborar e avaliar surveys do LimeSurvey

## Objetivo

Produzir questionários claros, proporcionais e tecnicamente importáveis no LimeSurvey, mantendo o Markdown SurveyMD como fonte canônica. A skill cobre criação, revisão de conteúdo, validação estrutural, geração do LSS e geração do guia DOCX que acompanha o link enviado aos respondentes.

Trate questionários e pareceres produzidos por IA como minutas. A equipe responsável deve aprovar conteúdo, critérios, dados pessoais coletados, lógica condicional e configuração final antes da publicação.

## Recursos autocontidos

- `scripts/survey_tool.py`: interface para revisar Markdown, gerar LSS/DOCX e validar os produtos;
- `scripts/surveymd_to_lss.py`: parser e gerador XML do LimeSurvey;
- `scripts/surveymd_to_docx.py`: renderizador do guia do respondente e conversor DOCX;
- `scripts/survey_utils.py`: front matter, targets e dependências condicionais;
- `references/surveymd-format.md`: gramática e exemplos do formato-fonte;
- `references/quality-review.md`: roteiro de avaliação metodológica, auditorial e de privacidade;
- `assets/survey-template.md`: ponto de partida editável;
- `assets/template-questionario.docx`: reference DOCX incorporado para o Pandoc;
- `assets/template-questionario-tcerj.docx`: template institucional versionado do TCE-RJ para o guia DOCX deste projeto;
- `evals/`: casos de avaliação da própria skill.

Os scripts não dependem do repositório do usuário, de PyYAML nem de pacotes do LimeSurvey. A geração DOCX segue preferencialmente a abordagem Pandoc com `reference-docx`; se Pandoc não estiver disponível, usa `python-docx` para produzir um documento funcional.

## Fluxo de trabalho

1. Identifique se a solicitação é criação, revisão, correção, validação ou geração do LSS.
2. Leia as instruções do repositório e o questionário existente antes de alterar qualquer arquivo.
3. Leia as fontes que sustentam objetivo, população, critérios, riscos, informações requeridas e evidências. Não invente requisitos ou conclusões.
4. Preserve códigos de grupos, perguntas, alternativas e subquestões existentes. Eles podem estar ligados a exportações, cálculos, evidências e séries históricas.
5. Use o Markdown como fonte canônica. Não edite o LSS gerado para implementar mudança permanente; corrija o Markdown e gere novamente.
6. Leia `references/surveymd-format.md` ao criar ou corrigir sintaxe, escalas, lógica condicional, targets, macro `adoption` ou uploads.
7. Leia `references/quality-review.md` ao elaborar ou avaliar conteúdo.
8. Execute a revisão automatizada. Corrija erros e examine conscientemente os avisos.
9. Gere conjuntamente o LSS e o guia DOCX do respondente e valide os dois produtos.
10. Confira se o DOCX não expõe diretivas técnicas, apresenta todas as perguntas aplicáveis e deixa claro que o envio ocorre no LimeSurvey.
11. Informe os arquivos alterados, resultado das validações e decisões que ainda exigem revisão humana.

Prefira intervenção mínima em questionários existentes. Reescreva somente o necessário para remover ambiguidade, corrigir lógica ou alinhar a pergunta ao objetivo da coleta.

## Elaboração do conteúdo

Antes de escrever perguntas, registre:

- finalidade da coleta e decisões que os dados apoiarão;
- população respondente e unidade de análise;
- período de referência;
- conceitos que precisam ser definidos;
- dados pessoais estritamente necessários;
- evidência esperada, quando a resposta precisar de comprovação;
- regra de análise ou cálculo que consumirá cada código.

Uma pergunta deve medir um conteúdo identificável. Separe enunciados com duas obrigações quando as respostas puderem divergir. Defina termos vagos como “periodicamente”, “adequado” ou “formalizado”. Evite indução, pressupostos não demonstrados e alternativas sobrepostas.

Em questionários de auditoria, diferencie:

- declaração do respondente;
- detalhamento confirmatório;
- documento ou registro comprobatório;
- avaliação posterior da equipe de auditoria.

Não apresente resposta autodeclarada como evidência conclusiva.

## Revisão

Avalie em quatro níveis:

1. **Finalidade e escopo** — cada pergunta contribui para o objetivo e se aplica à população indicada.
2. **Qualidade da mensuração** — enunciado, período, unidade de análise, alternativas, escalas e instruções são claros e neutros.
3. **Lógica e rastreabilidade** — códigos são estáveis; obrigatoriedade, `visible_if`, evidências, targets e dependências estão coerentes.
4. **Privacidade e operação** — há minimização de dados, orientação para anexos, base institucional adequada e plano de teste no LimeSurvey.

Ao concluir uma revisão, classifique observações como:

- `erro`: impede interpretação confiável, conversão ou navegação;
- `aviso`: exige decisão consciente, mas pode ser aceitável;
- `melhoria`: aumenta clareza ou eficiência sem corrigir defeito material.

## Formato-fonte

Use `.md` como extensão padrão e UTF-8. Comece a partir de `assets/survey-template.md` quando não houver fonte existente.

O formato aceita questões `single`, `multi`, `short`, `long`, `upload`, `multi_text`, `array`, `array_numbers` e a macro `adoption`. Consulte `references/surveymd-format.md` para a sintaxe completa.

## Comandos

Resolva `<skill-dir>` como o diretório que contém este `SKILL.md`.

Revisar o Markdown:

```bash
python <skill-dir>/scripts/survey_tool.py review questionario.md
```

Obter resultado estruturado:

```bash
python <skill-dir>/scripts/survey_tool.py review questionario.md --json
```

Gerar e validar o LSS:

```bash
python <skill-dir>/scripts/survey_tool.py build questionario.md questionario.lss
```

Gerar somente o guia DOCX destinado aos respondentes:

```bash
python <skill-dir>/scripts/survey_tool.py build-docx questionario.md questionario.docx
```

Gerar o pacote recomendado — LSS e DOCX com o mesmo nome-base:

```bash
python <skill-dir>/scripts/survey_tool.py build-all questionario.md saida/questionario
```

O comando `build-all` produz `saida/questionario.lss` e `saida/questionario.docx`. O DOCX usa automaticamente o template interno e prefere pypandoc/Pandoc, como o conversor de Markdown usado nos projetos Argos.

Para forçar ou diagnosticar o mecanismo:

```bash
python <skill-dir>/scripts/survey_tool.py build-docx questionario.md questionario.docx --engine pandoc
python <skill-dir>/scripts/survey_tool.py build-docx questionario.md questionario.docx --engine python-docx
```

Tratar avisos como bloqueantes:

```bash
python <skill-dir>/scripts/survey_tool.py build questionario.md questionario.lss --strict
```

Validar um LSS existente:

```bash
python <skill-dir>/scripts/survey_tool.py validate-lss questionario.lss
```

Quando o front matter declarar mais de um `target`, os comandos `build` e `build-all` geram um conjunto por target, acrescentando o nome ao arquivo de saída.

## Guia DOCX para o respondente

O guia acompanha o link do LimeSurvey, mas não substitui o formulário eletrônico. Gere-o a partir do mesmo Markdown e na mesma execução do LSS para impedir divergências.

O documento apresenta:

- finalidade e orientações gerais;
- grupos e descrições;
- perguntas e obrigatoriedade;
- alternativas, subitens e campos esperados;
- condições de exibição traduzidas para linguagem humana;
- formatos e limites dos anexos;
- aviso de que o preenchimento e o envio ocorrem no LimeSurvey.

O guia omite diretivas técnicas como `mandatory:`, `visible_if:` e `evidence_text:`. Use `--show-logic` somente para uma versão interna de revisão, nunca como padrão do documento enviado aos auditados.

## Critérios de conclusão

Considere a tarefa tecnicamente concluída quando:

- o Markdown é a fonte do conteúdo e permanece legível;
- a revisão automatizada não apresenta erros;
- avisos foram corrigidos ou justificados;
- o LSS foi gerado e validado;
- o DOCX foi gerado da mesma fonte, abre como pacote válido e não expõe diretivas técnicas;
- códigos e dependências foram preservados ou a mudança foi explicitada;
- dados pessoais e uploads passaram por revisão humana;
- ficou registrado que importação, ativação, tokens, convites, permissões e teste de navegação são etapas da instância do LimeSurvey.

## Entrega

Informe:

- fonte Markdown criada ou alterada;
- LSS e DOCX gerados;
- quantidade de grupos e perguntas;
- erros, avisos e melhorias relevantes;
- limitações da validação local;
- pendências para teste e publicação no LimeSurvey.
