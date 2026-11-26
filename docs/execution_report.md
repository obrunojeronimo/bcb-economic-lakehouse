# Relatório de execução — 26/11/2026

Resultados de execução informados pelo responsável pelo projeto, validada no Databricks Free Edition com dados reais da API SGS. Este documento preserva esse recorte; uma nova execução pode produzir quantidades e tempos diferentes. Não há log bruto da execução versionado aqui.

## Volumes e qualidade

| Indicador | Resultado |
| --- | ---: |
| Séries econômicas | 5 |
| Registros ingeridos na Bronze | 4.500 |
| Registros válidos na Silver | 4.500 |
| Registros rejeitados | 0 |
| Duplicidades removidas | 0 |
| Aproveitamento nas regras implementadas | 100% |
| `workspace.bcb_gold.monthly_indicators` | 413 |
| `workspace.bcb_gold.latest_indicators` | 5 |
| `workspace.bcb_gold.economic_features` | 83 |

`data_quality` recebeu zero rejeições nessa execução. O aproveitamento é `4.500 / 4.500`, com base nos testes de tipo, presença, conflito de valores e duplicidade implementados em Silver. Não é uma avaliação de completude do SGS nem de plausibilidade econômica.

## Tempos

| Etapa | Duração |
| --- | ---: |
| Bronze | 6,53 s |
| Silver | 8,89 s |
| Gold | 9,85 s |
| Pipeline total | 26,96 s |

A soma das três etapas é 25,27 s; a diferença de 1,69 s em relação ao total abrange atividades fora dos cronômetros individuais, como inicialização, finalização e logging. Tempos são observações dessa execução, não benchmark reproduzível.

## Testes

Na validação operacional informada em 26/11/2026, **4 testes unitários** foram aprovados. Na revisão para v1.0.0, foram acrescentados dois testes de orquestração; a suíte local passou com **6 testes** em Python 3.12.16. `tests/test_extract.py` usa dublês HTTP tipados e `tests/test_pipeline.py` usa uma sessão Spark simulada; nenhum deles exercita a API real, o Databricks ou as transformações das três camadas. A execução do pipeline no workspace fornece evidência de integração operacional naquela data, mas não substitui testes de integração automatizados.

## Restrições da leitura

O pipeline é Full Refresh e sobrescreve cada tabela. Não há atomicidade entre as camadas, nem captura de versão comum entre as seis tabelas. Os números acima são um snapshot de 26/11/2026. Observações do mês corrente podem estar incompletas ou ainda não publicadas.
