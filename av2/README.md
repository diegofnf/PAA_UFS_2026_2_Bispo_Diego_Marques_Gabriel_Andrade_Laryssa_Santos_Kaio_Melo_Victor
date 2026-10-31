# PAA — Atividade 2 — Seleção de contexto com orçamento de tokens

Responsáveis:
- Etapa 1 (Ingestão e tokenização): Diego Bispo.
- Etapa 2 (Especificação e baseline guloso): Kaio Santos.
- Etapa 3 (Programação dinâmica): Diego Bispo e Kaio Santos.
- Etapa 4 (Corretude e benchmark comparativo): Gabriel Marques, com integração dos resultados da equipe.
- Etapa 5 (Complexidade e integração IA): Victor Melo. Integração das seleções,
  orçamento do prompt, deduplicação e análise experimental de tempo, memória e tokens.
Trilha A: seleção de contexto por mochila 0/1 com orçamento de tokens.
Esta etapa implementa a solução exata por programação dinâmica, os testes de
corretude, o benchmark comparativo com o baseline guloso e a montagem do
contexto para LLM.

## Relatório técnico

- [Relatório da AV2](https://docs.google.com/document/d/1cFoJsM_uP5D8M5gXjQQlGoIUPa56ldwupIIRD0V7Y_8/edit)

## Vídeo da atividade

Vídeo da AV2 a publicar. O roteiro e o estado da gravação estão em
[`VIDEO.md`](VIDEO.md).

## Apresentação

- [Apresentação da AV2](https://docs.google.com/presentation/d/1FjPmWpVQE1aJELaLnQo0peaQ_8FZfcmRb1jCor3uHu0/edit)

## Orquestrador

- [Abrir no Google Colab](https://colab.research.google.com/github/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/blob/av2/av2/orquestrador_av2.ipynb)

## Estrutura

```text
av2/
├── 1_scripts/              # Preparação, seletores guloso e PD, testes
├── 2_dados_tokenizados/    # Corpus com custos e scores associados
├── 3_instancias/           # Entradas para os seletores, com capacidades W
├── 4_selecao_contexto/     # Saídas concretas dos seletores (guloso e PD)
├── 5_resultados/           # Relatórios dos seletores e do contexto para LLM
├── 6_evidencias/           # Notebook executado, testes e versões
├── 7_contexto_llm/         # Payloads de chat, tabela e gráficos da Etapa 5
├── integrar_contexto.py    # Ponto de entrada oficial da Etapa 5
├── CONTEXTO_LLM.md         # Análise teórica e experimental da Etapa 5
├── DECLARACAO_IA.md        # Uso crítico de IA generativa
├── CONTRIBUICOES.md        # Contribuição individual
├── VIDEO.md                # Roteiro e URL do vídeo
├── orquestrador_av2.ipynb
├── requirements.txt
├── requirements-validacao.txt
└── README.md
```

O fluxo dos dados segue a numeração: tokenização → instâncias → seleção →
resultados. Os scripts executam o fluxo e as evidências registram sua validação.
O corpus original continua em `../av1/`.
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

# Etapa 3: Seleção ótima por programação dinâmica (Diego Bispo e Kaio Santos)
python av2/1_scripts/selecionar_pd.py
python av2/1_scripts/test_selecionar_pd.py

# Etapa 4: Corretude, benchmark e evidência consolidada (Gabriel Marques)
python av2/1_scripts/gerar_relatorio_corretude.py
python -m pytest av2/1_scripts/test_corretude_limites.py -q

# Etapa 5: Contexto para LLM, orçamento de prompt e análise de tokens (Victor Melo)
python av2/integrar_contexto.py
python -m pytest av2/1_scripts/test_montar_contexto_llm.py -q
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
| `4_selecao_contexto/selecao_gulosa.json` | Chunks selecionados pelo baseline guloso para cada capacidade $W$. |
| `4_selecao_contexto/selecao_pd.json` | Chunks selecionados pela solução ótima por PD para cada capacidade $W$. |
| `5_resultados/relatorio_preparacao.json` | Contagens, tempos, ambiente, consulta, tokenizer e proveniência da Etapa 1. |
| `5_resultados/relatorio_guloso.json` | Resumo executivo, aproveitamento de $W$, relevância total e tempos da Etapa 2. |
| `5_resultados/relatorio_pd.json` | Resumo executivo da PD, relevância máxima atingida e tempos da Etapa 3. |
| `4_selecao_contexto/contraexemplo_guloso.json` | Contraexemplo operacional da suboptimalidade do baseline guloso. |
| `5_resultados/relatorio_corretude_limites.json` | Comparação por orçamento, ganhos de relevância e evidências da Etapa 4. |
| `7_contexto_llm/contextos.json` | Payloads de chat (2 seletores × 4 `W`) na janela de exportação. |
| `7_contexto_llm/tabela_contexto_llm.csv` | Matriz de 160 execuções: tokens, overhead, dedupe, tempo, memória e qualidade. |
| `7_contexto_llm/prompt_exemplo.md` | Prompt legível da PD em `W = 4096`. |
| `7_contexto_llm/grafico_*.png` | Prompt por `W`, folga da janela e latência estimada. |
| `5_resultados/relatorio_contexto_llm.json` | Validação de `w_i`, benchmark dos seletores, resumo por `W` e comparação PD/guloso. |
| `CONTEXTO_LLM.md` | Análise teórica e experimental da Etapa 5. |

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
desatualizado e execução integrada nos dados reais. A suíte específica da
Etapa 4 cobre o contraexemplo guloso, a comparação com força bruta, as
invariantes da reconstrução e a comparação PD versus guloso nos quatro
orçamentos.
Os quatro valores de W não substituem experimentos com múltiplas escalas e
repetições para uma avaliação de desempenho mais ampla. Há uma única consulta
no caso padrão; ampliar as consultas e medir redundância/qualidade permanece
como trabalho futuro.

## Resultados da preparação

Foram preparados 182 chunks de 7 documentos e 75 candidatos positivos. O corpus
tokenizado soma 74.055 tokens, incluindo sobreposições. As quatro capacidades
são 512, 1024, 2048 e 4096. Em W = 512, um candidato excede sozinho a capacidade.

A evidência histórica registra 48 testes da preparação e da regressão da AV1.
Na execução atual das etapas 1 a 3 da AV2, foram aprovados **53 testes**: 34 da preparação, 10
do baseline guloso e 9 da programação dinâmica. O resultado JUnit consolidado
fica em `av2/6_evidencias/testes.xml`.

Opcionalmente, para executar novamente a suíte completa das etapas 1 a 3 e
regenerar a evidência consolidada:

```bash
python -m pytest av2/1_scripts/test_preparar_instancias.py av2/1_scripts/test_selecionar_guloso.py av2/1_scripts/test_selecionar_pd.py -q --junitxml=av2/6_evidencias/testes.xml
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
- **Testes automatizados:** 10 testes aprovados em `av2/1_scripts/test_selecionar_guloso.py`.

## Resultados da seleção por Programação Dinâmica (Etapa 3 — Diego Bispo e Kaio Santos)

A Etapa 3 implementa a solução exata para a Mochila 0/1 via Programação Dinâmica bottom-up com a equação de Bellman e reconstrução dos chunks por backtracking determinístico a partir de $DP[n][W]$.

A garantia matemática de otimalidade global da PD permitiu comprovar empiricamente a superioridade sobre o baseline guloso:

| Capacidade $W$ | Método | Chunks Selecionados | Tokens Utilizados | Saldo de $W$ | Ocupação | Relevância Acumulada | Ganho da PD |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **$W = 512$** | Guloso<br/>**PD** | 1<br/>**1** | 370 / 512<br/>**370 / 512** | 142<br/>**142** | 72,27%<br/>**72,27%** | 9,6206<br/>**9,6206** | Empate<br/>(Ótimo atingido) |
| **$W = 1024$** | Guloso<br/>**PD** | 2<br/>**2** | 761 / 1024<br/>**761 / 1024** | 263<br/>**263** | 74,32%<br/>**74,32%** | 16,6484<br/>**16,6484** | Empate<br/>(Ótimo atingido) |
| **$W = 2048$** | Guloso<br/>**PD** | 5<br/>**5** | 1905 / 2048<br/>**1905 / 2048** | 143<br/>**143** | 93,02%<br/>**93,02%** | 33,8168<br/>**33,8168** | Empate<br/>(Ótimo atingido) |
| **$W = 4096$** | Guloso<br/>**PD** | 10<br/>**11** | 3820 / 4096<br/>**4093 / 4096** | 276<br/>**3** | 93,26%<br/>**99,93%** | 57,5855<br/>**60,3138** | **+2,7283 (+4,7%)**<br/>**Ocupação quase perfeita!** |

- **Complexidade no Modelo RAM:** Tempo $\Theta(n \cdot W)$ e espaço $\mathcal{O}(n \cdot W)$.
- **Tempo medido em RAM:** ~0,147 segundos para todas as 4 instâncias combinadas.
- **Testes automatizados:** 9 testes aprovados em `av2/1_scripts/test_selecionar_pd.py`, cobrindo casos de borda, não mutação, comparação com o baseline e invariantes da reconstrução. O oráculo por força bruta pertence à suíte específica da Etapa 4.

## Corretude e benchmark comparativo (Etapa 4 — Gabriel Marques)

A corretude da programação dinâmica é sustentada pela prova por indução sobre
`DP[i][c]`, pela reconstrução via backtracking e por testes independentes em
instâncias pequenas. O oráculo por força bruta enumera todos os subconjuntos e
confirma o valor ótimo retornado pela PD. Os testes também verificam capacidade,
unicidade dos IDs, pertencimento à entrada e consistência das somas de custos e
benefícios.

O contraexemplo guloso usa capacidade `W = 10` e itens `(w, v) = (6, 30),
(5, 22), (5, 22)`. O guloso obtém 30 ao escolher o primeiro item, enquanto a
PD escolhe os dois últimos e obtém 44. Portanto, a ordenação por densidade não
garante optimalidade na mochila 0/1.

A PD possui tempo `O(N * W)` e espaço `O(N * W)`, sendo pseudo-polinomial em
relação à representação binária de `W`. O baseline guloso possui tempo
`O(N log N)`, mas não oferece garantia de solução ótima.

O notebook oficial executado é
`av2/6_evidencias/notebook_executado.ipynb`; a Etapa 4 foi anexada ao final
sem alterar as células históricas das etapas anteriores. A declaração
individual de uso de IA e a descrição detalhada da prova devem ser inseridas
nas seções 7, 16 e 17 do relatório técnico.

## Contexto para LLM e complexidade (Etapa 5 — Victor Melo)

A Etapa 5 lê as seleções gulosa e PD, verifica cada `w_i` contra
`tiktoken==0.14.0` (`cl100k_base`, `encode_ordinary`), monta o prompt com fontes
`[F1]...`, deduplica a sobreposição de 30 palavras e **reconta o prompt final**.
O `W` da mochila não é tratado como janela da LLM: instruções, resposta e
segurança são reservadas separadamente. A análise completa, com complexidade e
discussão de qualidade, está em [`CONTEXTO_LLM.md`](CONTEXTO_LLM.md).

Resultados principais (janela 8 192, resposta 512, segurança 64, dedupe):

| Seletor | `W` | Chunks | Soma `w_i` | Prompt final | Overhead | Relevância | Relevância/1k |
|---|---:|---:|---:|---:|---:|---:|---:|
| Guloso | 512 | 1 | 370 | 607 | 237 | 9,6206 | 15,85 |
| Guloso | 1 024 | 2 | 761 | 1 033 | 271 | 16,6484 | 16,12 |
| Guloso | 2 048 | 5 | 1 905 | 2 304 | 396 | 33,8168 | 14,68 |
| Guloso | 4 096 | 10 | 3 820 | 4 394 | 623 | 57,5855 | 13,11 |
| PD | 4 096 | 11 | 4 093 | 4 712 | 667 | 60,3138 | 12,80 |

- O overhead do prompt é 237–667 tokens; em `W=512`, ele é 64% do custo dos
  chunks. A concatenação pode alterar a contagem nas bordas (`delta_borda`
  entre +3 e −49 tokens, já considerando a dedupe).
- A deduplicação economiza 57 tokens em `W=4 096`.
- Em 1 024 tokens de janela, nenhum chunk inteiro cabe após as reservas; o
  contexto ajustado fica vazio. A menor janela que comporta a seleção completa
  é 2 048 para `W≤1 024`, 4 096 para `W=2 048` e 8 192 para `W=4 096`.
- Em `W=4 096`, a PD ganha +2,7283 de relevância (+4,7%), mas gasta 318 tokens
  de prompt a mais; em relevância por 1 000 tokens, o guloso é ligeiramente
  melhor (13,11 contra 12,80).
- A PD é bem mais cara: 72,38 ms e 6,72 MB no `W=4 096`, contra 0,08 ms e
  4,06 KB do guloso. A montagem do contexto custa poucas dezenas de ms
  (1–34 ms) e 20–646 KB.

A matriz cobre 2 seletores × 4 `W` × 5 janelas × 2 estratégias × 2 modos de
deduplicação = **160 execuções**. Os 34 testes da Etapa 5 em
`1_scripts/test_montar_contexto_llm.py` somam-se aos 58 anteriores: **92 testes
aprovados** na suíte da AV2.


