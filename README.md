[![Open in Colab](https://img.shields.io/badge/Open%20in-Colab-F9AB00?logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Farias_Franzone_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

# Regulamentos acadêmicos e manuais públicos

Corretude, eficiência e recuperação de contexto para IA generativa.

Este README é o manual operacional do repositório. O relatório técnico concentra a fundamentação, as provas, a análise detalhada, os experimentos e a discussão; esta página será atualizada à medida que esses artefatos forem produzidos.

## Relatório técnico

- [Relatório em desenvolvimento](https://docs.google.com/document/d/1RLEssVnXO0mOw0kx70mevGKRufop8sq1oqN-WQzNv2I/edit?usp=sharing)
  
**A PRODUZIR:** adicionar o PDF final do relatório nesta seção quando ele estiver concluído.

## Apresentações

- [Checkpoint — 10/09/2026](https://docs.google.com/presentation/d/1RHaAl9oXhdnzkjwhi0gLFhiCCBeQxHgZQSAyOLu0M_M/edit)
- [Apresentação final — 24/09/2026](https://docs.google.com/presentation/d/1oCvhlEqzGFUmxv-1XzmbMLjySthox-GRHUXjkgRtdVs/edit)

As apresentações estão em desenvolvimento e serão atualizadas com os resultados finais.

## Orquestrador no Google Colab

- [Abrir `orquestrador_pipeline.ipynb` no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Farias_Franzone_Melo_Victor/blob/main/orquestrador_pipeline.ipynb)

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
- `7_resultados/`: relatório consolidado das 12 baterias experimentais (`relatorio_experimentos.json`), tabela consolidada (`tabela_resultados.csv`) e os gráficos dos resultados (`grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png` e `grafico_etapas_pipeline.png`).


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

Etapa 6 — Tabela consolidada e gráficos dos resultados:
```bash
python 1_scripts/6_gerar_graficos.py
```

A Etapa 5 gera `7_resultados/relatorio_experimentos.json` (tabela consolidada das 12 baterias com tempo, pico de memória e status de cada execução). A Etapa 6 lê os relatórios das etapas 1 a 5 e gera `7_resultados/tabela_resultados.csv` mais os gráficos `grafico_tempo_execucao.png`, `grafico_busca_comparativo.png`, `grafico_escalabilidade_merge_sort.png`, `grafico_zipf.png`, `grafico_memoria_configuracoes.png` e `grafico_etapas_pipeline.png`.

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

## Reprodução

1. Obter ou utilizar os PDFs do diretório `2_corpus/`.
2. Preparar o ambiente conforme as seções acima.
3. Executar os comandos do pipeline e dos experimentos.
4. Conferir os resultados, tabelas, gráficos e dados brutos gerados.

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

