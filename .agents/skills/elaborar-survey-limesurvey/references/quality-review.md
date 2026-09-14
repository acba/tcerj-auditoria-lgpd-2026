# Avaliação de qualidade do survey

## 1. Finalidade e governança

- O objetivo da coleta está escrito e vinculado a uma decisão, análise ou procedimento?
- A população e a unidade de análise estão definidas?
- O período de referência aparece quando respostas podem variar no tempo?
- Está claro quem pode responder e se é necessário consultar outras unidades?
- Cada dado solicitado possui uso previsto?

## 2. Enunciados

- A pergunta mede um assunto por vez?
- Termos técnicos, siglas e expressões vagas estão definidos?
- A redação evita induzir concordância, culpa ou desejabilidade social?
- A pergunta não pressupõe um fato que pode não existir?
- A negação é necessária e está fácil de interpretar?
- O respondente consegue responder com informação disponível?

Divida perguntas duplas. “A organização aprovou e revisa anualmente a política?” deve virar duas medições se aprovação e revisão puderem divergir.

## 3. Alternativas e escalas

- As alternativas são mutuamente exclusivas quando a pergunta aceita apenas uma?
- O conjunto é suficientemente exaustivo?
- “Não sabe”, “não se aplica” e “outro” são oferecidos somente quando metodologicamente adequados?
- Os rótulos mantêm ordem, direção e distância conceitual coerentes?
- A escala não combina frequência, qualidade e concordância no mesmo eixo?
- Códigos das alternativas permanecem estáveis e separados do texto apresentado?

Não atribua valor numérico sem documentar o significado metodológico. Não trate “não se aplica” como ausência neutra por padrão.

## 4. Obrigatoriedade e navegação

- A obrigatoriedade é necessária para análise ou apenas conveniente?
- Perguntas condicionais aparecem somente depois da resposta da qual dependem?
- Todos os caminhos permitem concluir o survey?
- Há rota adequada para inexistência, desconhecimento e não aplicabilidade?
- Condições compostas foram testadas com respostas de fronteira?
- Targets não deixam dependências quebradas?

## 5. Evidência em auditoria

- O pedido especifica documento, registro, data-base, vigência e atributo verificável?
- A evidência é proporcional ao risco e à afirmação?
- Respostas positivas críticas possuem confirmação suficiente?
- Upload não é solicitado quando a informação pode ser verificada em fonte oficial mais segura?
- O texto explica formatos, quantidade e tamanho permitidos?
- O fluxo separa autodeclaração, evidência e conclusão da equipe?

Não conclua conformidade apenas porque houve upload. A evidência precisa ser examinada quanto a autenticidade, pertinência, vigência e suficiência.

## 6. Privacidade e proteção de dados

- A finalidade e a necessidade de cada dado pessoal foram analisadas?
- É possível coletar categoria, faixa ou indicador em vez de dado individual?
- Campos livres e anexos alertam contra envio de dados pessoais desnecessários?
- Dados sensíveis, sigilosos ou de crianças/adolescentes recebem tratamento específico?
- Acesso, retenção, exportação e descarte têm responsáveis definidos?
- Texto de abertura informa finalidade, responsável e canal de contato?
- Configuração de anonimização, tokens e persistência é coerente com a finalidade?

A skill não determina base legal nem substitui análise jurídica ou do encarregado. Registre como pendência aquilo que não puder ser confirmado.

## 7. Operação no LimeSurvey

Depois da validação local:

1. importe o LSS em ambiente de teste;
2. confira tema, idioma, textos e e-mails;
3. percorra todos os ramos condicionais;
4. teste obrigatoriedade, retorno, salvamento e conclusão;
5. teste upload com formatos, quantidade e limites esperados;
6. valide tokens e atributos usados por condições;
7. exporte respostas fictícias e confira nomes/códigos das colunas;
8. somente então ative ou substitua o survey de produção.

Não use respostas reais no teste estrutural. Preserve uma versão do Markdown e do LSS correspondente à aplicação efetiva.

## 8. Relatório de revisão

Apresente:

```text
Escopo revisado:
Erros:
Avisos:
Melhorias:
Riscos residuais:
Validação executada:
Pendências para o LimeSurvey:
```

Associe cada observação ao código da pergunta ou grupo. Evite recomendações genéricas sem indicar impacto e correção proposta.

