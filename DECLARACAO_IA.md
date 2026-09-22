# Declaração de Uso de IA Generativa

Conforme exigido pela **Seção 9** do enunciado da atividade, esta declaração
documenta o uso de IA generativa no desenvolvimento do trabalho, item por item.
O princípio que a orienta é o do próprio enunciado: *"Códigos, provas e análises
sugeridos por IA não serão aceitos sem validação."* Por isso, cada sugestão
listada abaixo é acompanhada do **teste, prova, documentação ou observação**
que a validou — e as sugestões que a validação **reprovou** estão registradas na
Seção 5 com o erro correspondente.

---

## 1. Ferramenta e modelo utilizados

| Item | Descrição |
|---|---|
| Ferramenta | **GitHub Copilot** (extensão para VS Code, modo agente/chat) |
| Modelo | Modelos de linguagem de grande porte disponibilizados pelo GitHub Copilot no período de 02/09/2026 a 23/09/2026 |
| Ambiente de uso | VS Code, sobre o repositório Git do grupo; acesso de leitura/escrita ao *workspace* e execução de comandos no terminal integrado |
| Outras ferramentas de IA | NLTK (biblioteca, para *tokenização*/remoção de stopwords — **não** é IA generativa, é uma dependência do pipeline e está declarada no `requirements.txt`) |

Não foi utilizada nenhuma outra ferramenta generativa (ChatGPT, Gemini, Claude,
Copilot Chat fora do VS Code) para produzir artefatos entregues neste
repositório. Nenhuma credencial, chave ou dado pessoal foi submetida à
ferramenta: todo o material enviado foi código e artefatos já versionados
publicamente no repositório do grupo.

---

## 2. Finalidade de cada uso

| # | Finalidade | Onde o resultado foi aplicado |
|---|---|---|
| F1 | Revisão de *docstrings* e mensagens de erro em português | `1_scripts/*.py` |
| F2 | Apoio à instrumentação de contagem de comparações e movimentações no Merge Sort | `1_scripts/4_buscar_e_ordenar.py:474-542` |
| F3 | Apoio à construção do *benchmark* comparativo contra bibliotecas de referência (`sorted`/Timsort e `heapq.nsmallest`) | `1_scripts/8_avaliar_robustez.py` |
| F4 | Sugestão de redação e estruturação de seções de relatório e documentação técnica | `README.md`, `ANALISE_CORRETUDE_COMPLEXIDADE.md`, `RAG_GENAI.md` |
| F5 | Diagnóstico de falhas de execução (codificação do console, dependências, *timing*) | correções de `PYTHONIOENCODING` e *imports* |
| F6 | Revisão da prova de corretude (invariantes de laço e indução) | `ANALISE_CORRETUDE_COMPLEXIDADE.md`, Seções 3 a 5 |
| F7 | Geração de casos de teste para o módulo de busca e ordenação | `1_scripts/test_etapa_4.py` |

Em **todos** os casos o uso foi de assistência: a IA propôs, e a equipe
executou, mediu, comparou com o resultado esperado e corrigiu.

---

## 3. Até cinco prompts relevantes

> **Nota de transparência:** os prompts abaixo são a transcrição fiel dos
> pedidos feitos durante o desenvolvimento. O trabalho foi conduzido de forma
> iterativa; os cinco foram selecionados por serem os que mais alteraram
> decisões técnicas do projeto.

**Prompt 1 — instrumentação da ordenação**

```
No 4_buscar_e_ordenar.py, preciso que o merge_sort conte separadamente:
número de comparações entre scores, número de desempates por id_chunk,
número de movimentações de elementos e profundidade máxima de recursão.
Mantenha a assinatura atual da função e não use sorted() nem list.sort().
```

**Prompt 2 — comparativo com biblioteca de referência (Seção 5.2, item 5)**

```
Preciso de um script que compare meu merge_sort com implementações de
referência da biblioteca padrão do Python (sorted e heapq.nsmallest),
na MESMA lista de candidatos reais, medindo tempo com time.perf_counter,
e que verifique se a ordem final e o top-k coincidem. Deixe explícito
no resultado se a ordem é idêntica à da referência.
```

**Prompt 3 — bateria de robustez (Seção 7.3)**

```
Preciso medir taxa de falhas e taxa de resultados vazios. Monte uma
bateria de consultas cobrindo: consulta relevante, string vazia, espaços,
pontuação apenas, apenas stopwords, termos fora do vocabulário, e uma
consulta mista. Rode cada uma nas duas configurações de busca e registre
exceções sem interromper a bateria. Exporte tabela CSV.
```

**Prompt 4 — estruturação da prova de corretude (Seção 5.3)**

```
Organize uma justificativa formal de corretude para merge_sort e para
buscar_linear usando invariante de laço e indução forte. Deixe explícito
o que se pretende provar, as hipóteses assumidas, inicialização,
manutenção e terminação, e os limites do argumento.
```

**Prompt 5 — análise de complexidade de espaço**

```
Quero distinguir, na análise assintótica, o espaço auxiliar pico medido
por tracemalloc do total de movimentações de elementos. Explique qual
dos dois corresponde a qual grandeza da análise. Justifique com a
recorrência de espaço.
```

---

## 4. Sugestões aproveitadas

| Sugestão | Como foi validada antes de ser incorporada |
|---|---|
| Contabilizar separadamente comparações de score e desempates por `id_chunk` | A soma passou a fechar com o total: `351 + 18 = 369`. A inconsistência anterior (total registrado igual a 351) foi detectada por essa conferência aritmética e corrigida — ver Seção 6, item E3 |
| Comparar contra `sorted()` **e** `heapq.nsmallest` | Executado sobre os 75 candidatos reais e sobre séries sintéticas de 75 a 4 800 candidatos; em **todas** as 7 ordens de grandeza testadas a ordem final e o Top-5 coincidiram com ambas as referências |
| Usar `key=(-score, id_chunk)` como ordem total | Verificado contra a definição de ordem total (propriedade antissimétrica e transitiva porque o desempate é o `id_chunk`, que é único no corpus): sem empates não resolvidos em 18 empates de score reais |
| Bateria de robustez com 9 classes de consulta, incluindo as patológicas | Executada: 18 execuções, 0 exceções. O resultado de 5 vazios confirmou-se **intencional** (todas as 5 são consultas patológicas por construção) |
| Modelo RAM com parâmetros explícitos (`N`, `L`, `m`, `k`, `n_c`, `Q`, `V`, `r`) | Cada parâmetro foi conferido contra os valores reais dos artefatos (N = 182, L = 37 269, avgdl = 204,7747, m = 3 ou 5, k = 5, V = 4 061) |
| Distinguir espaço auxiliar (pico `tracemalloc`) de movimentações totais | Verificado no código: `tracemalloc.start()` é chamado imediatamente antes de `merge_sort` (`4_buscar_e_ordenar.py:667`), logo o pico medido é auxiliar. O valor de 472 movimentações, por outro lado, é a soma das profundidades (6,29 × 75) |
| Reexecutar os gráficos com o rótulo correto da unidade de trabalho | `tabela_resultados.csv` passou a registrar "351 comparações de score + 18 desempates por id_chunk" em vez de "369 comparações de score" |

---

## 5. Sugestões corrigidas ou rejeitadas

| # | Sugestão | Decisão | Motivo |
|---|---|---|---|
| R1 | Medir o tempo das configurações disparando **subprocessos** (`python 4_buscar_e_ordenar.py ...`) e cronometrar o processo | **Rejeitada e revertida** | O custo fixo de *startup* do interpretador e do `import nltk` (~920 ms) dominava completamente o tempo medido (~41 ms de trabalho real). Isso **inverteu o ranking** das configurações. Reimplementado com medição *in-process* |
| R2 | Usar `sorted()` nos gráficos para gerar a curva de escalabilidade | **Corrigida** | Contraria a exigência da Seção 5.2 de comparar a implementação **da equipe** com a biblioteca de referência, e não substituir uma pela outra. Passou-se a chamar `merge_sort` da equipe e a medir as comparações |
| R3 | Afirmar que a Etapa 5 já mede "análise de falhas, consultas nulas e estabilidade temporal" | **Corrigida** | A Etapa 5 apenas registra exceções por execução. A taxa de falhas e de resultados vazios é produzida na Etapa 8. A *docstring* foi corrigida para não sobredeclarar |
| R4 | Usar `pytest --benchmark` ou uma biblioteca de *benchmarking* externa | **Rejeitada** | Introduziria dependência nova sem necessidade; a medição com `time.perf_counter` em mediana de 5 repetições é suficiente e mais transparente para auditoria |
| R5 | Contar a comparação de desempate apenas uma vez no total | **Corrigida** | Cada comparação de `id_chunk` também é uma comparação executada pelo algoritmo e deve entrar em `comparacoes_totais`. A versão anterior subcontava o total, produzindo o artefato inconsistente `351` |
| R6 | Arredondar/limitar as casas decimais dos tempos nos relatórios JSON | **Rejeitada** | Prejudicaria a reprodutibilidade e a análise dos expoentes log-log da Etapa 7 |
| R7 | Gerar o `package-lock.json` apenas como *stub* | **Corrigida** | O arquivo tinha 203 bytes e nome de pacote divergente; era inútil para `npm ci`. Regenerado (87 674 bytes) e validado com `npm ci` |
| R8 | Considerar `log₂ n` como anotação em texto sem verificar a codificação de saída do console | **Corrigida** | Em console Windows cp1252 o caractere `₂` quebrava a execução com `UnicodeEncodeError`. Adicionada configuração explícita de saída UTF-8 no script de gráficos |
| R9 | Manter na aplicação web uma métrica **TF-IDF própria**, com tokenizador `/[^\W_]+/u` e sem remoção de stopwords, descrita como equivalente ao BM25 do relatório | **Corrigida** | A verificação no navegador mostrou que o motor divergia dos artefatos: 182 candidatos em vez de 75, 1 100 comparações em vez de 369 e um Top-5 de um único documento em vez de três. Além disso, `\w` em JavaScript é ASCII-only, de modo que `critérios` era tokenizado como `crit` + `rios` e termos acentuados não eram encontrados. O motor foi reescrito para reproduzir `4_buscar_e_ordenar.py` com paridade numérica — ver Seção 6, item E11 |

---

## 6. Erros identificados (e como foram detectados)

| # | Erro | Como foi detectado | Correção aplicada |
|---|---|---|---|
| E1 | **Inversão do ranking de configurações por erro de medição**: *timing* por subprocesso dominado por ~920 ms de `import nltk` | Comparação entre tempo total do subprocesso e tempo interno medido pelo próprio script (≈41 ms) revelou discrepância de 20× | Medição reescrita *in-process* (`1_scripts/5_experimentar.py`); ranking recalculado |
| E2 | **Erro de instrumentação de 0,0006 ms** na medição de uma operação, com magnitude comparável ao próprio valor medido | Verificação de sanidade: um tempo reportado era menor que a resolução efetiva do `perf_counter` no ambiente | Medição substituída por mediana de 5 repetições; valor revalidado |
| E3 | **Artefato da Etapa 4 internamente inconsistente**: `num_comparacoes_totais = 351` enquanto `num_comparacoes_score = 351` **e** `num_comparacoes_id_chunk = 18` | Conferência aritmética cruzada dos campos do próprio JSON, exigida pelo enunciado ("coerência entre análise formal e experimento") | O artefato commitado era gerado por código anterior que não incrementava o total no ramo de desempate. Artefatos regenerados: `num_comparacoes_totais = 369` |
| E4 | **Explicação errada do 351 vs 369** no `README.md` (atribuía a diferença a outra causa) | Regeneração do artefato com o código atual mostrou que a diferença era o contador de desempate, não o que o README descrevia | Parágrafo do `README.md` reescrito; `ANALISE_CORRETUDE_COMPLEXIDADE.md` atualizado com a explicação correta (3 resultados de comparação por desempate) |
| E5 | **Números de tempos desatualizados** no `README.md` após a correção da medição da Etapa 5 | Reexecução da Etapa 5 e comparação campo a campo com o que o `README.md` afirmava | Tabelas do `README.md` atualizadas a partir dos artefatos |
| E6 | **`memoria_pico_bytes` não determinístico** (5 408 B em uma execução, valor distinto em outra) | Três execuções consecutivas do mesmo comando produzindo valores diferentes | Medição restrita ao trecho de ordenação com `tracemalloc.start()` imediatamente antes da chamada; valor estabilizado em 1 480 B |
| E7 | **`package-lock.json` inválido** (203 bytes, nome de pacote divergente do `package.json`) | `npm ci` falhou ao tentar resolver as dependências | Arquivo regenerado (87 674 bytes) e `npm ci` revalidado com sucesso |
| E8 | **`UnicodeEncodeError`** no script de gráficos ao imprimir `log₂n` em console cp1252 | Execução do script no terminal padrão do Windows | Configuração explícita de saída UTF-8 (`configurar_saida_padrao()`) |
| E9 | **Afirmação não sustentada** de que a Etapa 5 mede taxa de falhas e estabilidade temporal | Leitura da função `executar_bateria` mostrou que ela apenas registra exceções por execução | *Docstring* corrigida; a medição foi implementada na Etapa 8 e a Seção 7.3 passou a citar a fonte correta |
| E10 | **Rótulo incorreto na tabela de resultados**: "369 comparações de score", quando 369 é o total (score + desempates) | Conferência cruzada entre o CSV gerado e os campos do `relatorio_ordenacao.json` | Rótulo corrigido para "351 comparações de score + 18 desempates por id_chunk" |
| E11 | **Aplicação web divergente do relatório**: métrica TF-IDF própria no lugar do Okapi BM25, sem remoção de stopwords, e tokenizador que separava palavras acentuadas (`critérios` → `crit` + `rios`) | Execução da consulta canônica no navegador (build de produção) e comparação com `6_busca_lexical/candidatos_topk.json`. O app exibia "10 de 182" candidatos e 1 100 comparações, contra 75 e 369 do artefato | `src/utils/searchEngine.ts` reescrito com IDF e TF do BM25 (`k1 = 1,5`, `b = 0,75`), `|D|`/`avgdl` medidos em tokens do texto e `src/utils/stopwords.ts` com as 207 stopwords do NLTK; `src/utils/tokenizer.ts` passou a usar `\p{L}\p{N}` com a flag `u`; `mergeSort` passou a receber comparador com desempate separado, contando 369 comparações. Verificado no navegador: Top-5, scores, 75 candidatos e 369 comparações idênticos ao artefato |

> **Observação importante.** Os erros E1 a E11 são de **instrumentação, medição,
> documentação e portabilidade de linguagem** — não de corretude algorítmica.
> Nenhum deles foi encontrado pelos testes da equipe: foram encontrados por
> **conferência cruzada entre artefatos** (soma de contadores que não fechava,
> tempos incoerentes com a ordem de grandeza do trabalho, valores que mudavam
> entre execuções, resultados do navegador que não coincidiam com o relatório).
> Isso reforça a exigência do enunciado de validar toda sugestão de IA: um
> número gerado por IA só é aceitável depois de verificado contra outra fonte.

---

## 7. Testes, provas, documentação e observações usados para verificação

### 7.1 Suíte automatizada

`1_scripts/test_etapa_4.py` — **14 testes**, executados com
`python -m pytest 1_scripts/test_etapa_4.py`. Cobrem: corretude da ordenação,
critério de desempate, contagem de comparações, *Top-k*, e casos de borda
(lista vazia, `k` maior que o número de candidatos, `k = 1`, empates totais).

### 7.2 Verificação por comparação com implementação de referência

A Seção 5.2, item 5, exige comparar a implementação da equipe com uma biblioteca
de referência declarando o que foi feito **pela equipe**. A verificação é
empírica, não argumentativa: sobre os 75 candidatos reais e sobre séries
sintéticas de 75 a 4 800 elementos, a ordem final e o Top-5 produzidos pelo
`merge_sort` da equipe coincidiram **exatamente** com `sorted()` (Timsort) e com
`heapq.nsmallest`. O *log-log* das contagens de reproduz o expoente esperado
(1,1864 para comparações), o que fecha a coerência entre a análise formal
(`Θ(n log n)`) e o experimento.

### 7.3 Verificação por consistência aritmética entre artefatos

Vários dos erros E1–E10 foram encontrados por conferência de identidades:
`comparacoes_totais = comparacoes_score + comparacoes_id_chunk`;
`num_chamadas_recursivas = 2n − 1` (149 para `n = 75`);
`profundidade_maxima = 1 + ⌈log₂ n⌉` (8 para `n = 75`);
`total_postings = Σ DF` (36 + 3 + 22 + 12 + 17 = 90);
`Σ tamanhos de chunk ≈ 37 269` ocorrências. Nenhuma dessas identidades é óbvia
*o priori* — todas são checagens que a equipe estabeleceu e passou a aplicar aos
artefatos.

### 7.4 Verificação por documentação oficial

| Item verificado | Documentação consultada |
|---|---|
| Fórmula de Okapi BM25 (`k₁`, `b`, `avgdl`) | Referência canônica de *Information Retrieval* e implementações de referência do BM25 |
| Semântica de `heapq.nsmallest` e estabilidade | Documentação oficial do módulo `heapq` da biblioteca padrão |
| Garantia de estabilidade do Timsort | Documentação oficial da função `sorted` |
| Medição de memória com `tracemalloc` | Documentação oficial do módulo `tracemalloc` |
| Teorema Mestre | Material didático da disciplina (Projeto e Análise de Algoritmos) |
| Tokenização e stopwords em português | Documentação oficial do NLTK (`nltk.corpus.stopwords`, lista `portuguese`) |

### 7.5 Reprodutibilidade

Os três artefatos da Etapa 8 (`7_resultados/avaliacao_robustez.json`,
`7_resultados/tabela_robustez.csv`, `7_resultados/tabela_baseline_ordenacao.csv`)
são regeneráveis com semente fixa (`--semente 20260923`) e foram verificados
determinísticos entre execuções. Os valores de tempo são os únicos sujeitos a
variação de máquina, e por isso o `README.md` registra explicitamente o ambiente
de medição.

---

## 8. Contribuição individual dos integrantes

A discriminação detalhada por integrante, por etapa e por artefato encontra-se em
[`CONTRIBUICOES.md`](./CONTRIBUICOES.md). Em resumo:

| Integrante | Foco principal nesta atividade |
|---|---|
| Diego Bispo | Dados/corpus, *notebook* orquestrador, revisão do `README.md` |
| Gabriel Marques | Etapa 4 (busca e ordenação), artefatos de `6_busca_lexical/` |
| Laryssa Santos | Etapas 1–6 (scripts do *pipeline*), testes, aplicação web |
| Kaio Farias | Etapa 4, chunks, *notebook*, revisão do `README.md` |
| Victor Melo | Análise assintótica (Etapa 7), artefatos de resultados, gráficos, infraestrutura e integração |

> **Campos para preenchimento pela equipe antes da entrega.** A lista de
> prompts da Seção 3 é a transcrição dos pedidos efetivamente feitos, mas cada
> integrante deve **confirmar e, se necessário, completar** as contribuições da
> Seção 8 com os itens não rastreados por Git (redação do relatório, gravação do
> vídeo, preparação dos *slides*). Esta confirmação é obrigatória porque o
> enunciado exige a declaração assinada pela equipe, e a atribuição por commits
> cobre apenas a parte versionada do trabalho.
