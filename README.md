# Fiscalização TCE-RJ nº 22/2026 - Auditoria de Conformidade LGPD 2026.2

**Tribunal de Contas do Estado do Rio de Janeiro (TCE-RJ)**  
**Secretaria-Geral de Controle Externo (SGE) | CAD-TI**  
**Processo PAAG nº 303.389-0/25**  
**Monitoramento do Processo TCE-RJ nº 217.899-0/2024 (Acórdão nº 3931/2025)**

Este repositório reúne os papéis de trabalho, matrizes de planejamento, termos de auditoria e scripts automatizados da **Fiscalização nº 22/2026**, referente à Auditoria de Conformidade à Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018 - LGPD) aplicada às 91 prefeituras municipais jurisdicionadas do Estado do Rio de Janeiro.

## Objetivo da Auditoria

Avaliar o grau de conformidade das 91 prefeituras municipais jurisdicionadas com os requisitos selecionados da LGPD, verificar o nível de cumprimento das decisões expedidas pelo Plenário do TCE-RJ no Acórdão nº 3931/2025, diagnosticar a evolução da maturidade (índice iLGPD 2026) em relação ao ciclo anterior (2024), avaliar a efetividade do material orientador pedagógico (*"Os 6 passos para adequação à LGPD"*) e mapear dinamicamente as causas estruturais de eventuais não cumprimentos.

## Estrutura do Repositório

```text
├── 00-Estudos_Preliminares/       # Histórico, relatórios de auditorias anteriores (2022, 2024) e questionário LimeSurvey
├── 01-Planejamento/               # Termos de auditoria, ata de reunião e matriz de planejamento (MD e DOCX)
│   ├── 01-Termos_de_Auditoria/    # Termos de auditoria formalizados, ata e visualizações (SVG/PNG)
│   └── 02-Matriz_de_Planejamento/ # Matriz de planejamento oficial e scripts de compilação
└── 98-scripts/                    # Automação de geração de termos de solicitação (TSIDs) e rotinas de suporte
```

## Escopo e Questões de Auditoria

- **Q1**: Preparação Institucional, Governança em Privacidade e Encarregado de Dados (DPO)
- **Q2**: Políticas Institucionais, Normativos e Ações de Capacitação em Privacidade
- **Q3**: Mapeamento, Inventário de Dados Pessoais, Registro das Operações (ROPA) e Bases Legais
- **Q4**: Gestão de Riscos à Privacidade, Relatório de Impacto (RIPD) e Privacy by Design
- **Q5**: Transparência Pública, Avisos de Privacidade e Atendimento aos Direitos dos Titulares
- **Q6**: Segurança da Informação, Controle de Acesso, Compartilhamento e Resposta a Incidentes
- **QT1 (Transversal)**: Monitoramento das Decisões do Processo TCE-RJ nº 217.899-0/2024 e Mapeamento Dinâmico de Causas de Não Cumprimento
- **QT2 (Transversal)**: Diagnóstico do Índice iLGPD 2026 e Avaliação do Material Didático (*"Os 6 passos para adequação à LGPD"*)

## Instrumentos de Coleta e Monitoramento

A coleta de dados utiliza o formulário eletrônico oficial estruturado no LimeSurvey (evolução do survey 832871), com perguntas dinâmicas e condicionais direcionadas para prefeituras com controles pendentes de deliberações anteriores e módulos específicos para avaliação de consultorias, percepção pedagógica e desafios de implementação.
