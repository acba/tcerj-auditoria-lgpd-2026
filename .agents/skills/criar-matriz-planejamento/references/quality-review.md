# Revisão de qualidade

## 1. Estrutura

- Questão geral está alinhada ao objetivo?
- IDs são únicos e estáveis?
- Toda IR referencia F?
- Todo P referencia IR?
- Toda E referencia P?
- Referências existem na mesma questão?
- Questão normativa possui critérios e possíveis achados?
- Questão de levantamento está marcada com `natureza: levantamento` e `gera_achado: false`?
- Questão de levantamento não contém achado de desconformidade?

## 2. Coerência semântica

- Cada subquestão é respondida por informações e procedimentos suficientes?
- Os riscos correspondem ao objeto realmente avaliado?
- As fontes são origens reais da informação?
- As informações requeridas não confundem dado com procedimento?
- Os procedimentos produzem as evidências descritas?
- As evidências permitem confirmar ou refutar as situações previstas?
- Cada possível achado é materialização plausível de um risco?
- Não existem critérios, procedimentos ou evidências órfãos?

## 3. Critérios

- Cada critério aponta dispositivo específico?
- O texto explica o requisito testável?
- Normas técnicas apontam cláusula/controle/item?
- COBIT aponta objetivo/prática?
- Decisões apontam item/subitem?
- Obrigações distintas estão separadas?
- A referência foi confirmada e não inferida?

## 4. Procedimentos

- O verbo descreve ação de auditoria?
- O objeto está explícito?
- Os atributos a testar estão explícitos?
- Universo, amostra e período estão definidos quando necessários?
- A técnica é suficiente para a força da conclusão pretendida?
- Há confirmação documental/sistêmica/amostral quando resposta declaratória é insuficiente?

## 5. Possíveis achados

Para cada situação normativa, percorra:

`S -> R -> P -> E -> C`

E confirme também:

`P -> IR -> F`

A descrição da situação deve ser uma condição observável, não causa, efeito, opinião ou encaminhamento.

## 6. Levantamentos

- O produto analítico responde à pergunta?
- As limitações de comparabilidade e qualidade dos dados estão registradas?
- Não há linguagem de desconformidade sem critério?
- Critérios metodológicos, se houver, são usados para cálculo/classificação, não para criar achado automaticamente?
