[![Open in Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

# Regulamentos acadêmicos e manuais públicos

Corretude, eficiência e recuperação de contexto para IA generativa.

Este README é o manual operacional do repositório. O relatório técnico concentra a fundamentação, as provas, a análise detalhada, os experimentos e a discussão; esta página será atualizada à medida que esses artefatos forem produzidos.

## Relatório técnico

- [Relatório em desenvolvimento](https://docs.google.com/document/d/1RLEssVnXO0mOw0kx70mevGKRufop8sq1oqN-WQzNv2I/edit?usp=sharing)
  
**A PRODUZIR:** adicionar o PDF final do relatório nesta seção quando ele estiver concluído.

O relatório em PDF deve cobrir os 19 itens exigidos na Seção 10 do enunciado.
A tabela abaixo indica, para cada item, o artefato deste repositório que já
contém o material pronto para ser transposto — o relatório não precisa
reconstruir nada, apenas redigir e referenciar as evidências.

| # | Item exigido no relatório (Seção 10) | Material de origem neste repositório |
|---|---|---|
| 1 | Identificação da equipe | [`CONTRIBUICOES.md`](CONTRIBUICOES.md) — 5 integrantes e papéis por etapa |
| 2 | Tema, corpus e fonte | Seção [Corpus](#corpus) — 7 PDFs, 83 páginas, URLs oficiais |
| 3 | URL do repositório, **licença**, commit/tag/release e data de acesso | Badge do Colab e demais URLs; [`LICENSE`](LICENSE); commit `2a9a8e9`; acesso em 02/09/2026 às 21h10 |
| 4 | Definição formal do problema | [`ANALISE_CORRETUDE_COMPLEXIDADE.md`](ANALISE_CORRETUDE_COMPLEXIDADE.md) §1 (entrada, saída, relevância, pré/pós-condições, casos de borda) |
| 5 | Representação dos dados e estratégia de *chunking* | Seção [Corpus](#corpus) e `4_chunks/relatorio_chunking.json` |
| 6 | Algoritmos e pseudocódigo | `ANALISE_CORRETUDE_COMPLEXIDADE.md` §2 e §2.1 |
| 7 | Justificativa de corretude | `ANALISE_CORRETUDE_COMPLEXIDADE.md` §3 (invariante de laço + indução) |
| 8 | Análise no modelo RAM | `ANALISE_CORRETUDE_COMPLEXIDADE.md` §4.1 e §4.2 |
| 9 | Melhor, pior e caso médio | `ANALISE_CORRETUDE_COMPLEXIDADE.md` §4.3 |
| 10 | Recorrências | `ANALISE_CORRETUDE_COMPLEXIDADE.md` §5 |
| 11 | Metodologia experimental | Seção [Execução](#execução) (decisões de medição) e `metadados` de `7_resultados/relatorio_experimentos.json` |
| 12 | Resultados e gráficos | Seção [Resultados principais](#resultados-principais), `7_resultados/*.png` e as 3 tabelas CSV |
| 13 | Discussão de escalabilidade | `7_resultados/analise_assintotica.json`, `tabela_analise_assintotica.csv` e §6 do documento de análise |
| 14 | Relação com IA generativa e RAG | [`RAG_GENAI.md`](RAG_GENAI.md) |
| 15 | Limitações e ameaças à validade | Seção [Corpus](#corpus) (riscos e limitações), §3.6 e §4.5 do documento de análise e `RAG_GENAI.md` |
| 16 | Declaração de Uso de IA Generativa | [`DECLARACAO_IA.md`](DECLARACAO_IA.md) |
| 17 | Contribuição individual | [`CONTRIBUICOES.md`](CONTRIBUICOES.md) |
| 18 | URL do vídeo | [`VIDEO.md`](VIDEO.md) — **a preencher** |
| 19 | Referências | Seção [Referências](#referências) |

## Apresentação

- [Apresentação final — 24/09/2026](https://docs.google.com/presentation/d/1RHaAl9oXhdnzkjwhi0gLFhiCCBeQxHgZQSAyOLu0M_M/edit)

As apresentações estão em desenvolvimento e serão atualizadas com os resultados finais.

## Orquestrador no Google Colab

- [Abrir `orquestrador_pipeline.ipynb` no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

## Vídeo da atividade

**URL pública:** **A PRODUZIR** — a URL definitiva deve ser registrada neste
ponto, em [`VIDEO.md`](VIDEO.md) e na capa do relatório em PDF, conforme a
Seção 11 do enunciado. O arquivo [`VIDEO.md`](VIDEO.md) já contém os campos de
URL, data de gravação e identificação dos participantes, além do roteiro
sugerido para caber em 10 minutos.

## Status dos entregáveis

| Entregável | Situação |
|---|---|
| Corpus de 7 PDFs indexado | Concluído |
| Etapa 1 — extração e normalização | Concluído |
| Etapa 2 — chunking | Concluído — 182 chunks |
| Etapa 3 — índice invertido | Concluído — 4 061 termos, 21 530 postings |
| Etapa 4 — busca lexical e ordenação | Concluído — 14 testes automatizados |
| Etapa 5 — baterias experimentais | Concluído — medição in-process |
| Etapa 6 — tabela e gráficos | Concluído — 7 gráficos, 2 CSVs |
| Etapa 7 — análise assintótica do pipeline | Concluído — 8 etapas medidas |
| Etapa 8 — robustez, taxa de falhas e baseline de ordenação | Concluído — 18 execuções, 0 falhas |
| Aplicação web (React + Vite) | Concluído — `vite build` e `tsc --noEmit` sem erros |
| Análise de corretude e complexidade | Concluído — `ANALISE_CORRETUDE_COMPLEXIDADE.md` |
| Relação com IA generativa e RAG | Concluído — `RAG_GENAI.md` |
| Declaração de uso de IA generativa | Concluído — `DECLARACAO_IA.md` |
| Tabela de contribuição individual | Concluído — `CONTRIBUICOES.md` |
| Licença | Concluído — `LICENSE` |
| Relatório técnico | **A PRODUZIR** — documento no Google Docs; falta exportar o PDF |
| Apresentação | **A PRODUZIR** — slides no Google Drive, em revisão |
| Vídeo da atividade | **A PRODUZIR** — a gravar |

Os três itens finais dependem de produção humana (redação final, ensaio e gravação) e são os únicos pendentes para a entrega.

## Documentação complementar

| Documento | Conteúdo |
|---|---|
| [`ANALISE_CORRETUDE_COMPLEXIDADE.md`](ANALISE_CORRETUDE_COMPLEXIDADE.md) | Definição formal do problema, invariantes de laço, indução, modelo RAM, melhor/pior/caso médio, recorrências e complexidade de espaço |
| [`RAG_GENAI.md`](RAG_GENAI.md) | Uso do contexto recuperado por uma aplicação RAG: montagem do prompt, impacto de k e do chunking, relevância lexical vs. semântica, riscos de recuperação e trade-offs |
| [`DECLARACAO_IA.md`](DECLARACAO_IA.md) | Ferramenta e modelo, finalidade, prompts, sugestões aproveitadas/corrigidas/rejeitadas, erros identificados e verificação aplicada |
| [`CONTRIBUICOES.md`](CONTRIBUICOES.md) | Contribuição individual apurada a partir do histórico Git, por integrante e por etapa |
| [`VIDEO.md`](VIDEO.md) | Dados do vídeo (URL, data de gravação, participantes) e roteiro de gravação |
| [`LICENSE`](LICENSE) | Licença MIT para o código da equipe; condições de uso do corpus |

## Conformidade com os entregáveis da Seção 10 do enunciado

| # | Entregável exigido | Onde está neste repositório | Situação |
|---|---|---|---|
| 1 | Relatório técnico em PDF | Documento no Google Docs (ver [Relatório técnico](#relatório-técnico)) | **A PRODUZIR** |
| 2 | Código-fonte e instruções de execução | `1_scripts/`, `src/`, seções [Execução](#execução) e [Reprodução](#reprodução) | Concluído |
| 3 | README.md com dependências, ambiente, comandos, parâmetros e reprodução | Este arquivo | Concluído |
| 4 | Corpus, subconjunto permitido ou script de obtenção | `2_corpus/`, seção [Corpus](#corpus) com URLs oficiais | Concluído |
| 5 | Scripts de pré-processamento, ordenação, busca e medição | `1_scripts/1` a `1_scripts/8` | Concluído |
| 6 | Dados brutos, tabelas e gráficos dos experimentos | `3_dados/`, `4_chunks/`, `5_indexacao/`, `6_busca_lexical/`, `7_resultados/` | Concluído |
| 7 | Casos de teste e resultados esperados | [`1_scripts/test_etapa_4.py`](1_scripts/test_etapa_4.py) — 14 testes; seção [Testes](#testes) | Concluído |
| 8 | Prova ou justificativa de corretude | [`ANALISE_CORRETUDE_COMPLEXIDADE.md`](ANALISE_CORRETUDE_COMPLEXIDADE.md) | Concluído |
| 9 | Declaração de Uso de IA Generativa | [`DECLARACAO_IA.md`](DECLARACAO_IA.md) | Concluído |
| 10 | Tabela de contribuição individual dos integrantes | [`CONTRIBUICOES.md`](CONTRIBUICOES.md) | Concluído |
| 11 | Apresentação em PDF ou slides | Slides no Google Drive (ver [Apresentação](#apresentação)) | **A PRODUZIR** |
| 12 | URL funcional do vídeo (Seção 11) | `VIDEO.md`, esta seção [Vídeo da atividade](#vídeo-da-atividade) e o relatório em PDF | **A PRODUZIR** |

Os três itens pendentes (1, 11 e 12) dependem de produção humana e não podem ser
gerados a partir do código.

## Estrutura do repositório

- `orquestrador_pipeline.ipynb`: execução integrada no Google Colab.
- `1_scripts/1_processar_documentos.py`: inventário, extração, normalização e validação.
- `2_corpus/`: PDFs utilizados no corpus.
- `3_dados/`: JSONs gerados pelo pipeline com extração PyMuPDF e normalização.
- `4_chunks/`: segmentação de texto com janelamento deslizante e sobreposição; chunks prontos para indexação (`chunks.json`) e relatório estatístico da etapa (`relatorio_chunking.json`).
- `5_indexacao/`: índice invertido (`indice_invertido.json`) e relatório da indexação (`relatorio_indexacao.json`).
- `6_busca_lexical/`: candidatos com scores gerados (`candidatos_busca.json` na busca indexada e `candidatos_linear.json` na busca linear), métricas das duas buscas (`relatorio_busca.json` e `relatorio_busca_linear.json`), candidatos ordenados pelo Merge Sort (`candidatos_ordenados.json`), Top-k (`candidatos_topk.json`) e contadores da ordenação (`relatorio_ordenacao.json`).
- `7_resultados/`: relatório consolidado das baterias experimentais (`relatorio_experimentos.json`), tabela consolidada (`tabela_resultados.csv`), análise assintótica do pipeline (`analise_assintotica.json` e `tabela_analise_assintotica.csv`), avaliação de robustez e *baseline* de ordenação (`avaliacao_robustez.json`, `tabela_robustez.csv` e `tabela_baseline_ordenacao.csv`) e os gráficos dos resultados (`grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png`, `grafico_etapas_pipeline.png` e `grafico_analise_assintotica.png`).
- `src/`: aplicação web em React + Vite que consulta os artefatos já versionados em `public/data/`.
- `ANALISE_CORRETUDE_COMPLEXIDADE.md`: justificativa de corretude, análise no modelo RAM, melhor/pior/caso médio, recorrências e complexidade de espaço.
- `RAG_GENAI.md`: relação do contexto recuperado com aplicações RAG e IA generativa.
- `DECLARACAO_IA.md`: declaração de uso crítico de IA generativa.
- `CONTRIBUICOES.md`: contribuição individual dos integrantes.
- `VIDEO.md`: dados e roteiro do vídeo da atividade.
- `LICENSE`: licença do código e condições de uso do corpus.

## Resultados principais

Medições in-process, em Windows 11 (AMD64) com Python 3.14.7:

| Configuração | Carga 1 — 182 chunks | Carga 2 — 91 chunks |
|---|---|---|
| 1 — Busca linear (baseline) | 41,46 ms | 23,13 ms |
| 2 — Busca indexada (Okapi BM25) | 3,65 ms | 2,57 ms |
| 3 — Indexada + Merge Sort Top-k | 2,70 ms | 3,37 ms |

A busca indexada é cerca de **11× mais rápida** que a linear no corpus integral e, o que é o ponto central, é a única que praticamente não escala com o tamanho do corpus: reduzir o corpus à metade quase não altera seu tempo (3,65 → 2,57 ms), enquanto a busca linear cai para pouco mais da metade (41,46 → 23,13 ms), como esperado de um custo Θ(n). A configuração 3 acrescenta ao índice o custo do Merge Sort, que ordena os 75 candidatos do corpus integral em cerca de 0,52 ms e executa **369 comparações** — 351 comparações de score e 18 desempates por `id_chunk`. O artefato isolado da Etapa 4 (`6_busca_lexical/relatorio_ordenacao.json`), que ordena exatamente os mesmos 75 candidatos, registra os mesmos 369, porque as duas contagens incluem o desempate.

Por que 18 desempates: os 75 candidatos produzem **61 scores distintos**, o que significa que **14 candidatos compartilham o score com outro** (18,7% do conjunto), em 7 grupos de scores repetidos — com multiplicidades 5, 3, 3, 3, 3, 2 e 2. Ao longo das fusões, o Merge Sort cai 18 vezes no ramo de igualdade de score; como o score é igual, cada uma dessas 18 comparações é resolvida pelo `id_chunk`, o que produz exatamente `num_comparacoes_score = 351` e `num_comparacoes_id_chunk = 18`. Os 18 desempates e os 14 candidatos duplicados são grandezas diferentes: a primeira conta *comparações*, a segunda conta *elementos*.

A Etapa 8 fecha a verificação de ordenação contra a biblioteca de referência, como pede a Seção 5.2, item 5. Sobre os mesmos 75 candidatos reais (valores da execução registrada em `7_resultados/avaliacao_robustez.json`):

| Implementação | Tempo (mediana) | Ordem final | Top-5 |
|---|---|---|---|
| `merge_sort` da equipe | 0,3390 ms | — | — |
| `sorted()` (Timsort) | 0,0282 ms | idêntica | idêntico |
| `heapq.nsmallest` | 0,0290 ms | idêntica | idêntico |

A razão entre a referência e a implementação da equipe é 0,0832 — ou seja, o Timsort é cerca de 12× mais rápido, o que é o esperado de um algoritmo de biblioteca escrito em C contra uma implementação em Python puro. O ponto que a comparação estabelece não é desempenho, e sim **equivalência de resultado**: a ordem completa e o Top-5 coincidem. A varredura sintética de 75 a 4 800 elementos confirma o mesmo em todas as 7 ordens de grandeza. Os tempos absolutos variam entre execuções (a medição é feita em máquina compartilhada); as contagens de comparações, movimentações e chamadas recursivas, essas, são determinísticas.

A bateria de robustez da Etapa 8 cobre a exigência de "taxa de falhas, resultados vazios ou itens irrelevantes" da Seção 7.3: 9 consultas em 2 configurações, 18 execuções, **0 falhas (0,0%)** e 5 resultados vazios (55,6%). Os 5 vazios são todos consultas construídas para serem patológicas — string vazia, apenas espaços, apenas pontuação, apenas stopwords e termos fora do vocabulário —, e a consulta mista ("de bolsas xilofone") ainda devolve resultados ao descartar o termo estranho. A mesma bateria confirma que a busca linear e a busca indexada devolvem **o mesmo Top-k** nas 9 consultas.


Os valores absolutos variam entre execuções por causa da contenção da máquina, mas o ranking entre as configurações é estável — é ele que sustenta a conclusão, não os milissegundos exatos. As medianas por configuração e o desvio-padrão de cada carga estão em `7_resultados/tabela_resultados.csv`.

A análise assintótica do pipeline (Etapa 7) classifica cada etapa pelo expoente empírico da regressão log-log:

| Etapa | Unidade de entrada | Faixa de n | Observado | Expoente |
|---|---|---|---|---|
| Extração de texto | páginas | 3 – 30 | O(n log n) | 0,50 |
| Normalização | caracteres | 9 957 – 79 662 | O(n log n) | 1,06 |
| Chunking | palavras | 1 547 – 12 371 | O(n log n) | 1,07 |
| Indexação | tokens | 5 102 – 37 269 | O(n log n) | 0,91 |
| Busca linear | chunks varridos | 22 – 182 | O(n log n) | 0,78 |
| Busca indexada | postings | 12 – 78 | O(1) | −0,10 |
| Merge Sort | candidatos | 256 – 2 048 | O(n log n) | 1,29 |
| Seleção Top-k | candidatos | 256 – 2 048 | O(1) | −0,02 |

O expoente deve ser lido como o coeficiente de crescimento: valores próximos de 1 correspondem a crescimento linear e o excedente sobre 1 é a contribuição do termo logarítmico. O `O(n log n)` eleito para a extração, cujo expoente é 0,50, e o eleito para a busca linear, com 0,78, são consequências de ruído em n pequeno: os primeiros pontos de cada varredura pagam custos de primeira execução (I/O de PDF e tokenização) que não se repetem, e o ajuste recebe essa curvatura. Uma varredura em ordem decrescente desloca esse efeito para o ponto de menor n, onde é visível, e uma medição isolada em n = 22/91/182 devolve expoente 1,00/0,96, confirmando que a busca é genuinamente Θ(n).

Duas limitações devem ser explicitadas na defesa:

1. **Faixa de n.** Cada etapa cobre aproximadamente uma década de n, limitada pelo corpus disponível. O termo logarítmico varia apenas cerca de 3,4 (o `log₂` de 2 a 182) nessa faixa, o que torna o R² incapaz de separar `O(n)` de `O(n log n)`: medido em todas as etapas, a diferença entre os dois ajustes é de 0,01 a 0,06 e quase sempre favorece `O(n)`. Por isso a classificação usa o expoente, não o R².
2. **Máquina compartilhada.** As medições foram feitas em uma máquina de uso geral, não dedicada. Cada ponto é a mediana de repetições após aquecimentos, mas picos de carga do sistema ainda afetam varreduras longas; reexecuções sucessivas do script produzem curvas monotônicas e expoentes estáveis, dentro de poucos centésimos.


## Dependências

Python 3, `PyMuPDF`, `nltk` e `matplotlib`. Os testes da Etapa 4 requerem `pytest`.

## Ambiente

Execução validada em Windows com Python 3. O script usa caminhos relativos ao repositório.

## Instalação

```bash
python -m pip install PyMuPDF nltk matplotlib pytest
python -c "import nltk; nltk.download('stopwords')"
```

## Execução

Etapa 1 — Processar documentos (extração e normalização):
```bash
python 1_scripts/1_processar_documentos.py
```

Etapa 2 — Geração de chunks:
```bash
python 1_scripts/2_gerar_chunks.py
```

Etapa 3 — Construção do índice invertido:
```bash
python 1_scripts/3_construir_indice_invertido.py
```

Etapa 4 — Busca lexical e geração de candidatos (Okapi BM25 ou Simples):
```bash
# Execução padrão (busca indexada com Okapi BM25, gera arquivo candidatos_busca.json):
python 1_scripts/4_buscar_e_ordenar.py

# Personalizando a consulta e k:
python 1_scripts/4_buscar_e_ordenar.py --consulta "critérios para atribuição de bolsas" --k 5

# Ajuste fino de hiperparâmetros BM25 (k1 e b):
python 1_scripts/4_buscar_e_ordenar.py --metrica bm25 --k1 1.2 --b 0.75

# Indicando nome de arquivo customizado de saída:
python 1_scripts/4_buscar_e_ordenar.py --saida-candidatos 6_busca_lexical/minha_busca.json --relatorio-busca 6_busca_lexical/meu_relatorio.json

# Execuções alternativas para comparação/benchmarking (gerando linear ou ambos):
python 1_scripts/4_buscar_e_ordenar.py --modo linear
python 1_scripts/4_buscar_e_ordenar.py --modo ambos
```

Etapa 5 — Experimentos comparativos (matriz de configurações × cargas × repetições):
```bash
python 1_scripts/5_experimentar.py
```

Etapa 7 — Análise assintótica do pipeline:
```bash
python 1_scripts/7_analise_assintotica.py
```

Etapa 8 — Robustez, taxa de falhas e *baseline* de ordenação (Seção 7.3 e Seção 5.2, item 5, do enunciado):
```bash
python 1_scripts/8_avaliar_robustez.py
```

Etapa 6 — Tabela consolidada e gráficos dos resultados (executar por último, pois consolida as saídas das etapas 1 a 5 e 7):
```bash
python 1_scripts/6_gerar_graficos.py
```

A Etapa 8 é **aditiva e somente leitura** sobre os artefatos das etapas 1 a 4:
não regrava nenhum arquivo produzido por elas. Ela produz duas evidências que
faltavam:

1. **Bateria de robustez** — 9 consultas (relevante, string vazia, apenas
   espaços, apenas pontuação, apenas stopwords, fora do vocabulário e uma mista)
   executadas nas duas configurações de busca: 18 execuções, **0 falhas** e 5
   resultados vazios — todos correspondentes às consultas patológicas
   construídas de propósito. Também confirma que a busca linear e a indexada
   devolvem **o mesmo Top-k** nas 9 consultas.
2. ***Baseline* de ordenação contra a biblioteca de referência** — o `merge_sort`
   da equipe é comparado, na **mesma** lista de 75 candidatos reais e em
   varreduras sintéticas de 75 a 4 800 elementos, com `sorted()` (Timsort) e com
   `heapq.nsmallest`. Em todas as ordens de grandeza testadas a ordem final e o
   Top-5 são idênticos aos das duas referências.

Como o protocolo de medição é o ponto mais delicado do trabalho, vale registrar as decisões:

- A Etapa 5 mede as configurações **no mesmo processo** que as executa, e não por subprocesso. A versão anterior disparava um processo novo por bateria e cronometrava o processo inteiro; como a inicialização do interpretador e a importação do `nltk` custam cerca de 920 ms, esse custo fixo dominava o tempo medido (a busca em si leva poucos milissegundos) e chegava a inverter o ranking — a configuração com Merge Sort aparecia mais rápida que a busca linear. Com a medição in-process, o ranking passa a refletir o algoritmo.
- As duas cargas deixaram de apontar para o mesmo arquivo de chunks. Hoje a `Carga 1` é o corpus integral (182 chunks) e a `Carga 2` é um subconjunto real (91 chunks), de modo que o efeito do tamanho de entrada é observável.
- A Etapa 5 grava apenas em `7_resultados/relatorio_experimentos.json` e não sobrescreve mais os artefatos da Etapa 4.
- A Etapa 7 repete cada ponto (com aquecimentos e mediana) porque a máquina de medição não é dedicada, e classifica cada etapa pelo **expoente da regressão log-log**, não pelo R². Sobre uma faixa de n de aproximadamente uma década, `R²(O(n))` e `R²(O(n log n))` diferem por 0,01 a 0,06 e quase sempre favorecem `O(n)`, o que torna o R² incapaz de separar as duas classes; o expoente, por outro lado, é estável e interpretável.

A Etapa 5 gera `7_resultados/relatorio_experimentos.json` (tempo, pico de memória e status de cada execução, com síntese por configuração **e por carga**). A Etapa 6 lê os relatórios das etapas 1 a 5 mais a saída da Etapa 7 e gera `tabela_resultados.csv`, `tabela_analise_assintotica.csv` e os gráficos `grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png`, `grafico_etapas_pipeline.png` e `grafico_analise_assintotica.png`.

## Parâmetros

- `1_scripts/1_processar_documentos.py`:
  - `--corpus`: diretório dos PDFs de entrada (padrão: `2_corpus`).
  - `--saida`: diretório para gravação dos JSONs de extração e catálogo (padrão: `3_dados`).

- `1_scripts/2_gerar_chunks.py`:
  - `--entrada`: caminho do arquivo de documentos normalizados (padrão: `3_dados/documentos_normalizados.json`).
  - `--saida`: caminho para gravação dos chunks (padrão: `4_chunks/chunks.json`).
  - `--relatorio`: caminho para o relatório estatístico da etapa (padrão: `4_chunks/relatorio_chunking.json`).
  - `--tamanho-chunk`: quantidade de palavras por chunk (padrão: `200`).
  - `--overlap`: quantidade de palavras de sobreposição entre chunks consecutivos (padrão: `30`).

- `1_scripts/3_construir_indice_invertido.py`:
  - `--entrada`: arquivo de chunks de entrada (padrão: `4_chunks/chunks.json`).
  - `--saida`: arquivo do índice invertido (padrão: `5_indexacao/indice_invertido.json`).
  - `--relatorio`: relatório da indexação (padrão: `5_indexacao/relatorio_indexacao.json`).

- `1_scripts/4_buscar_e_ordenar.py`:
  - `--consulta`: consulta textual a pesquisar (padrão: `"critérios para atribuição de bolsas"`).
  - `--k`: quantidade de resultados desejados no Top-k (padrão: `5`).
  - `--modo`: estratégia de recuperação: `indexada`, `linear` ou `ambos` (padrão: `indexada`).
  - `--metrica`: função de pontuação de relevância: `bm25` (Okapi BM25) ou `simples` (contagem de frequências) (padrão: `bm25`).
  - `--k1`: parâmetro $k_1$ do BM25 que calibra a saturação do TF (padrão: `1.5`).
  - `--b`: parâmetro $b$ do BM25 que calibra a penalização pelo tamanho do documento (padrão: `0.75`).
  - `--chunks`: caminho dos chunks de entrada (padrão: `4_chunks/chunks.json`).
  - `--indice`: caminho do índice invertido (padrão: `5_indexacao/indice_invertido.json`).
  - `--saida-candidatos`: caminho customizado para o arquivo de candidatos (padrão na busca indexada: `6_busca_lexical/candidatos_busca.json`).
  - `--relatorio-busca`: caminho customizado para o relatório de métricas (padrão na busca indexada: `6_busca_lexical/relatorio_busca.json`).
  - `--saida_candidatos_ordenados`: caminho customizado para o arquivo de candidatos ordenados (padrão: `6_busca_lexical/candidatos_ordenados.json`).
  - `--saida_candidatos_top_k`: caminho customizado para o arquivo do Top-k (padrão: `6_busca_lexical/candidatos_topk.json`).
  - `--relatorio-ordenacao`: caminho customizado para o relatório de ordenação (padrão: `6_busca_lexical/relatorio_ordenacao.json`).

- `1_scripts/5_experimentar.py`:
  - `--consulta`: consulta padrão utilizada nas baterias de teste (padrão: `"critérios para atribuição de bolsas e requisitos de matrícula"`).
  - `--k`: quantidade de candidatos retornados no Top-k (padrão: `5`).
  - `--chunks`: caminho do arquivo de chunks de entrada (padrão: `4_chunks/chunks.json`).
  - `--saida`: caminho para gravação do relatório experimental consolidado (padrão: `7_resultados/relatorio_experimentos.json`).
  - `--indice`: índice invertido, necessário à configuração indexada (padrão: `5_indexacao/indice_invertido.json`).

- `1_scripts/6_gerar_graficos.py`:
  - `--resultados`: diretório de saída dos gráficos e da tabela (padrão: `7_resultados`).
  - `--experimentos`: relatório experimental de entrada (padrão: `7_resultados/relatorio_experimentos.json`).
  - `--busca-linear`: relatório da busca linear (padrão: `6_busca_lexical/relatorio_busca_linear.json`).
  - `--busca-indexada`: relatório da busca indexada (padrão: `6_busca_lexical/relatorio_busca.json`).
  - `--ordenacao`: relatório da ordenação com os contadores do Merge Sort (padrão: `6_busca_lexical/relatorio_ordenacao.json`).
  - `--indexacao`: relatório da indexação (padrão: `5_indexacao/relatorio_indexacao.json`).
  - `--indice`: índice invertido de entrada, usado na distribuição de frequências (padrão: `5_indexacao/indice_invertido.json`).
  - `--chunking`: relatório da etapa de chunking (padrão: `4_chunks/relatorio_chunking.json`).
  - `--processamento`: relatório da etapa de extração e normalização (padrão: `3_dados/relatorio_processamento.json`).
  - `--script-busca`: script cujo Merge Sort é reexecutado para medir a curva de escalabilidade (padrão: `1_scripts/4_buscar_e_ordenar.py`).
  - `--tamanhos-escala`: tamanhos de entrada da curva experimental do Merge Sort (padrão: `8 16 32 64 128 256 512 1024 2048`).
  - `--repeticoes-escala`: repetições por tamanho na curva experimental (padrão: `30`).
  - `--analise-assintotica`: saída da Etapa 7, consolidada em `tabela_analise_assintotica.csv` e no gráfico `grafico_analise_assintotica.png` (padrão: `7_resultados/analise_assintotica.json`).

- `1_scripts/7_analise_assintotica.py`:
  - `--corpus`: diretório com os PDFs do corpus, usado no estágio de extração (padrão: `2_corpus`).
  - `--chunks`: artefato com os chunks gerados na Etapa 2 (padrão: `4_chunks/chunks.json`).
  - `--normalizados`: artefato com os documentos normalizados da Etapa 1 (padrão: `3_dados/documentos_normalizados.json`).
  - `--indice`: índice invertido gerado na Etapa 3 (padrão: `5_indexacao/indice_invertido.json`).
  - `--pontos`: número de pontos de medição por estágio (padrão: `8`).
  - `--consulta`: consulta usada nos estágios de busca (padrão: a consulta do trabalho).
  - `--saida`: arquivo JSON de saída com as medições e ajustes (padrão: `7_resultados/analise_assintotica.json`).
  - `--grafico`: arquivo PNG com as curvas medidas e os modelos ajustados (padrão: `7_resultados/grafico_analise_assintotica.png`).

- `1_scripts/8_avaliar_robustez.py`:
  - `--chunks`: chunks da Etapa 2 (padrão: `4_chunks/chunks.json`).
  - `--indice`: índice invertido da Etapa 3 (padrão: `5_indexacao/indice_invertido.json`).
  - `--candidatos`: artefato de candidatos da Etapa 4 usado como carga real da comparação de ordenação (padrão: `6_busca_lexical/candidatos_busca.json`).
  - `--consulta`: consulta usada nas consultas de robustez marcadas como relevantes (padrão: `"critérios para atribuição de bolsas"`).
  - `--k`: tamanho do Top-k (padrão: `5`).
  - `--repeticao`: repetições internas por medição de tempo (padrão: `5`).
  - `--pontos`: quantidade de pontos da varredura de escala sintética (padrão: `7`).
  - `--semente`: semente das cargas sintéticas, para reprodutibilidade (padrão: `20260923`).
  - `--saida`: JSON consolidado de saída (padrão: `7_resultados/avaliacao_robustez.json`).
  - `--tabela-robustez`: CSV da taxa de falhas e de resultados vazios (padrão: `7_resultados/tabela_robustez.csv`).
  - `--tabela-baseline`: CSV do *baseline* de ordenação (padrão: `7_resultados/tabela_baseline_ordenacao.csv`).

## Reprodução

1. Obter ou utilizar os PDFs do diretório `2_corpus/`.
2. Preparar o ambiente conforme as seções acima.
3. Executar os comandos do pipeline (etapas 1 a 4), depois os experimentos (etapa 5), a análise assintótica (etapa 7), a avaliação de robustez (etapa 8) e, por fim, a consolidação (etapa 6).
4. Conferir os resultados, tabelas, gráficos e dados brutos gerados.

Todas as medições de tempo devem ser feitas no **mesmo ambiente**. Os valores registrados em `relatorio_experimentos.json` e nos gráficos foram obtidos em Windows 11 (AMD64) com Python 3.14.7; misturar máquinas ou versões invalida a comparação entre configurações.

## Testes

```bash
python -m pytest 1_scripts/test_etapa_4.py
```

A suíte cobre a corretude da ordenação, o critério de desempate
`(−score, id_chunk)`, a contagem de comparações, a seleção do Top-k e os casos
de borda (lista vazia, `k` igual a 1, `k` maior que o número de candidatos e
empates totais). Resultado esperado: **14 testes aprovados**.

Os "resultados esperados" dos experimentos estão nos artefatos versionados em
`7_resultados/`, e a verificação de que eles não são apenas plausíveis mas
**reproduzíveis** é feita por conferência aritmética entre contadores: a soma
`comparacoes_score + comparacoes_id_chunk` deve igualar `comparacoes_totais`
(351 + 18 = 369), o número de chamadas recursivas deve ser `2n − 1` (149 para
n = 75) e a profundidade máxima deve ser `1 + ⌈log₂ n⌉` (8 para n = 75).

## Corpus

Corpus normativo e orientativo público do PROCC/UFS e normas correlatas. Uso exclusivamente acadêmico.

- **Acesso/download:** 02/09/2026, às 21h10.
- **Quantidade:** 7 documentos, 83 páginas e aproximadamente 4,50 MB.
- **Idioma/formato:** português brasileiro; arquivos PDF.
- **Licença e condições de uso:** os PDFs são **documentos institucionais públicos**, publicados pelo próprio PROCC/UFS em seus canais oficiais (SIGAA) e pelo Edital CAPES, e são utilizados aqui **exclusivamente para fins acadêmicos e não comerciais**, sem redistribuição com finalidade comercial. Eles **não** estão cobertos pela licença MIT que se aplica ao código da equipe: a licença do repositório cobre apenas os scripts e artefatos produzidos pelo grupo, e cada documento permanece sujeito às condições do órgão emissor. As URLs oficiais de origem constam da tabela abaixo, o que permite verificar a procedência de cada arquivo. Ver [`LICENSE`](LICENSE).
- **Dados removidos ou anonimizados:** nenhum — o corpus é composto por atos normativos públicos, sem dados pessoais.
- **Limpeza e normalização:** Unicode NFC, quebras de linha, espaços repetidos e hifenização entre linhas; texto original preservado.
- **Chunking:** janelamento deslizante contínuo de 200 palavras por documento, com overlap de 30 palavras entre chunks consecutivos (passo de 170 palavras). Total de 182 chunks, com média de 196,85 palavras/chunk: 175 chunks atingem a janela cheia de 200 palavras e apenas 7 são menores (o menor tem 64), por serem o último chunk de um documento. Os chunks são extraídos do fluxo contínuo de texto, portanto o overlap de 30 palavras também ocorre entre chunks de uma mesma página; 80 chunks (43,96%) atravessam fronteiras de página.
- **Riscos de viés, qualidade ou cobertura:** o corpus é **pequeno e tematicamente concentrado** em normas do PROCC/UFS sobre bolsas, credenciamento e estrutura curricular. Consequências observáveis: (i) assuntos ausentes do corpus são irrecuperáveis por qualquer consulta, e o sistema não distingue "não existe" de "não encontrei"; (ii) o Top-5 da consulta de referência traz **4 dos 5 chunks de apenas 2 documentos**, o que concentra o contexto recuperado e pode enviesar uma resposta gerada a partir dele; (iii) a relevância é **lexical**, de modo que consultas formuladas com vocabulário diferente do normativo ("auxílio" em vez de "bolsa") têm cobertura pior; (iv) uma página de `Resolucao_04_2021_CONEPE_Normas_Academicas_Pos_Graduacao.pdf` é apenas imagem, sem camada de texto, e seu conteúdo é irrecuperável — a ocorrência está registrada em `3_dados/relatorio_processamento.json`; (v) todo o material é pt-BR, e consultas em outro idioma produzem zero resultados.
- **Limitações para generalização dos resultados:** os tempos e as contagens deste trabalho caracterizam **este** corpus, com N = 182 chunks e vocabulário de 4 061 termos. O comportamento assintótico é geral, mas os valores absolutos não se transferem para outros conjuntos — em particular, o tempo de consulta indexada depende do número de candidatos `n_c`, que aqui é 75 (corpus integral) e 32 (metade do corpus), e não do tamanho do corpus. Além disso, `n_c` cresce com a cobertura terminológica da consulta, de modo que uma consulta com termos muito comuns pode elevar `n_c` bem acima de 75 e alterar o custo relativo das configurações. Por fim, não há conjunto de relevância anotado, o que impede reportar Precision@k e limita as conclusões à eficiência, não à qualidade da recuperação.

| Documento | URL oficial |
|---|---|
| IN 02/2026/PROCC — Destinação de recursos financeiros | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5040212&key=bd7f4126e48c0ff0c3f3ecd020bea2af) |
| IN 01/2026/PROCC — Credenciamento, recredenciamento e distribuição de vagas de orientação docente | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=5025297&key=2d84693e082547f2c3b9e5a7211baf63) |
| Edital CAPES nº 14/2023 — PRAPG | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4214078&key=9a30771aef926507ec26e66ff5da6260) |
| IN 01/2023/PROCC — Estrutura curricular do Mestrado | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4024039&key=3935a3b7b0d57462398d13c8fa68def5) |
| IN 01/2024/PROCC — Critérios para atribuição de bolsas | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4357246&key=807372ebd6adf4d3ad63cd51277fec38) |
| Resolução nº 04/2021/CONEPE — Normas Acadêmicas da Pós-Graduação | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=2737960&key=1861aeae080b4f6318206935e3b17414) |
| Resolução nº 29/2022/CONEPE — Regimento Interno do PROCC | [SIGAA](https://www.sigaa.ufs.br/sigaa/verProducao?idProducao=4218408&key=0f7e24ac2195143e5735697d19cb43ac) |


## Aplicação Web — Recuperação Lexical e Ordenação (PROCC/UFS)

Interface web interativa desenvolvida para busca, recuperação e ordenação de contexto sobre os regulamentos acadêmicos do Programa de Pós-Graduação em Ciência da Computação (PROCC/UFS).

🔗 **[Acessar a Aplicação Web](https://procc-recuperacao-documentos.vercel.app/)**

> A publicação é feita na **Vercel** pelo workflow [`.github/workflows/deploy-vercel.yml`](.github/workflows/deploy-vercel.yml) a cada push em `main`.
> O **GitHub Pages não é utilizado**: o `index.html` da raiz é o arquivo de desenvolvimento do Vite e, quando servido estaticamente (por exemplo, pelos forks), aponta para `/src/main.tsx` e resulta em página em branco.

## Licença

O **código-fonte** deste repositório (scripts em `1_scripts/`, aplicação web em
`src/`, *notebook* e documentação produzida pela equipe) está licenciado sob a
**Licença MIT** — ver [`LICENSE`](LICENSE).

Os **PDFs do corpus** em `2_corpus/` **não** estão cobertos por essa licença:
são documentos institucionais públicos, publicados pelos próprios órgãos
emissores, e são utilizados neste trabalho exclusivamente para fins acadêmicos e
não comerciais. As URLs oficiais de origem estão na seção [Corpus](#corpus), o
que permite verificar a procedência de cada arquivo.

Este repositório não contém chaves, senhas, tokens ou dados pessoais. Arquivos
grandes (PDFs do corpus e `node_modules/`) são controlados por `.gitignore`, e as
instruções para obtê-los ou reproduzi-los estão nas seções
[Instalação](#instalação), [Execução](#execução) e [Reprodução](#reprodução).

## Referências

Referências bibliográficas efetivamente consultadas na atividade:

**Algoritmos e estruturas de dados**

- CORMEN, Thomas H. et al. *Introduction to Algorithms*. 4. ed. Cambridge: MIT Press, 2022. (Merge Sort, recorrências e modelo RAM)
- KLEINBERG, Jon; TARDOS, Éva. *Algorithm Design*. Boston: Pearson, 2006. (divisão e conquista, análise de recorrências)
- SKIENA, Steven S. *The Algorithm Design Manual*. 3. ed. Cham: Springer, 2020. (escolha de algoritmos e *trade-offs* práticos)
- SEDGEWICK, Robert; WAYNE, Kevin. *Algorithms*. 4. ed. Boston: Addison-Wesley, 2011. (*baseline* de ordenação e *mergesort*)

**Recuperação de informação**

- MANNING, Christopher D.; RAGHAVAN, Prabhakar; SCHÜTZE, Hinrich. *Introduction to Information Retrieval*. Cambridge: Cambridge University Press, 2008. (índice invertido, *postings lists* e medidas de avaliação)
- ROBERTSON, Stephen; ZARAGOZA, Hugo. *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval, v. 3, n. 4, p. 333–389, 2009. (fundamentação do Okapi BM25 e dos parâmetros `k1` e `b`)

**Recuperação aumentada por geração (RAG) e IA generativa**

- LEWIS, Patrick et al. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS, 2020. Disponível em: <https://arxiv.org/abs/2005.11401>.
- ZHOU, Zixuan et al. *A Survey on Efficient Inference for Large Language Models*. arXiv:2404.14294, 2024. Disponível em: <https://arxiv.org/abs/2404.14294>.
- GAN, Aoran et al. *Retrieval Augmented Generation Evaluation in the Era of Large Language Models: A Comprehensive Survey*. arXiv:2504.14891, 2025. Disponível em: <https://arxiv.org/abs/2504.14891>.
- SENTENCE TRANSFORMERS. Repositório oficial. Disponível em: <https://github.com/huggingface/sentence-transformers>. (alternativa de busca semântica não adotada, discutida em [`RAG_GENAI.md`](RAG_GENAI.md))
- FAISS. *Faiss documentation*. Disponível em: <https://faiss.ai/>. (busca vetorial em larga escala, discutida como trabalho futuro)

**Ferramentas**

- BIRD, Steven; KLEIN, Ewan; LOPER, Edward. *Natural Language Processing with Python*. Sebastopol: O'Reilly Media, 2009. (NLTK, usado na tokenização e na lista de *stopwords*)
- PYMUPDF. *PyMuPDF Documentation*. Disponível em: <https://pymupdf.readthedocs.io/>. (extração de texto dos PDFs)

As fontes do corpus (atos normativos do PROCC/UFS e o Edital CAPES) estão
listadas com seus endereços oficiais na seção [Corpus](#corpus).


