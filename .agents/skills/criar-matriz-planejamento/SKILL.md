---
name: criar-matriz-planejamento
description: Elabora, revisa, melhora, valida e gera matrizes de planejamento de auditoria governamental em Markdown/texto estruturado e DOCX. Use quando o usuário estiver criando ou alterando questões de auditoria, subquestões, riscos, fontes de informação, informações requeridas, critérios, procedimentos, evidências, possíveis achados ou a rastreabilidade entre esses elementos; quando precisar distinguir questões normativas de questões descritivas/levantamentos; ou quando quiser produzir `matriz_planejamento.md` e `matriz_planejamento.docx`. A skill é autocontida: possui parser, validador, gerador DOCX e template próprios. Não use apenas porque o usuário menciona auditoria, achados, recomendações ou normas fora do contexto de uma matriz de planejamento.
---

# Preencher Matriz de Planejamento

## Objetivo

Criar e manter matrizes de planejamento de auditoria governamental que sejam claras, executáveis, específicas e rastreáveis, sem antecipar conclusões da fase de execução.

A matriz deve permitir responder, para cada questão: **o que será avaliado, por que importa, de onde virá a informação, qual informação é necessária, qual padrão será aplicado, qual teste será executado, qual evidência será obtida e qual possível achado poderá resultar**.

Use esta skill para auditorias de conformidade, operacionais, financeiras, de governança, de TI, fiscalizações, inspeções, monitoramentos e levantamentos. Preserve convenções locais válidas quando existirem, mas não dependa de scripts, módulos ou templates externos para funcionar.

## Recursos autocontidos

A skill inclui:

- `scripts/matrix_engine.py`: parser e motor OpenXML da matriz;
- `scripts/validate_matrix.py`: validação estrutural, de rastreabilidade e heurísticas de qualidade;
- `scripts/build_matrix.py`: valida e gera o DOCX final;
- `assets/matriz_planejamento_template.docx`: template padrão;
- `references/`: modelo, critérios de qualidade, exemplos e instruções de geração.

## Fluxo de trabalho

1. Identifique se a tarefa é **criação**, **revisão**, **melhoria**, **validação** ou **geração do DOCX**.
2. Leia a matriz existente, se houver, antes de alterá-la.
3. Leia os documentos que definem objetivo, escopo, objeto, questionário, bases de dados, metodologia e critérios citados pelo usuário.
4. Classifique cada questão como **normativa/avaliativa** ou **descritiva/levantamento**.
5. Estruture ou revise a cadeia lógica da questão.
6. Faça revisão em três níveis: estrutural, semântico e metodológico.
7. Execute `scripts/validate_matrix.py` após mudanças relevantes.
8. Corrija todos os erros e examine conscientemente os avisos.
9. Quando solicitado, gere o DOCX com `scripts/build_matrix.py`.
10. Confirme que o DOCX foi criado e contém todas as questões esperadas.

Ao revisar uma matriz existente, aplique intervenção mínima: preserve conteúdo válido e IDs estáveis; não reescreva por preferência estilística; atualize referências dependentes quando mover, dividir, excluir ou renumerar itens.

## Tipos de questão

### Questão normativa ou avaliativa

Use quando a auditoria pretende avaliar uma condição à luz de um padrão esperado: conformidade, controles, governança, desempenho, economicidade, eficiência, eficácia ou outro requisito verificável.

Uma questão normativa deve conter, no mínimo:

`questão -> subquestões -> riscos -> fontes -> informações requeridas -> critérios -> procedimentos -> evidências -> possíveis achados/situações`

Regras obrigatórias:

- deve possuir critérios de auditoria específicos;
- deve prever pelo menos um possível achado/situação, como hipótese de auditoria;
- cada situação deve ser rastreável a risco, procedimento, evidência e critério;
- o possível achado não é conclusão: somente se confirma após a execução dos procedimentos.

Se uma questão misturar partes puramente descritivas com avaliação normativa e isso prejudicar a clareza, divida-a.

### Questão descritiva ou levantamento

Use quando a finalidade é descrever, mapear, comparar, quantificar, caracterizar, identificar causas, perfis, distribuição, evolução ou maturidade sem concluir desconformidade individual.

Declare:

```yaml
natureza: levantamento
gera_achado: false
```

Uma questão de levantamento:

- não precisa de critérios de auditoria;
- não precisa de riscos de achado;
- não deve conter possíveis achados de desconformidade;
- deve possuir fontes, informações requeridas, procedimentos e evidências/saídas analíticas suficientes;
- deve preferir `o_que_a_analise_permite_dizer` e `limitacoes_e_cautelas`.

Critérios ou referências metodológicas podem ser usados para cálculo, classificação ou comparabilidade, mas não transformam a questão em normativa por si só.

## Fontes de informação

Trate fonte como **origem da informação**, não como o documento produzido.

Boas fontes:

- gestores ou responsáveis pelo processo;
- unidade administrativa, secretaria, órgão ou entidade;
- sistema corporativo ou aplicação específica;
- base de dados institucional;
- processo administrativo ou repositório oficial;
- portal institucional;
- fornecedor, operador ou terceiro responsável pela informação.

Evite:

- `F1: Respostas ao questionário.`
- `F2: Documentos anexados.`
- `F3: Relatórios.`

Prefira:

- `F1: Gestores responsáveis pelo processo X.`
- `F2: Unidade responsável pelo controle X.`
- `F3: Sistema corporativo X.`

O conteúdo necessário pertence a `informacoes_requeridas`; o elemento comprobatório pertence a `evidencias`.

## Informações requeridas

Descreva **o que a equipe precisa saber** para responder às subquestões, sem antecipar o teste.

Toda `IR#` deve apontar pelo menos uma `F#`.

Exemplo:

`IR2: ato de designação vigente, autoridade signatária, data de publicação e período de vigência; [F1, F3]`

## Critérios de auditoria

Leia `references/criteria-and-procedures.md` ao criar ou revisar critérios.

Para questão normativa, não aceite como critério apenas o nome de uma norma, lei, framework, manual, acórdão ou referência técnica.

O critério deve indicar **qual dispositivo será aplicado e qual requisito será testado**, por exemplo:

- lei/decreto/regulamento: artigo, parágrafo, inciso ou alínea;
- decisão/acórdão/deliberação: item ou subitem;
- ISO/ABNT: cláusula, controle, requisito ou anexo aplicável;
- COBIT: objetivo/prática específica, como `APO01.05`;
- NIST: função/categoria/subcategoria aplicável;
- manual/metodologia: item, seção ou requisito determinado.

Prefira um critério por obrigação testável. Se dispositivos diferentes estabelecem requisitos distintos, desdobre-os em critérios separados.

Não invente artigo, item, cláusula ou prática. Quando o dispositivo exato não estiver disponível nos arquivos fornecidos, localize a fonte oficial quando permitido. Se não puder confirmar, marque a referência como pendente de validação em vez de fabricar precisão.

## Procedimentos de auditoria

Leia `references/criteria-and-procedures.md` ao elaborar procedimentos.

Procedimentos devem ser específicos e executáveis. Indique, conforme aplicável:

- objeto/documento/registro/população/amostra a examinar;
- ação: analisar, confrontar, recalcular, entrevistar, inspecionar, confirmar, observar, selecionar amostra etc.;
- atributos ou condições a verificar;
- universo, amostra, período ou regra de seleção;
- informação requerida atendida.

Evite:

- `avaliar a governança`;
- `verificar a conformidade`;
- `analisar os documentos`.

Prefira:

`P2: Examinar o ato de aprovação e a versão vigente da política para confirmar autoridade aprovadora, data de vigência, escopo institucional, responsabilidades mínimas e periodicidade de revisão; [IR2]`

Quando a questão for normativa e houver possibilidade de comprovação objetiva, não dependa apenas de resposta declaratória: combine-a com documento, registro de sistema, inspeção, recálculo, confronto ou amostra.

## Evidências

Descreva o elemento observável que poderá confirmar ou refutar a hipótese planejada.

Toda `E#` deve apontar pelo menos um `P#`.

Exemplos:

- ato formal vigente e publicado;
- registro extraído de sistema;
- amostra de processos e resultados do teste;
- logs, contratos, atas, planos, políticas, relatórios ou trilhas de auditoria;
- resultado de recálculo ou confronto entre bases.

Não confunda evidência com conclusão.

## Possíveis achados e rastreabilidade

Use possíveis achados como **hipóteses de deficiência**. Prefira poucos achados estruturantes com situações objetivas quando várias manifestações derivarem do mesmo problema.

Para cada situação de questão normativa, exija ao menos:

- `R#`: risco relacionado;
- `P#`: procedimento que testa a condição;
- `E#`: evidência que resulta do procedimento;
- `C#`: critério específico aplicável.

A cadeia deve poder ser percorrida nos dois sentidos:

`Situação -> Critério + Evidência -> Procedimento -> Informação requerida -> Fonte`

E também:

`Fonte -> Informação requerida -> Procedimento -> Evidência -> Situação/Achado`

Campos como `severidade`, `regra_de_identificacao`, `tipo_encaminhamento`, `fundamentacao_encaminhamento`, `encaminhamento` e `variantes` são extensões opcionais. Preserve-os quando o projeto os utilizar, mas não os imponha a toda matriz governamental.

## Revisão de qualidade

Leia `references/quality-review.md` para a revisão completa.

Revise em três níveis:

1. **Estrutural** — sintaxe, IDs, campos, duplicidades e referências existentes.
2. **Semântico** — coerência entre questão, subquestões, riscos, fontes, informações, critérios, procedimentos, evidências e possíveis achados.
3. **Metodológico** — adequação do tipo de questão, especificidade do critério, executabilidade do procedimento, suficiência da evidência e capacidade da matriz de responder ao objetivo.

A validação automatizada não substitui a revisão semântica do auditor.

## Formato-fonte

O formato canônico é Markdown/texto estruturado e pode usar extensão `.txt` ou `.md`.

Leia `references/matrix-model.md` antes de criar uma matriz do zero.

Quando não houver nome definido, use `matriz_planejamento.md`.

## Validação automatizada

Execute:

```bash
python scripts/validate_matrix.py matriz_planejamento.md
```

Use `--json` para saída estruturada e `--strict` quando quiser tratar qualquer aviso como bloqueante.

Erros são bloqueantes. Avisos exigem revisão consciente.

O validador verifica, entre outros pontos:

- referências inexistentes;
- `IR` sem `F`, `P` sem `IR`, `E` sem `P`;
- questão normativa sem critério ou sem possível achado;
- situação sem `R/P/E/C`;
- questão de levantamento com achado;
- critérios genéricos ou ISO/COBIT sem item específico;
- fontes descritas como produto informacional;
- procedimentos genéricos;
- elementos órfãos na cadeia de rastreabilidade.

## Geração do DOCX

Leia `references/docx-generation.md` quando o usuário pedir o documento final.

Fluxo padrão:

```bash
python scripts/build_matrix.py matriz_planejamento.md
```

Por padrão, o script:

1. usa o parser da própria skill;
2. valida a matriz;
3. usa o template interno `assets/matriz_planejamento_template.docx`;
4. lê do front matter `fiscalizacao`, `jurisdicionados` e `objetivo_auditoria`;
5. gera `matriz_planejamento.docx` ao lado da matriz.

Não depende de `gerar_matriz_planejamento.py`, `build_matrix.py`, template ou módulo do repositório do usuário.

## Saída ao concluir

Informe de forma concisa:

- o que foi criado ou alterado;
- inconsistências corrigidas;
- pontos que ainda dependem de decisão ou fonte do auditor;
- resultado da validação;
- caminho de `matriz_planejamento.md` e do DOCX, quando gerados.
