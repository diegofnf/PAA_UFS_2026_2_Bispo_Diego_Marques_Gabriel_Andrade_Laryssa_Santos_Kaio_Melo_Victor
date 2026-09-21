[![Open in Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

# Regulamentos acadêmicos e manuais públicos

Corretude, eficiência e recuperação de contexto para IA generativa.

Este README é o manual operacional do repositório. O relatório técnico concentra a fundamentação, as provas, a análise detalhada, os experimentos e a discussão; esta página será atualizada à medida que esses artefatos forem produzidos.

## Relatório técnico

- [Relatório em desenvolvimento](https://docs.google.com/document/d/1RLEssVnXO0mOw0kx70mevGKRufop8sq1oqN-WQzNv2I/edit?usp=sharing)
  
**A PRODUZIR:** adicionar o PDF final do relatório nesta seção quando ele estiver concluído.

## Apresentação

- [Apresentação final — 24/09/2026](https://docs.google.com/presentation/d/1RHaAl9oXhdnzkjwhi0gLFhiCCBeQxHgZQSAyOLu0M_M/edit)

As apresentações estão em desenvolvimento e serão atualizadas com os resultados finais.

## Orquestrador no Google Colab

- [Abrir `orquestrador_pipeline.ipynb` no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

## Vídeo da atividade

**URL pública:** **A PRODUZIR**.

## Status dos entregáveis

Os itens ainda não implementados ou não definidos estão marcados como **A PRODUZIR** e serão atualizados no decorrer do projeto.

## Estrutura do repositório

- `orquestrador_pipeline.ipynb`: execução integrada no Google Colab.
- `1_scripts/1_processar_documentos.py`: inventário, extração, normalização e validação.
- `2_corpus/`: PDFs utilizados no corpus.
- `3_dados/`: JSONs gerados pelo pipeline com extração PyMuPDF e normalização.
- `4_chunks/`: segmentação de texto com janelamento deslizante e sobreposição; chunks prontos para indexação (`chunks.json`) e relatório estatístico da etapa (`relatorio_chunking.json`).
- `5_indexacao/`: índice invertido (`indice_invertido.json`) e relatório da indexação (`relatorio_indexacao.json`).
- `6_busca_lexical/`: candidatos com scores gerados (`candidatos_busca.json` na busca indexada e `candidatos_linear.json` na busca linear), métricas das duas buscas (`relatorio_busca.json` e `relatorio_busca_linear.json`), candidatos ordenados pelo Merge Sort (`candidatos_ordenados.json`), Top-k (`candidatos_topk.json`) e contadores da ordenação (`relatorio_ordenacao.json`).
- `7_resultados/`: relatório consolidado das baterias experimentais (`relatorio_experimentos.json`), tabela consolidada (`tabela_resultados.csv`), análise assintótica do pipeline (`analise_assintotica.json` e `tabela_analise_assintotica.csv`) e os gráficos dos resultados (`grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png`, `grafico_etapas_pipeline.png` e `grafico_analise_assintotica.png`).

## Resultados principais

Medições in-process, em Windows 11 (AMD64) com Python 3.14.7:

| Configuração | Carga 1 — 182 chunks | Carga 2 — 91 chunks |
|---|---|---|
| 1 — Busca linear (baseline) | 41,46 ms | 23,13 ms |
| 2 — Busca indexada (Okapi BM25) | 3,65 ms | 2,57 ms |
| 3 — Indexada + Merge Sort Top-k | 2,70 ms | 3,37 ms |

A busca indexada é cerca de **11× mais rápida** que a linear no corpus integral e, o que é o ponto central, é a única que praticamente não escala com o tamanho do corpus: reduzir o corpus à metade quase não altera seu tempo (3,65 → 2,57 ms), enquanto a busca linear cai para pouco mais da metade (41,46 → 23,13 ms), como esperado de um custo Θ(n). A configuração 3 acrescenta ao índice o custo do Merge Sort, que ordena os 75 candidatos do corpus integral em cerca de 0,52 ms (369 comparações de score). O artefato isolado da Etapa 4, que ordena os mesmos 75 candidatos, registra 351 comparações — a diferença vem dos 18 empates de score, resolvidos de forma distinta conforme a ordem em que os candidatos chegam.

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
python 1_scripts/4_buscar_e_ordenar.py --saida-candidatos 6_busca_lexical/minha_busca.json --relatorio 6_busca_lexical/meu_relatorio.json

# Execuções alternativas para comparação/benchmarking (gerando linear ou ambos):
python 1_scripts/4_buscar_e_ordenar.py --modo linear
python 1_scripts/4_buscar_e_ordenar.py --modo ambos
```

Etapa 5 — Experimentos comparativos (matriz de configurações × cargas × repetições):
```bash
python 1_scripts/5_experimentar.py
```

Etapa 6 — Tabela consolidada, gráficos dos resultados e consolidação da análise assintótica:
```bash
python 1_scripts/6_gerar_graficos.py
```

Etapa 7 — Análise assintótica do pipeline (item 7.1 do edital):
```bash
python 1_scripts/7_analise_assintotica.py
```

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

## Reprodução

1. Obter ou utilizar os PDFs do diretório `2_corpus/`.
2. Preparar o ambiente conforme as seções acima.
3. Executar os comandos do pipeline (etapas 1 a 4), depois os experimentos (etapa 5), a análise assintótica (etapa 7) e, por fim, a consolidação (etapa 6).
4. Conferir os resultados, tabelas, gráficos e dados brutos gerados.

Todas as medições de tempo devem ser feitas no **mesmo ambiente**. Os valores registrados em `relatorio_experimentos.json` e nos gráficos foram obtidos em Windows 11 (AMD64) com Python 3.14.7; misturar máquinas ou versões invalida a comparação entre configurações.

## Corpus

Corpus normativo e orientativo público do PROCC/UFS e normas correlatas. Uso exclusivamente acadêmico.

- **Acesso/download:** 02/09/2026, às 21h10.
- **Quantidade:** 7 documentos, 83 páginas e aproximadamente 4,50 MB.
- **Idioma/formato:** português brasileiro; arquivos PDF.
- **Dados removidos ou anonimizados:** nenhum.
- **Limpeza e normalização:** Unicode NFC, quebras de linha, espaços repetidos e hifenização entre linhas; texto original preservado.
- **Chunking:** janelamento deslizante contínuo de 200 palavras por documento, com overlap de 30 palavras entre chunks consecutivos (passo de 170 palavras). Total de 182 chunks, com média de 196,85 palavras/chunk: 175 chunks atingem a janela cheia de 200 palavras e apenas 7 são menores (o menor tem 64), por serem o último chunk de um documento. Os chunks são extraídos do fluxo contínuo de texto, portanto o overlap de 30 palavras também ocorre entre chunks de uma mesma página; 80 chunks (43,96%) atravessam fronteiras de página.

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

