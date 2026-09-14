---
title: "METODOLOGIA DE CÁLCULO DO iLGPD 2026"
lang: pt-BR
figure-caption-position: above
---

# 1. Introdução

Este relatório apresenta a metodologia de cálculo do Índice de Conformidade e Maturidade em Proteção de Dados Pessoais — iLGPD 2026, aplicado às 91 prefeituras municipais jurisdicionadas ao Tribunal de Contas do Estado do Rio de Janeiro (TCE-RJ). O índice integra a Fiscalização TCE-RJ nº 22/2026 e sintetiza, em escala de zero a um, as respostas autodeclaradas ao questionário de conformidade com a Lei Federal nº 13.709/2018 — Lei Geral de Proteção de Dados Pessoais (LGPD).

A metodologia preserva a estrutura aplicada na fiscalização de 2024. Essa continuidade permite comparar os resultados dos dois ciclos, pois mantém as perguntas pontuadas, as regras de conversão das respostas, as nove dimensões, os pesos, os intervalos de maturidade e o método de classificação.

O arquivo `estrutura-ilgpd-2026.yaml` é a fonte estruturada da metodologia. O programa `98-scripts/calcula_ilgpd.py` interpreta esse arquivo, valida as respostas, calcula os indicadores e registra a memória de cálculo. A separação entre regras e código reduz o risco de que alterações futuras sejam introduzidas de maneira implícita.

# 2. Objetivo e natureza do índice

O iLGPD tem quatro finalidades principais:

1. sintetizar as respostas municipais sobre práticas selecionadas de proteção de dados pessoais;
2. permitir a classificação das prefeituras por faixa de maturidade;
3. apoiar diagnósticos consolidados e comparações entre 2024 e 2026; e
4. oferecer um indicador reproduzível para subsidiar as análises da fiscalização.

O índice é diagnóstico. Ele não substitui a aplicação dos critérios jurídicos e dos procedimentos específicos previstos na matriz de planejamento. Uma mesma pontuação pode resultar de combinações diferentes de capacidades e deficiências, motivo pelo qual o valor agregado deve ser interpretado em conjunto com as dimensões e as respostas que o compõem.

## 2.1. Unidade de análise

Cada linha de entrada representa uma resposta institucional de uma prefeitura municipal. Quando houver mais de um envio para o mesmo identificador, a calculadora mantém o envio mais recente, conforme `submitdate`, `datestamp` ou `startdate`, salvo se a deduplicação for expressamente desativada.

## 2.2. Cenário calculado

A metodologia oficial de 2026 adota o cenário autodeclarado. Os documentos anexados, comentários e resultados de procedimentos de auditoria não alteram automaticamente a pontuação. Eventuais cenários ajustados somente deverão ser produzidos mediante metodologia própria, identificada separadamente, para que não sejam confundidos com o resultado autodeclarado.

# 3. Fontes e continuidade metodológica

A metodologia foi consolidada a partir dos seguintes insumos locais:

- questionário eletrônico LGPD 2026: `02-Execução/01-Questionário/questionario_lgpd_2026.md`;
- notebook de referência do cálculo de 2024: `00-Estudos_Preliminares/00-Antecedentes/LGPD 2024/99-Scripts/01-processa_dados/02-calcula_ilgpd.ipynb`;
- planilha bruta de respostas codificadas de 2024; e
- resultados históricos do iLGPD sem ajustes.

As perguntas e subquestões usadas no cálculo mantiveram seus códigos no questionário de 2026. Perguntas acrescentadas para monitoramento das decisões do TCE-RJ, contratações de apoio, avaliação do guia “Os 6 passos para adequação à LGPD”, detalhamentos e uploads não integram o iLGPD. Essa exclusão evita alterar a escala histórica apenas porque o instrumento de coleta passou a abranger novos objetivos da fiscalização.

: Síntese da continuidade metodológica

| Elemento | Regra de 2026 |
|---|---|
| Perguntas pontuadas | Mesmos códigos centrais utilizados em 2024 |
| Conversão das respostas | Mesmas escalas numéricas |
| Dimensões | Nove dimensões, de `iPrep` a `iProt` |
| Pesos | Mesmos pesos do cálculo de 2024 |
| Faixas de maturidade | Inexpressivo, Iniciando, Intermediário e Aprimorado |
| Evidências e comentários | Não alteram o cenário autodeclarado |
| Perguntas novas de 2026 | Excluídas do índice |

<div custom-style="FonteImagem">(Fonte: elaboração própria a partir da metodologia de 2024)</div>

# 4. Dados de entrada e controles de qualidade

## 4.1. Formatos aceitos

A calculadora aceita exportações codificadas do LimeSurvey nos formatos CSV e XLSX. No caso de XLSX, é lida a primeira planilha do arquivo. As respostas devem ser exportadas por código, como `A5`, `A3` e `Y`, e não apenas pelos rótulos extensos apresentados aos respondentes.

A identificação da prefeitura é procurada, nessa ordem, nas colunas `firstname`, `attribute_1`, `municipio`, `município`, `orgao`, `órgão`, `auditado`, `entidade` e `id`. Outra coluna pode ser indicada pelo parâmetro `--coluna-id`.

## 4.2. Respostas concluídas e duplicidades

Quando a coluna `submitdate` estiver presente, registros sem data de submissão são considerados incompletos e excluídos. Essa regra pode ser suspensa com `--incluir-incompletas`. Se houver respostas duplicadas para uma prefeitura, prevalece o envio mais recente. A quantidade de registros lidos, incompletos excluídos, duplicados excluídos e efetivamente processados é registrada no resumo da execução.

## 4.3. Ausência e códigos inválidos

As perguntas de escala que alimentam diretamente o índice são obrigatórias. Por padrão, a ausência de resposta ou a presença de código desconhecido interrompe o cálculo. Essa escolha evita que falha de coleta seja confundida com não adoção.

O modo alternativo `--modo-ausentes zero` permite atribuir zero a resposta de escala ausente, registrando aviso. Esse modo deve ser utilizado somente mediante decisão metodológica documentada.

Nas questões de múltipla escolha, a ausência de marcação de um subitem corresponde a zero. Os códigos `Y`, `1` e equivalentes representam subitem marcado. A opção exclusiva “ainda não atende a nenhum dos itens” faz a dimensão receber zero. Se ela aparecer simultaneamente com alguma opção positiva, a execução é interrompida, pois o registro é logicamente contraditório.

# 5. Conversão das respostas categóricas

As respostas de seleção única são transformadas em valores entre zero e um. Valores maiores representam estágios mais avançados da prática examinada.

## 5.1. Preparação institucional — Q21

| Código | Valor |
|---|---:|
| `A1` — não se aplica | 0,00 |
| `A2` | 0,00 |
| `A3` | 0,10 |
| `A4` | 0,24 |
| `A5` | 0,42 |
| `A6` | 0,67 |
| `A7` | 1,00 |

O notebook histórico não explicitava o tratamento de `A1` em Q21. Para 2026, o YAML registra `A1 = 0`, em coerência com o tratamento dado às demais respostas “não se aplica” nas escalas originais. A decisão é agora expressa e auditável.

## 5.2. Capacitação — Q51

| Código | Valor |
|---|---:|
| `A1` ou `A2` | 0,00 |
| `A3` | 0,15 |
| `A4` | 0,35 |
| `A5` | 0,63 |
| `A6` | 1,00 |

## 5.3. Política de Privacidade e direitos dos titulares — Q71 e Q72

| Código | Valor |
|---|---:|
| `A1` ou `A2` | 0,00 |
| `A3` | 0,43 |
| `A4` | 1,00 |

## 5.4. Compartilhamento de dados pessoais — Q81

| Código | Valor |
|---|---:|
| `A1` ou `A2` | 0,00 |
| `A3` | 0,15 |
| `A4` | 0,35 |
| `A5` | 0,63 |
| `A6` | 1,00 |

# 6. Cálculo das dimensões

O iLGPD é composto por nove dimensões. Sete delas são obtidas diretamente de uma escala ou da média dos subitens binários. A dimensão de direitos dos titulares combina duas questões. Todas variam de zero a um.

: Dimensões do iLGPD 2026

| Dimensão | Tema | Origem | Regra |
|---|---|---|---|
| `iPrep` | Preparação institucional | Q21 | Escala categórica |
| `iOrg` | Contexto organizacional | Q31 | Média de oito subitens |
| `iLid` | Liderança e políticas | Q41 | Média de cinco subitens |
| `iCap` | Capacitação | Q51 | Escala categórica |
| `iConf` | Conformidade do tratamento | Q61 | Média de nove subitens |
| `iDir` | Direitos dos titulares | Q71 e Q72 | Média ponderada |
| `iComp` | Compartilhamento | Q81 | Escala categórica |
| `iResp` | Resposta a incidentes | Q91 | Média de cinco subitens |
| `iProt` | Medidas de proteção | Q101 | Média de oito subitens |

<div custom-style="FonteImagem">(Fonte: elaboração própria a partir da metodologia de 2024)</div>

## 6.1. Dimensões binárias

Para uma dimensão formada por `n` subitens positivos:

```text
dimensao = quantidade de subitens marcados / n
```

Se a opção exclusiva negativa for marcada, a dimensão recebe zero. Os denominadores são fixos: oito em `iOrg`, cinco em `iLid`, nove em `iConf`, cinco em `iResp` e oito em `iProt`.

Exemplo: se uma prefeitura marcar seis dos oito controles de Q101, `iProt = 6 / 8 = 0,75`.

## 6.2. Direitos dos titulares

A dimensão `iDir` atribui peso de 40% à Política de Privacidade e 60% aos mecanismos de atendimento dos direitos dos titulares:

```text
iDir = (Q71_score * 0,4) + (Q72_score * 0,6)
```

# 7. Fórmula final e pesos

As nove dimensões são combinadas por média ponderada. Os pesos originais somam 15.

: Pesos das dimensões no iLGPD

| Dimensão | Peso original | Participação no índice |
|---|---:|---:|
| `iPrep` | 1,0 | 6,67% |
| `iOrg` | 1,0 | 6,67% |
| `iLid` | 2,0 | 13,33% |
| `iCap` | 1,5 | 10,00% |
| `iConf` | 2,0 | 13,33% |
| `iDir` | 2,0 | 13,33% |
| `iComp` | 2,0 | 13,33% |
| `iResp` | 1,5 | 10,00% |
| `iProt` | 2,0 | 13,33% |
| **Total** | **15,0** | **100,00%** |

<div custom-style="FonteImagem">(Fonte: elaboração própria a partir da metodologia de 2024)</div>

A fórmula é:

```text
iLGPD = (
    iPrep
  + iOrg
  + 2,0 * iLid
  + 1,5 * iCap
  + 2,0 * iConf
  + 2,0 * iDir
  + 2,0 * iComp
  + 1,5 * iResp
  + 2,0 * iProt
) / 15
```

Como todas as dimensões estão no intervalo de zero a um e os pesos são positivos, o resultado final também pertence ao intervalo `[0, 1]`.

## 7.1. Exemplo ilustrativo

Considere uma prefeitura com os seguintes valores: `iPrep = 0,42`, `iOrg = 0,50`, `iLid = 0,80`, `iCap = 0,35`, `iConf = 0,60`, `iDir = 0,70`, `iComp = 0,35`, `iResp = 0,40` e `iProt = 0,50`.

```text
iLGPD = 7,945 / 15 = 0,529667
```

O resultado situa a prefeitura no nível `Intermediário`.

# 8. Classificação da maturidade

| Nível | Intervalo |
|---|---|
| `Inexpressivo` | `0 <= iLGPD < 0,15` |
| `Iniciando` | `0,15 <= iLGPD < 0,40` |
| `Intermediário` | `0,40 <= iLGPD < 0,70` |
| `Aprimorado` | `0,70 <= iLGPD <= 1,00` |

Os limites inferiores pertencem à nova faixa. Assim, o valor exato `0,15` é classificado como `Iniciando`, `0,40` como `Intermediário` e `0,70` como `Aprimorado`.

# 9. Ranking

As prefeituras são ordenadas do maior para o menor iLGPD. O ranking é denso: resultados empatados recebem a mesma posição e a posição seguinte é consecutiva. Por exemplo, pontuações que produzam as posições `1, 1, 2` permanecem dessa forma, sem salto para a posição 3.

O ranking é uma ordenação descritiva. Diferenças pequenas de posição não devem ser interpretadas isoladamente como diferenças substantivas de capacidade institucional.

# 10. Execução da calculadora

## 10.1. Validar a estrutura

```bash
python 98-scripts/calcula_ilgpd.py --validar-config
```

## 10.2. Calcular a partir de CSV

```bash
python 98-scripts/calcula_ilgpd.py caminho/para/respostas_codificadas.csv
```

## 10.3. Calcular a partir de XLSX

```bash
python 98-scripts/calcula_ilgpd.py caminho/para/respostas_codificadas.xlsx
```

Por padrão, os arquivos são gravados em `02-Execução/02-iLGPD`. Outra pasta pode ser informada com `--saida-dir`. O programa requer Python 3.10 ou superior e PyYAML.

# 11. Produtos gerados

| Arquivo | Conteúdo |
|---|---|
| `resultados_ilgpd_2026.csv` | Identificador, nove dimensões, iLGPD, maturidade, ranking e linha de origem |
| `memoria_calculo_ilgpd_2026.json` | Códigos recebidos, valores normalizados, componentes, pesos e contribuições por prefeitura |
| `resumo_execucao_ilgpd_2026.json` | Hashes dos insumos, contagens, estatísticas descritivas, distribuição da maturidade e arquivos produzidos |
| `diagnosticos_ilgpd_2026.csv` | Avisos de processamento, como ausência de coluna de conclusão ou imputação por zero |

A memória de cálculo não replica campos livres, contatos ou documentos anexados. Ela registra somente o identificador institucional e os elementos necessários à reprodução da pontuação.

# 12. Rastreabilidade e reprodutibilidade

Cada execução registra o hash SHA-256 do arquivo de respostas e do YAML metodológico. Com isso, é possível identificar exatamente quais versões deram origem aos resultados. Alterações de escala, componentes, pesos ou faixas devem resultar em nova versão do YAML e em nova execução integral da calculadora.

O script valida:

- presença das colunas necessárias;
- existência de todos os códigos de escala;
- coerência das opções exclusivas;
- positividade dos pesos;
- existência dos componentes da árvore;
- ausência de ciclos entre agregados; e
- cobertura integral do intervalo de maturidade entre zero e um.

## 12.1. Teste de regressão com 2024

A implementação foi testada com as 91 respostas brutas codificadas da fiscalização de 2024. Foram comparados `iPrep`, `iOrg`, `iLid`, `iCap`, `iConf`, `iDir`, `iComp`, `iResp`, `iProt` e `iLGPD` com o arquivo histórico `resultado_ilgpd_sem_ajustes.xlsx`.

Não foi encontrada divergência superior a `0,0000005` em nenhuma das 910 comparações realizadas. O teste confirma que a nova calculadora reproduz a implementação do notebook de referência para os dados efetivamente observados em 2024.

# 13. Limitações e cautelas de interpretação

1. O cenário oficial utiliza autodeclarações institucionais. O índice mede o estado informado pela prefeitura, conforme a premissa metodológica adotada pela fiscalização.
2. Os pesos foram herdados da metodologia de 2024 e representam uma escolha de agregação, não uma estimativa estatística da importância causal de cada dimensão.
3. A média de subitens permite compensação interna: a ausência de um controle pode ser compensada numericamente pela presença de outro. Isso não afasta eventual desconformidade específica.
4. A comparação longitudinal pressupõe preservação dos códigos e significado material das perguntas pontuadas. Mudanças futuras devem ser submetidas a análise de comparabilidade.
5. A categoria “não se aplica” recebe zero nas escalas históricas do iLGPD. Esse tratamento deve ser considerado ao interpretar casos em que a não aplicabilidade seja juridicamente válida.
6. O ranking não incorpora margem de erro e não deve ser usado isoladamente para concluir superioridade substantiva entre prefeituras com resultados próximos.

# 14. Conclusão

A metodologia de 2026 torna explícitas, em um arquivo estruturado e versionável, as regras anteriormente concentradas em um notebook. A calculadora associada valida os insumos, reproduz a fórmula histórica, registra diagnósticos e produz memória de cálculo por prefeitura. Esse desenho permite calcular o iLGPD 2026 de forma transparente, repetível e comparável com o ciclo de 2024, preservadas as limitações inerentes à autodeclaração e à agregação sintética de controles distintos.
