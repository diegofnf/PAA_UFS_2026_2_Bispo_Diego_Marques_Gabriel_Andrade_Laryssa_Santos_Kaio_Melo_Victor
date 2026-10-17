# PAA — Atividade 2 — Seleção de contexto com orçamento de tokens

Responsáveis:
- Etapa 1 (Ingestão e tokenização): Diego Bispo.
- Etapa 2 (Especificação e baseline guloso): Kaio Santos.
Trilha A: seleção de contexto por mochila 0/1 com orçamento de tokens.
Esta etapa implementa a seleção gulosa (baseline); a programação dinâmica e o
benchmark comparativo pertencem às próximas etapas.

## Relatório técnico

- [Relatório da AV2](https://docs.google.com/document/d/1cFoJsM_uP5D8M5gXjQQlGoIUPa56ldwupIIRD0V7Y_8/edit)

## Vídeo da atividade

Vídeo da AV2 a publicar.

## Apresentação

- [Apresentação da AV2](https://docs.google.com/presentation/d/1FjPmWpVQE1aJELaLnQo0peaQ_8FZfcmRb1jCor3uHu0/edit)

## Orquestrador

- [Abrir no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/av2/av2/orquestrador_av2.ipynb)

## Estrutura

```text
av2/
├── 1_scripts/              # Preparação, testes e validação do notebook
├── 2_dados_tokenizados/    # Corpus com custos e scores associados
├── 3_instancias/           # Entradas para os seletores, com capacidades W
├── 4_selecao_contexto/     # Reservada para as saídas dos seletores
├── 5_resultados/           # Relatórios e resultados das execuções
├── 6_evidencias/           # Notebook executado, testes e versões
├── orquestrador_av2.ipynb
├── requirements.txt
├── requirements-validacao.txt
└── README.md
```

O fluxo dos dados segue a numeração: tokenização → instâncias → seleção →
resultados. Os scripts executam o fluxo e as evidências registram sua validação.
`4_selecao_contexto/` está reservada e contém apenas `.gitkeep`, para aparecer
no GitHub mesmo sem resultados. O corpus original continua em `../av1/`.
Os comandos abaixo partem da raiz do repositório.

## Organização no GitHub

O repositório permanece o mesmo. A branch compartilhada **`av2`** concentra o
desenvolvimento da segunda atividade. A `main` e a tag existente `av1-entrega`
são preservadas durante esse desenvolvimento. Cada etapa concluída recebe um
commit na `av2`; não criamos uma tag de entrega final para uma etapa parcial.
Ao concluir e validar a atividade inteira, a equipe integra `av2` à `main` e
cria a tag `av2-entrega`.

```bash
git clone --branch av2 https://github.com/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor.git
```

Para uma cópia existente, após guardar eventuais alterações locais:

```bash
git fetch origin
git switch av2
git pull --ff-only
```

## Reprodução

Na raiz do repositório, com Python 3.10 ou superior:

```bash
# Etapa 1: Ingestão, tokenização e preparação das instâncias (Diego Bispo)
python -m pip install -r av2/requirements.txt
python av2/1_scripts/preparar_instancias.py
python -m pip install pytest
python -m pytest av2/1_scripts/test_preparar_instancias.py -q

# Etapa 2: Seleção de contexto por baseline guloso (Kaio Santos)
python av2/1_scripts/selecionar_guloso.py
python av2/1_scripts/test_selecionar_guloso.py
```

O comando padrão funciona com os artefatos já versionados da AV1. Não executa
extração, chunking, indexação, busca ou chamadas a LLM. A primeira carga do
tokenizer pode baixar seu vocabulário; execuções posteriores usam o cache local.
Não exige chave de API. Para Colab, utilize o
[notebook exclusivo da AV2](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/av2/av2/orquestrador_av2.ipynb)
e execute todas as células. Ele clona explicitamente a branch `av2`, instala
as dependências, prepara os dados e roda os testes.

## Continuidade da AV1

Reutilizamos os 7 PDFs institucionais, o pré-processamento, os 182 chunks em
`av1/4_chunks/chunks.json` e os candidatos completos da busca indexada em
`av1/6_busca_lexical/candidatos_busca.json`. O caso versionado contém 75 candidatos
com BM25 positivo para a consulta registrada no próprio arquivo. `v_i` é esse
score, inclusive o arredondamento da AV1; não é uma avaliação humana nem uma
medida direta de cobertura. Não usamos `candidatos_topk.json`, pois limitar os
itens antes da mochila mudaria o problema.

A tag `av1-entrega` aponta para `34e06aaa63a0d50f1ad634861d3a40476894df96`.
A base utilizada nesta implementação é
`1cdf6cf5463a178d7679a58e83237fc75f2def6d`. São referências distintas e ambas
são registradas. Nenhum script, corpus ou resultado da AV1 é regravado pela
preparação. Textos, IDs, ordem, documentos e páginas são preservados; a AV2
acrescenta somente `w_i` e `v_i` nas cópias em `av2/2_dados_tokenizados/` e `av2/3_instancias/`.

Chunks ausentes da recuperação recebem `v_i = 0` no corpus tokenizado. Apenas
itens com score positivo e custo positivo seguem para as instâncias. Textos
iguais com IDs distintos permanecem como itens distintos, preservando a AV1;
redundância deve ser avaliada nos experimentos. IDs repetidos são rejeitados.

## Tokenizer e orçamento

Decisão metodológica para esta entrega: `tiktoken==0.14.0`, encoding
`cl100k_base`, método `encode_ordinary`. O encoding fixo permite comparar os
dois seletores sob a mesma unidade de custo, sem depender de uma API paga.
Não há modelo de LLM definido nesta etapa. `w_i` é a quantidade exata de tokens
do texto original de cada chunk para **esse encoding**, sem substituir palavras
por uma estimativa e sem aplicar nova normalização. Marcadores especiais que
apareçam no texto são tratados como texto comum.

`W` representa o orçamento disponível para a **soma dos custos individuais dos
chunks**, nos valores 512, 1024, 2048 e 4096. Não é o tamanho completo da janela
de uma LLM. Instruções, consulta, citações, separadores, mensagens e resposta
exigem espaço adicional. A concatenação pode alterar a tokenização nas bordas;
a etapa de integração deve contar novamente o prompt final com o tokenizer do
modelo escolhido. Se o tokenizer mudar, regenerar todas as instâncias dos dois
algoritmos. Referência: [documentação oficial do tiktoken](https://github.com/openai/tiktoken).

## Contrato dos arquivos de saída

| Arquivo relativo a `av2/` | Conteúdo |
|---|---|
| `2_dados_tokenizados/chunks_tokenizados.json` | Todos os chunks, com origem/texto intactos, `w_i` inteiro e `v_i` numérico. |
| `3_instancias/instancias.json` | Lista comum `itens` e quatro `instancias`, com `W` e `ids_itens`. |
| `4_selecao_contexto/selecao_gulosa.json` | Chunks selecionados para cada capacidade $W$, tokens usados e saldo de $W$. |
| `5_resultados/relatorio_preparacao.json` | Contagens, tempos, ambiente, consulta, tokenizer e proveniência da Etapa 1. |
| `5_resultados/relatorio_guloso.json` | Resumo executivo, aproveitamento de $W$, relevância total e tempos da Etapa 2. |

Os seletores devem carregar `itens` por `id_chunk` e, em cada cenário, usar os
IDs em `ids_itens` e a capacidade `W`. Todos os cenários utilizam a mesma lista
de candidatos. Itens maiores que `W` continuam na entrada, são contados no
relatório e devem ser descartados pela regra de viabilidade dos seletores.
Orçamento zero e listas vazias são válidos; capacidade negativa, IDs repetidos,
scores negativos/não finitos, origem inválida e candidatos que não conferem com
os chunks provocam erro. Contagens de corpus divergentes entre os metadados
da busca e dos chunks também são rejeitadas. O script valida tudo antes de
gravar resultados.

Cada saída registra hashes SHA-256 das entradas e do preparador, commit da
execução, commit da tag AV1 e estado de alterações locais antes da gravação.
As evidências da entrega são geradas de uma cópia limpa do commit da implementação;
um segundo commit guarda os artefatos obtidos. Isso evita atribuir os resultados
à base da AV1, que ainda não continha este código. Os dados das instâncias são
determinísticos para os mesmos arquivos, tokenizer e parâmetros. Os tempos e a
data do relatório variam por execução. Arquivos padrão são regenerados a cada
execução; para guardar outra consulta/tokenizer, use uma pasta base de saída própria. `--saida` recebe a pasta base e cria
dentro dela `2_dados_tokenizados/`, `3_instancias/` e `5_resultados/`:

```bash
python av2/1_scripts/preparar_instancias.py --candidatos caminho/candidatos_completos.json --saida caminho/outra_execucao
```

O arquivo de candidatos precisa ser a saída completa da busca AV1, com as chaves
`metadados` e `candidatos`, consulta, métrica e `total_candidatos` corretos. Não
misturar scores de consultas diferentes. Para gerar nova busca com o script da
AV1, direcione **todas** as saídas para a AV2, preservando os resultados antigos:

```bash
python av1/1_scripts/4_buscar_e_ordenar.py --chunks av1/4_chunks/chunks.json --indice av1/5_indexacao/indice_invertido.json --consulta "requisitos de matrícula" --modo indexada --saida-candidatos av2/3_instancias/candidatos_matricula.json --relatorio-busca av2/5_resultados/busca_matricula.json --saida_candidatos_ordenados av2/3_instancias/ordenados_matricula.json --saida_candidatos_top_k av2/3_instancias/topk_matricula.json --relatorio-ordenacao av2/5_resultados/ordenacao_matricula.json
python av2/1_scripts/preparar_instancias.py --candidatos av2/3_instancias/candidatos_matricula.json --saida caminho/execucao_matricula
```

Essa opção requer também as dependências da AV1 (`av1/requirements.txt`). Ela não é
necessária para reproduzir o caso padrão já versionado.

## Custos: RAM, tokenização e I/O

O relatório separa leitura/decodificação/hash das entradas, validação/associação
dos scores, carregamento do tokenizer, **tokenização**, montagem das instâncias
e serialização/gravação dos dados. O campo `tokenizacao_ram` mede exclusivamente
a fase de contagem/registro dos custos, sem leitura dos arquivos, carregamento
do tokenizer ou validação dos candidatos. O total informado termina antes da gravação
do próprio relatório. O carregamento inicial do tokenizer pode incluir rede.
Esses tempos são evidências de preparação, **não** resultados do benchmark de
seleção. A fase medida inclui a criação dos registros com `w_i`; não é uma
microanálise das operações internas do BPE.

Sejam `N` os chunks, `M` os candidatos, `L` o volume de texto e `B` o número de
orçamentos. A associação usa dicionários e custa O(N + M) operações esperadas,
mais a comparação dos textos de candidatos. A tokenização tem o custo da
implementação BPE sobre os textos, medido separadamente; não assumimos que
o tokenizer realiza uma operação RAM por palavra. Construir as listas de IDs
custa O(BM). Guardamos os textos e metadados em O(L + N + M + BM), além da
memória do tokenizer e da lista temporária de tokens do maior chunk. Leitura e
serialização percorrem os bytes dos arquivos e são contabilizadas à parte.

## Verificação e limites

Para reproduzir também a regressão da AV1 e a execução do notebook em um kernel
Jupyter real, instale as dependências de validação:

```bash
python -m pip install -r av2/requirements-validacao.txt
python av2/1_scripts/validar_notebook.py --saida caminho/notebook_executado.ipynb
```

O workflow `.github/workflows/av2-etapa1.yml` executa esse mesmo procedimento
em Linux e guarda notebook executado, resultados e testes como artefatos.
Veja a [matriz de testes e evidências](6_evidencias/README.md).

A suíte cobre contagem conhecida, não mutação, vazio/sem correspondência,
fronteiras de orçamento, empate, textos duplicados com IDs distintos, entrada
grande/Unicode/marcador especial, IDs inválidos, scores inválidos, candidato
desatualizado e execução integrada nos dados reais. Essas verificações não são
uma prova de corretude dos algoritmos de seleção, ainda não implementados.
Os quatro valores de W também não substituem as duas escalas e as repetições
exigidas no futuro benchmark. Há uma única consulta no caso padrão; ampliar as
consultas e medir redundância/qualidade é trabalho das próximas etapas.

## Resultados da preparação

Foram preparados 182 chunks de 7 documentos e 75 candidatos positivos. O corpus
tokenizado soma 74.055 tokens, incluindo sobreposições. As quatro capacidades
são 512, 1024, 2048 e 4096. Em W = 512, um candidato excede sozinho a capacidade.

Foram aprovados 48 testes: 34 da preparação e 14 de regressão da AV1. Para
executá-los juntos, após instalar `av2/requirements-validacao.txt`:

```bash
python -m pytest av2/1_scripts/test_preparar_instancias.py av1/1_scripts/test_etapa_4.py -q
python av2/1_scripts/test_selecionar_guloso.py
```

## Resultados da seleção gulosa (Etapa 2 — Kaio Santos)

A Etapa 2 implementa o baseline da heurística gulosa com ordenação por densidade de relevância ($r_i = v_i / w_i$) e desempate determinístico quádruplo (`-r_i`, `-v_i`, `w_i`, `id_chunk`).

A varredura contínua garante que itens não sejam descartados precipitadamente: ao encontrar um chunk que excede o saldo restante de $W$, o algoritmo o ignora e segue avaliando os itens subsequentes menores.

| Capacidade $W$ | Chunks Selecionados | Tokens Utilizados | Saldo de $W$ | Taxa de Ocupação | Relevância Acumulada | Chunks Escolhidos |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **$W = 512$** | 1 | 370 / 512 | 142 tokens | 72,27% | 9,6206 | `chunk_0131` |
| **$W = 1024$** | 2 | 761 / 1024 | 263 tokens | 74,32% | 16,6484 | `chunk_0131`, `chunk_0018` |
| **$W = 2048$** | 5 | 1905 / 2048 | 143 tokens | 93,02% | 33,8168 | `chunk_0131`, `chunk_0018`, `chunk_0176`, `chunk_0022`, `chunk_0139` |
| **$W = 4096$** | 10 | 3820 / 4096 | 276 tokens | 93,26% | 57,5855 | `chunk_0131`, `chunk_0018`, `chunk_0176`, `chunk_0022`, `chunk_0139`, `chunk_0119`, `chunk_0178`, `chunk_0136`, `chunk_0066`, `chunk_0138` |

- **Complexidade no Modelo RAM:** Tempo $\mathcal{O}(n \log n + B \cdot n) = \mathcal{O}(n \log n)$ com $n=75$ e $B=4$; espaço auxiliar $\mathcal{O}(n)$.
- **Tempo medido em RAM:** ~0,0005 segundos (sub-milissegundo).
- **Testes automatizados:** 9 testes unitários aprovados em `av2/1_scripts/test_selecionar_guloso.py`.

