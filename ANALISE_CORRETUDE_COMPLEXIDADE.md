# Corretude, modelo RAM, casos e recorrências

Este documento responde às Seções **5.3** (corretude), **6.1** (modelo RAM e
operações elementares), **6.2** (melhor, pior e caso médio), **6.3**
(recorrências) da atividade e ao entregável **10 §10, item 8** ("prova ou
justificativa de corretude").

Toda referência de código aponta para
[`1_scripts/4_buscar_e_ordenar.py`](./1_scripts/4_buscar_e_ordenar.py), que é o
artefato que implementa a busca e a ordenação. As contagens citadas vêm dos
artefatos commitados (`6_busca_lexical/relatorio_ordenacao.json`,
`7_resultados/avaliacao_robustez.json`) e são reprodutíveis pelos comandos do
README.

---

## 1. Definição formal do problema

**Entrada.** Uma tupla `(C, q, k, metrica, k1, b)`, em que:

- `C = {D_1, …, D_N}` é o corpus, uma lista de chunks, com `N = 182`;
- cada `D` tem um identificador globalmente único `D.id_chunk` (p. ex.
  `chunk_0001`) e um texto `D.texto`;
- `q` é a consulta textual;
- `k ∈ ℕ*` é o número de resultados (`k = 5`);
- `metrica ∈ {bm25, simples}` e `k1, b ∈ ℝ` parametrizam a função de relevância.

**Saída.** Uma lista `R` com no máximo `k` chunks de `C`, sem repetição e sem
elementos fora de `C`.

**Função de relevância.** Para `metrica = bm25`:

```
score(D, q) = Σ_{t ∈ T(q)} IDF(t) · TF_BM25(t, D)

TF_BM25(t, D) = freq(t, D) · (k1 + 1) / (freq(t, D) + k1 · (1 − b + b · |D| / avgdl))
IDF(t)        = ln(1 + (N − DF(t) + 0.5) / (DF(t) + 0.5))
```

em que `T(q)` é o conjunto de termos distintos de `q` **após** a remoção de
stopwords, `DF(t)` é o número de chunks que contêm `t` e `avgdl` é o
comprimento médio dos chunks em tokens.

Para `metrica = simples`: `score(D, q) = Σ_{t ∈ T(q)} freq(t, D)`, sempre um
inteiro não negativo.

**Critério de ordenação.** Defina a relação binária `≺` sobre candidatos:

```
x ≺ y  ⟺  score(x) > score(y)  ∨  ( score(x) = score(y) ∧ id_chunk(x) < id_chunk(y) )
```

`≺` é uma **ordem total estrita** sobre qualquer conjunto de chunks distintos,
porque `id_chunk` é único e funciona como desempate irreflexivo. Note que
`score(x) = score(y) ∧ id_chunk(x) < id_chunk(y)` é o único desempate adotado;
como os identificadores nunca coincidem, não há par de elementos
"equivalentes" e a saída é, portanto, **única** (não apenas estável).

**Pré-condições.**

1. Todo `D ∈ C` possui `id_chunk` distinto e não vazio.
2. Se `metrica = bm25`, `avgdl > 0` (garantido por `N ≥ 1` e por pelo menos um
   chunk com texto não vazio).
3. Se `metrica = bm25`, `k1 ≥ 0` e `0 ≤ b ≤ 1`.
4. Os scores dos candidatos são comparáveis entre si, isto é, foram calculados
   com o mesmo `metrica`, `k1`, `b`, `N` e `avgdl`.

**Pós-condições.**

1. `|R| ≤ k`.
2. `R ⊆ C` e não há identificadores repetidos em `R`.
3. Para todo `D ∈ R`, `score(D, q) > 0` (o conjunto de candidatos exclui os
   chunks irrelevantes, conforme o filtro `score_final > 0` executado antes da
   ordenação).
4. Se `C_q = {D ∈ C : score(D, q) > 0}` e `|C_q| ≥ k`, então `R` é formado pelos
   `k` elementos mínimos de `C_q` segundo `≺`; se `|C_q| < k`, então
   `R = C_q` (ordenação total).
5. `R` está ordenado de forma não crescente por `score`, com empates resolvidos
   por `id_chunk` crescente.

**Casos de borda explicitados.**

| Caso | Comportamento exigido | Comportamento implementado |
|---|---|---|
| `q` vazia ou só stopwords | não lançar exceção; retornar lista vazia com aviso | `buscar_linear`/`buscar_indexada` retornam `([], metricas)` com o campo `aviso` |
| Nenhum termo de `q` no vocabulário | lista vazia, `Q = 0` postings | `candidatos = []`, `total_postings_consultadas = 0` |
| `k > |C_q|` | retornar todos os candidatos disponíveis | `selecionar_topk` usa `candidatos_ordenados[:k]`, que satura no tamanho da lista |
| `C_q = ∅` | lista vazia | `merge_sort([])` devolve `[]`; Top-k devolve `[]` |
| Empate de `score` | desempate determinístico | comparação de `id_chunk` dentro de `merge` |
| `N = 0` | `avgdl = 0`, sem divisão por zero | `calcular_estatisticas_corpus` devolve `avgdl = 0.0`; `calcular_tf_bm25` trata `avgdl ≤ 0` |

**Hipótese sobre os dados.** Não se assume distribuição específica para os
tamanhos dos chunks nem para a ordem de chegada dos candidatos: todos os
limites abaixo são de pior caso, e a análise de caso médio é explicitamente
condicionada a um modelo de permutação aleatória dos scores (§4.2).

---

## 2. Panorama dos algoritmos

| # | Algoritmo | Papel no projeto | Arquivo / função |
|---|---|---|---|
| A1 | Busca linear | Configuração 1 (baseline) | `buscar_linear` (linha 212) |
| A2 | Busca indexada por postings lists | Configuração 2 | `buscar_indexada` (linha 347) |
| A3 | `merge` + Merge Sort | Configuração 3 (divisão e conquista) | `merge` (474), `merge_sort` (521) |
| A4 | Seleção do Top-k | Pós-processamento | `selecionar_topk` (550) |

---

## 3. Justificativa de corretude

### 3.1 O que se deseja provar

> **Teorema.** Para toda entrada que satisfaça as pré-condições da Seção 1, o
> procedimento
> `R = selecionar_topk(merge_sort(C_q, metricas), k)` devolve uma lista que
> satisfaz as pós-condições 1 a 5.

O argumento é decomposto em três lemas independentes — (i) `merge` intercala
corretamente, (ii) `merge_sort` ordena corretamente e (iii) `selecionar_topk`
devolve o prefixo correto — mais a prova de que `C_q`, produzido por
`buscar_linear`/`buscar_indexada`, é exatamente o conjunto dos chunks com
`score > 0` (Seção 3.4).

### 3.2 Lema 1 — corretude da intercalação (`merge`, linha 474)

Sejam `E` e `D` duas listas já ordenadas segundo `≺` e sejam `m = |E|`,
`n = |D|`. O procedimento `merge` preenche `resultado` com os `m + n` elementos
de `E ∪ D` em ordem `≺`-crescente.

**Invariante de laço.** No início de cada iteração do laço principal:

> **I1.** `resultado` contém exatamente `{E[0], …, E[i−1]} ∪ {D[0], …, D[j−1]}`,
> nessa ordem, e está ordenado segundo `≺`.
> **I2.** Todo elemento já movido para `resultado` precede, segundo `≺`, todo
> elemento ainda não movido de `E[i..m−1] ∪ D[j..n−1]`.

*Inicialização.* Antes da primeira iteração, `i = j = 0` e `resultado = []`. O
conjunto `{E[0],…,E[−1]} ∪ {D[0],…,D[−1]}` é vazio, logo I1 vale; I2 é
vacuamente verdadeira porque não há elemento movido.

*Manutenção.* Suponha I1 e I2 válidas no início de uma iteração com `i < m` e
`j < n`. Como `E` está ordenado e `E[i]` é o primeiro elemento não movido de
`E`, `E[i]` é `≺`-mínimo do sufixo `E[i..m−1]`; pelo mesmo motivo `D[j]` é
`≺`-mínimo de `D[j..n−1]`. O procedimento executa a primeira comparação
(contador `comparacoes_score`):

- se `score(E[i]) > score(D[j])`, então `E[i] ≺ D[j]`. Para todo
  `D[j']` com `j' ≥ j` temos `D[j] ⪯ D[j']` e, como `id_chunk` desempata de
  forma total, `E[i] ≺ D[j']`. Resta comparar `E[i]` com os demais elementos de
  `E`, que são `⪰ E[i]`. Logo `E[i]` é o `≺`-mínimo do conjunto não movido e,
  por I2, também é `⪰` que todos os já movidos. Anexar `E[i]` e incrementar `i`
  preserva I1 (a ordem é mantida) e I2 (o novo movido é mínimo do remanescente).
- se `score(E[i]) < score(D[j])`, o argumento é simétrico.
- se `score(E[i]) = score(D[j])`, executa-se a **segunda** comparação (contador
  `comparacoes_id_chunk`) e anexa-se o elemento de menor `id_chunk`. Como
  `id_chunk` é único e `score` é igual, o anexado é `≺`-mínimo do conjunto não
  movido: qualquer outro elemento tem score menor (e é posterior) ou score
  igual com `id_chunk` maior. I1 e I2 são preservadas.

*Término.* O laço principal encerra quando `i = m` ou `j = n`, pois cada
iteração incrementa `i` ou `j`. Nesse ponto I1 garante que `resultado` contém um
prefixo de `E` e um prefixo de `D` em ordem, e I2 garante que todo o conteúdo já
depositado precede o que resta. Os dois laços finais (linhas 501–510) copiam o
sufixo remanescente, que já está ordenado por hipótese. Logo, ao término,
`resultado` é a intercalação ordenada de `E` e `D`. ∎

*Complexidade do laço.* O laço principal executa no máximo `m + n − 1`
iterações; cada iteração move exatamente um elemento, e os laços finais movem o
resto, totalizando exatamente `m + n` movimentações (`metricas["movimentacoes"]`).
O número de comparações de score é igual ao número de iterações e, portanto,
fica no intervalo `[min(m,n), m+n−1]`.

### 3.3 Lema 2 — corretude do Merge Sort (`merge_sort`, linha 521)

> **Lema 2.** Para toda lista `L` de candidatos com `id_chunk` distintos,
> `merge_sort(L)` devolve uma permutação de `L` ordenada segundo `≺`.

**Prova por indução forte sobre `n = |L|`.**

*Caso base (`n ≤ 1`).* A linha 537 devolve `L` sem modificação. Uma lista com
zero ou um elemento é, por vacuidade, ordenada; e é trivialmente uma permutação
de si mesma. □

*Passo indutivo.* Seja `n ≥ 2` e suponha o lema verdadeiro para todo
`n' < n`. O procedimento calcula `meio = ⌊n/2⌋` e forma
`E = L[0..meio−1]` e `D = L[meio..n−1]`, com `|E| = ⌊n/2⌋` e
`|D| = ⌈n/2⌉`. Como `n ≥ 2`, ambos os comprimentos são `≥ 1` e estritamente
menores que `n` (pois `⌊n/2⌋ < n` e `⌈n/2⌉ = n − ⌊n/2⌋ < n`). Por hipótese de
indução, `merge_sort(E)` e `merge_sort(D)` devolvem, respectivamente, `E` e `D`
ordenados; e, como as duas chamadas apenas permutam seus argumentos, o conjunto
de elementos devolvidos é o mesmo de `E` e `D`. Pelo Lema 1, `merge` produz a
intercalação ordenada desses dois conjuntos, que é uma permutação de
`E ∪ D = L` em ordem `≺`. □

**Consequência (determinismo e ausência de dependência da ordem de entrada).**
Como `≺` é uma ordem total estrita sobre `L` (Seção 1), existe exatamente uma
permutação ordenada de `L`. O Lema 2 garante que `merge_sort` produz uma
permutação ordenada; logo ela é *aquela* permutação, independentemente da ordem
inicial de `L`. O resultado não depende, portanto, nem da ordem de chegada dos
candidatos nem da estabilidade da intercalação — a estabilidade está
implementada (a linha 499 usa `<=`, favorecendo `E`), mas é irrelevante para a
correção, porque o critério de desempate elimina toda ambiguidade. Essa é a
propriedade verificada empiricamente na Etapa 8 (§5).

### 3.4 Prova de que `C_q` é o conjunto dos chunks com `score > 0`

> **Lema 3.** Ao término de `buscar_linear`, a lista `candidatos` contém
> exatamente os chunks `D ∈ C` com `score(D, q) > 0`, cada um no máximo uma vez.

**Invariante de laço (linhas 265–284).** Após a `i`-ésima iteração do laço
`for chunk in chunks`, o dicionário `chunks_com_matches` contém uma entrada para
exatamente os chunks `chunks[0..i−1]` que possuem ao menos um termo de `T(q)`
com frequência `> 0`, e o valor associado a cada entrada é
`(chunk, freqs, doc_len)` com `freqs[t] = freq(t, D)` exato para todo
`t ∈ T(q) ∩ D`.

- *Inicialização:* `i = 0`, `chunks_com_matches = {}` — vacuamente correto.
- *Manutenção:* na iteração `i`, `contagens = Counter(tokenizar(D.texto))` conta
  exatamente as ocorrências de cada token de `D` (`tokenizar` é o mesmo
  tokenizador usado na Etapa 3, garantindo coerência com o índice). O laço
  interno lê `contagens.get(termo, 0)` para cada `termo ∈ T(q)`, portanto
  `freqs[t]` é exato; se `freqs ≠ ∅`, a entrada é inserida. A chave é `cid`
  (único, pela pré-condição 1), de modo que não há duplicatas nem sobrescrita.
- *Término:* ao final do laço, `i = N` e o invariante afirma que
  `chunks_com_matches` cobre exatamente os chunks que casam algum termo.

Segue que `df_map[t] = |{D : t ∈ freqs(D)}|` é exatamente `DF(t)` e, portanto,
que `IDF(t)` está correto (linha 289). O laço das linhas 300–319 calcula
`score` com a fórmula da Seção 1 e anexa a `candidatos` exatamente os elementos
com `score_final > 0`, uma vez cada. ∎

`buscar_indexada` satisfaz o mesmo lema: ela percorre as posting lists de cada
`t ∈ T(q)` e acumula `IDF(t) · TF_BM25(t, D)`; como cada posting traz
`(chunk_id, freq)` e o acumulador é indexado por `chunk_id`, cada chunk aparece
uma única vez e o score final é idêntico ao da busca linear. Essa equivalência
é verificada por testes automatizados (`test_etapa_4.py`) e pela bateria da
Etapa 8, que compara os Top-k das duas configurações em 9 consultas.

### 3.5 Lema 4 — corretude da seleção do Top-k (`selecionar_topk`, linha 550)

> **Lema 4.** Se `L` está ordenada segundo `≺` e `k ≥ 0`, então `L[:k]` é o
> prefixo `≺`-mínimo de `L` com `min(k, |L|)` elementos.

**Prova.** A semântica de fatiamento em Python garante
`L[:k] = ⟨L[0], …, L[min(k,|L|)−1]⟩` quando `k ≥ 0`, e `[]` quando `k = 0`. Como
`L` é `≺`-crescente, `L[0..min(k,|L|)−1]` são precisamente os
`min(k, |L|)` elementos mínimos de `L`. Em particular, se `k ≥ |L|`, o
resultado é `L` inteira, satisfazendo o caso de borda "`k > |C_q|`". ∎

**Prova do Teorema.** Combinando os Lemas 2, 3 e 4: `C_q` é o conjunto dos chunks
com `score > 0` (Lema 3); `merge_sort(C_q)` devolve `C_q` em ordem `≺`
(Lema 2); `selecionar_topk` devolve os `min(k, |C_q|)` menores (Lema 4). Isso
estabelece as pós-condições 1 (tamanho), 2 (pertinência e ausência de repetição,
herdadas de `C_q`), 3 (score `> 0`), 4 (minimalidade) e 5 (ordenação e
desempate). ∎

### 3.6 Hipóteses assumidas, limites do argumento e casos em que a prova não se aplica

1. **Unicidade de `id_chunk` é indispensável.** A totalidade de `≺` depende dela.
   Se dois chunks compartilhassem `id_chunk`, a linha 499 (`<=`) decidiria pelo
   elemento da metade esquerda e o resultado passaria a depender da ordem de
   entrada — a ordenação continuaria correta em relação a um critério *fraco*,
   mas deixaria de ser única. A pré-condição é verificada pela Etapa 2 (busca
   por duplicatas em `4_chunks/chunks.json`) e pela Etapa 8.
2. **Comparabilidade dos scores.** Os Lemas 1 e 2 supõem que todos os candidatos
   foram pontuados com os mesmos parâmetros. Se `merge_sort` recebesse
   candidatos de execuções com `k1`, `b` ou `metrica` diferentes, a relação `≺`
   não seria transitiva e o Lema 2 falharia. É por isso que a Configuração 3
   reordena *os mesmos* candidatos produzidos pela busca indexada, e não uma
   mistura de buscas.
3. **A prova não cobre a qualidade da relevância.** Corretude aqui significa
   "a saída satisfaz as pós-condições", não "os `k` resultados são os
   semanticamente mais relevantes para o usuário". BM25 é uma heurística de
   relevância lexical e a pós-condição 4 é relativa à função de score adotada.
   A avaliação de qualidade exige um conjunto de relevância anotado, que este
   trabalho não possui (ver `RAG_GENAI.md`, Seção 4, e a coluna
   "Precision@k" na Seção 5).
4. **O modelo de contagem não é o modelo de custo.** Os lemas contam
   comparações e movimentações; eles não afirmam nada sobre tempo em segundos,
   que depende do interpretador, das bibliotecas e da hierarquia de memória
   (§4.5).
5. **`calcular_tf_bm25` não é provado aqui.** A função é avaliada sob
   `avgdl > 0` e `denominador > 0`, mas é uma fórmula fechada; sua "corretude" é
   a fidelidade à definição do Okapi BM25, não um teorema. O caso `avgdl = 0` é
   tratado defensivamente devolvendo ajuste nulo.
6. **Empates e o limite inferior de comparações.** Com `≺` total, uma
   comparação de scores tem **três** resultados possíveis (`>`, `<`, `=`), e não
   dois. Por isso as 351 comparações de score medidas em `n_c = 75` podem ficar
   abaixo do limite inferior clássico `⌈log₂ 75!⌉ = 364` para ordenação por
   comparações binárias: o modelo binário não se aplica diretamente quando o
   critério admite empates. A estrutura real dos empates, apurada em
   `6_busca_lexical/candidatos_busca.json`, é: **61 scores distintos em 75
   candidatos**, portanto **14 candidatos compartilham o score com outro**
   (18,67%), distribuídos em **7 grupos** de multiplicidades 5, 3, 3, 3, 3, 2 e
   2. Ao longo das fusões o algoritmo cai **18 vezes** no ramo de igualdade de
   score (cada uma resolvida pelo `id_chunk`), o que explica a decomposição
   exata do contador total: `351 + 18 = 369`. Note que 18 e 14 são grandezas
   distintas — a primeira conta comparações, a segunda conta elementos.

---

## 4. Análise no modelo RAM (§6.1) e casos (§6.2)

### 4.1 Parâmetros da análise

| Símbolo | Significado | Valor no corpus | Definição |
|---|---|---|---|
| `N` | número de chunks do corpus | 182 | `len(chunks)` |
| `L` | total de tokens do corpus | 37 269 ocorrências, 4 061 termos distintos | soma de `len(tokenizar(D.texto))` |
| `\bar{L}` | comprimento médio do chunk | 204,77 tokens | `avgdl` |
| `m` | termos distintos da consulta após stopwords | 3 (execução padrão) ou 5 (consulta do trabalho) | `len(termos_distintos)` |
| `k` | resultados retornados | 5 | argumento `--k` |
| `n_c` | candidatos com `score > 0` | 75 (carga 1) / 32 (carga 2) | `len(candidatos)` |
| `Q` | postings consultadas pela busca indexada | 90 | `total_postings_consultadas` |
| `V` | termos no vocabulário do índice | 4 061 | `len(indice_invertido)` |
| `r` | repetições experimentais | 2 (Etapa 5) / 5 (mediana por ponto) | `--repeticoes` |

Custos medidos que alimentam a calibração: `N = 182` chunks, `Q = 90` postings
para a consulta `"critérios para atribuição de bolsas e requisitos de matrícula"`
(`DF` = 36, 3, 22, 12 e 17; soma exatamente 90).

### 4.2 Operações elementares

O modelo RAM adotado assume que um número constante de palavras de memória pode
ser acessado e que cada operação abaixo custa `Θ(1)`.

| Operação elementar | Onde aparece | Contador / evidência |
|---|---|---|
| **Comparação** de scores | `merge` linha 489 | `comparacoes_score` (351) |
| **Comparação** de identificadores | `merge` linha 499 | `comparacoes_id_chunk` (18) |
| **Acesso a vetor/lista** | `E[i]`, `D[j]`, `candidatos[:k]` | — (implícito em comparações e movimentações) |
| **Atribuição/escrita** | `resultado.append(...)`, `freqs[t] = f` | `movimentacoes` (472) |
| **Incremento** | `i += 1`, contadores de métrica | derivado |
| **Chamada recursiva** | `merge_sort` linhas 540–541 | `chamadas_recursivas` (149) |
| **Atualização de estrutura** | `chunks_com_matches[cid] = …`, `contagens.get` | `total_comparacoes_termos` (N · m) |
| **Divisão/fatiamento de vetor** | `candidatos[:meio]`, `candidatos[meio:]` | custo `Θ(meio)`, contabilizado na recorrência |

Para a busca indexada, a operação elementar dominante é o **percurso de uma
posting list**: `total_postings_consultadas = Q`.

Nas três configurações, `N` e `L` são as entradas do modelo; `m`, `k` e `r` são
parâmetros do usuário; `V` e `Q` caracterizam a estrutura de índice construída.

### 4.3 Melhor, pior e caso médio

#### A1 — Busca linear (`buscar_linear`)

O laço das linhas 265–284 **visita sempre os `N` chunks**, independentemente de
a consulta casar ou não. Logo não há separação entre melhor e pior caso no
tempo de varredura:

| | Tempo | Candidatos produzidos |
|---|---|---|
| **Melhor caso** | `Θ(N · (\bar{L} + m))` | `0` (consulta sem nenhum termo no vocabulário) |
| **Pior caso** | `Θ(N · (\bar{L} + m))` | `N` (todos os chunks casam) |
| **Caso médio** | `Θ(N · (\bar{L} + m))` | `E[|C_q|] = N · P(chunk casa a consulta)` |

O pós-processamento (linhas 287–319) custa `Θ(m · |C_q|)` para `df_map` e
`Θ(m · |C_q|)` para os scores. A diferença entre os casos está, portanto, no
**trabalho pós-varredura e no tamanho da saída**, não na varredura.

*Consequência de projeto:* a busca linear é o baseline que demonstra o custo de
não ter índice; seu tempo é proporcional ao corpus mesmo quando a resposta é
vazia. Foi exatamente esse comportamento que a Etapa 8 confirmou (5 consultas
patológicas, todas com 0 candidatos, gastando o mesmo tempo de varredura).

#### A2 — Busca indexada (`buscar_indexada`)

| | Tempo | Justificativa |
|---|---|---|
| **Melhor caso** | `Θ(m)` | nenhum termo de `q` está no vocabulário: apenas `m` buscas em dicionário, `Q = 0` |
| **Pior caso** | `Θ(m · N)` | cada termo de `q` ocorre em todos os `N` chunks |
| **Caso médio** | `Θ(m + Σ_{t∈T(q)} DF(t)) = Θ(m + Q)` | `DF(t)` obtido em `Θ(1)` pelo tamanho da posting list |

No corpus real, `Q = 90 ≪ m · N = 5 · 182 = 910`, o que explica a vantagem de
cerca de 11× da Configuração 2 sobre a Configuração 1: o custo deixa de depender
de `N` e passa a depender de `Q`, o número de postings efetivamente relevantes.
Como `Q` cresce com a fração do corpus que contém os termos consultados (e não
com `N` em si), o comportamento assintótico é `O(1)` *em relação a `N` quando a
consulta é seletiva* — o expoente log-log medido de −0,10 na Etapa 7.

#### A3 — Merge Sort (`merge_sort`)

| | Comparações de score | Movimentações |
|---|---|---|
| **Melhor caso** | `220` (mínimo exato para a árvore de divisão de `n_c = 75`) | `Σ` profundidades `= Θ(n_c log₂ n_c)` |
| **Pior caso** | `n_c·⌈log₂ n_c⌉ − 2^⌈log₂ n_c⌉ + 1 = 398` | idem |
| **Caso médio** | `≈ n_c log₂ n_c − 1,26·n_c ≈ 373` (modelo de permutação aleatória) | idem |
| **Medido (`n_c = 75`)** | **351** de score + 18 de desempate | **472** |

O valor medido (351) cai dentro do intervalo `[220, 398]` e próximo da
estimativa de caso médio, e o mesmo vale em todas as 7 cargas sintéticas da
Etapa 8. O melhor caso alcançável é `Σ_{nós internos} min(|E|, |D|)`, que para
`n_c = 75` vale exatamente 220 — o caso em que as duas metades se intercalam
perfeitamente em todos os níveis. As 472 movimentações são exatamente
`Σ_{D ∈ C_q} profundidade(D)`:
cada elemento é reescrito uma vez por nível de recursão em que participa, o que
para `n_c = 75` (entre `2⁶` e `2⁷`) dá uma média de 6,29 cópias por elemento —
`6,29 × 75 = 472`. Esse é um ajuste exato entre a análise e o artefato.

#### A4 — Seleção do Top-k (`selecionar_topk`)

`Θ(k)` para a cópia do prefixo (independente de `n_c`), com custo espacial
`Θ(k)`. É por isso que a Etapa 7 mede expoente ≈ 0 (−0,017) para esse estágio: o
trabalho não cresce com o tamanho da entrada. Se o projeto exigisse `k` grande
(por exemplo, `k ≈ n_c`), a seleção passaria a ser `Θ(n_c)` e o gargalo voltaria
a ser a ordenação — a divisão e conquista descrita em §5.2 do edital só se paga
quando `k ≪ n_c`.

### 4.4 Complexidade espacial

| Estrutura | Espaço | Observação |
|---|---|---|
| Corpus `C` | `Θ(N · \bar{L})` | 182 chunks, ~37 269 tokens |
| Índice invertido | `Θ(V + L)` | 4 061 termos + 21 530 postings |
| Candidatos `C_q` | `Θ(n_c)` | até `N` no pior caso |
| `merge_sort` — pico auxiliar | **`Θ(n_c)`** | medido: 1 480 bytes para `n_c = 75` |
| `merge_sort` — movimentação total | `Θ(n_c log₂ n_c)` | medido: 472 escritas |
| Top-k `R` | `Θ(k)` | 5 elementos |

A distinção entre as duas últimas linhas de `merge_sort` é o ponto mais
delicado da análise espacial e merece ser explicitada:

- **Pico de memória auxiliar:** em um dado instante, as fatias vivas são a da
  chamada corrente (tamanho `n_c/2^d`) mais as fatias pendentes ao longo do
  caminho de recursão, cuja soma é
  `n_c/2 + n_c/4 + … < n_c`. Logo o pico é `Θ(n_c)` — e isso é exatamente o que
  `tracemalloc` registra (1 480 bytes; `merge` copia **referências**, não
  dicionários, de modo que o custo por elemento é o de um ponteiro).
- **Movimentação total:** cada nível de recursão reescreve a totalidade dos
  elementos, logo o número de escritas é `Θ(n_c log₂ n_c)` – o custo de copiar
  as fatias em `candidatos[:meio]`/`candidatos[meio:]`. Uma implementação com
  vetor auxiliar único (à la CLRS) trocaria esse custo de movimentação por
  `Θ(n_c)` de espaço alocado uma única vez, mas manteria a mesma ordem de
  grandeza assintótica.

O `memoria_pico_bytes` do artefato mede **memória auxiliar alocada dentro da
região cronometrada** (`tracemalloc` é iniciado imediatamente antes de
`merge_sort`), e não o *footprint* total do processo — os candidatos já existiam
antes. O mesmo vale para `pico_memoria_mb` em `relatorio_experimentos.json`.

### 4.5 Fatores não representados pelo modelo RAM

1. **E/S e extração de PDF.** A Etapa 1 depende do PyMuPDF (camada C) para ler
   4,50 MB de PDF; o custo de I/O e de decodificação não é unitário e domina os
   `n` pequenos da varredura log-log (expoente 0,50 para extração).
2. **Hierarquia de memória e representação de objetos.** Um chunk é um `dict`
   Python com 7 campos; `E[i]["score"]` é uma sequência de *ponteiro → dict →
   hash lookup*, isto é, 2 a 3 acessos não contíguos, enquanto o modelo RAM
   presume acesso unitário. Isso explica por que a constante medida é muito
   maior que a prevista.
3. **Bibliotecas e interpretador.** `Counter` (C), `math.log` (C) e
   `tokenizar` sobre `str` têm constantes muito menores que código Python puro.
   O impacto agregado é medido diretamente na Etapa 8: o Timsort nativo
   (`sorted`) gasta **0,0282 ms** para os mesmos 75 candidatos em que o Merge
   Sort da equipe gasta **0,3390 ms** — um fator constante de **≈ 12×**.
   Ambos têm a mesma ordem assintótica (expoentes log-log 1,15 e 1,25), o que
   confirma que a diferença é de constante, não de classe de complexidade. Os
   tempos absolutos variam entre execuções; o fator constante permanece na casa
   de uma ordem de grandeza em todas elas.
4. **Coleta de lixo e alocação.** As ~472 alocações/escritas de `merge` pagam
   custo de gerenciador de memória que o modelo RAM ignora.
5. **Ausência de paralelismo e de embeddings.** Nenhuma etapa usa múltiplos
   núcleos; não há representação vetorial, `d` não existe no modelo, e por isso
   nenhum limite do tipo `Θ(d·n)` se aplica.
6. **Contadores de precisão arbitrária.** Python não tem palavras de tamanho
   fixo: os contadores são `int` de precisão arbitrária. Enquanto os valores
   cabem em poucas palavras de máquina, o custo por incremento é constante; este
   trabalho nunca ultrapassa 2⁶⁴, de modo que a hipótese do modelo se sustenta.
7. **Dicionários e hashing.** `Counter` e os `dict` de frequência têm custo
   médio `Θ(1)` por operação, mas pior caso `Θ(size)` sob colisões. O modelo de
   caso médio da busca indexada depende dessa hipótese.

---

## 5. Recorrências (§6.3)

### 5.1 Recorrência principal: Merge Sort

**Origem de cada termo na implementação concreta.**

```
T(n) = 2·T(⌊n/2⌋) + Θ(n)
```

- **`2·T(⌊n/2⌋)`** — as duas chamadas recursivas das linhas 540 e 541, uma
  sobre `candidatos[:meio]` e outra sobre `candidatos[meio:]`. O fator **2** vem
  literalmente de serem duas chamadas; o argumento `⌊n/2⌋` vem de
  `meio = tamanho // 2` (linha 535) — divisão inteira, daí o piso.
- **`+ Θ(n)`** — o termo de combinação, que aqui tem **duas** fontes explícitas:
  1. `merge` (linha 543) executa exatamente `m + n` movimentações e até
     `m + n − 1` comparações sobre as duas metades, ou seja `Θ(n)` no total;
  2. o **fatiamento** `candidatos[:meio]` e `candidatos[meio:]` copia
     `Θ(n)` referências antes mesmo da primeira chamada recursiva. Se o projeto
     usasse índices `(início, fim)` em vez de fatias, esse segundo componente
     desapareceria — mas o termo `Θ(n)` permaneceria por causa de `merge`.
- **Caso base:** `tamanho <= 1` devolve imediatamente (linha 537), logo
  `T(0) = T(1) = Θ(1)`, o que satisfaz a condição de regularidade do Teorema
  Mestre.

**Resolução.**

`a = 2`, `b = 2`, `f(n) = Θ(n)`. Como
`n^{log_b a} = n^{log₂ 2} = n^1` e `f(n) = Θ(n¹)`, recai-se no **caso 2** do
Teorema Mestre (`f(n) = Θ(n^{log_b a})`), donde:

```
T(n) = Θ(n^{log_b a} · log n) = Θ(n log n)
```

Isso é confirmado empiricamente pelo expoente log-log do tempo
(1,25 para o Merge Sort da equipe, 1,15 para o Timsort como referência) e pelo
expoente do **número de comparações** medido na varredura de escala da Etapa 8:
**1,1864**, próximo de 1 mas com o excedente característico do fator `log n`.
O crescimento é visível na própria tabela: de `n = 75` para `n = 4800`
(64× de aumento) as comparações crescem de 369 para 54 145 (147×), isto é,
pouco mais que 64·log(64) ≈ 64 × 1,4.

**Verificação independente pelo contador de recursão.** A profundidade máxima
registrada é `1 + ⌈log₂ n⌉` (a raiz conta como profundidade 1 e cada nível
adicional divide por 2): para `n_c = 75`, `1 + ⌈log₂ 75⌉ = 1 + 7 = 8`, que é
exatamente o valor de `profundidade_maxima` no artefato. E o número total de
chamadas é `2n − 1` em uma árvore binária completa — o artefato registra
**149** chamadas para `n_c = 75`, e `2·75 − 1 = 149` (para `n_c = 182` seria
363, igualmente `2·182 − 1`). Esse ajuste exato é a assinatura da recorrência
`T(n) = 2T(n/2) + Θ(n)` na implementação.

### 5.2 Recorrência de espaço

O pico de memória auxiliar obedece

```
S(n) = S(⌊n/2⌋) + Θ(n)     →     S(n) = Θ(n)
```

Os `Θ(n)` de cada nível **não se somam ao longo de toda a árvore** (isso daria
`Θ(n log n)`), mas apenas ao longo do **caminho** de recursão, porque as fatias
de um ramo já terminado são liberadas antes de o ramo irmão ser processado. A
soma geométrica `n/2 + n/4 + …` é `O(n)`, o que fecha em `Θ(n)` — o mesmo valor
registrado em `memoria_pico_bytes`.

### 5.3 Alterações para uma variante de seleção particionada

Se o Top-k fosse obtido por particionamento recursivo (Quickselect) em vez de
ordenar tudo, a recorrência passaria a

```
T(n) = T(n/2) + Θ(n)   (caso médio)      →   T(n) = Θ(n)
T(n) = T(n−1) + Θ(n)   (pior caso)       →   T(n) = Θ(n²)
```

com resolução pelo caso 3 do Teorema Mestre no primeiro caso
(`f(n) = Θ(n)`, e `n^{log₂1} = n⁰ = 1`, logo `f(n) = Ω(n^{1+ε})` com
`0 < ε ≤ 1`, e a condição de regularidade `2·f(n/2) ≤ c·f(n)` vale com `c = 1`).
A Configuração 3 adota deliberadamente o caminho `Θ(n log n)` porque o artefato
precisa da **ordenação completa** dos candidatos (`candidatos_ordenados.json`),
e não apenas do Top-k; a seleção, nesse caso, é um corte `Θ(k)`.

---

## 6. Coerência entre análise formal e experimento

| Etapa do pipeline | Predito | Expoente medido (Etapa 7) | Coerente? |
|---|---|---|---|
| Extração de texto | `Θ(P)` em páginas | 0,50 | ruído em `n` pequeno (§4.5, item 1) |
| Normalização | `Θ(L)` | 1,06 | ✓ |
| Chunking | `Θ(L)` | 1,07 | ✓ |
| Indexação | `Θ(L)` | 0,91 | ✓ |
| Busca linear | `Θ(N · (\bar{L}+m))` | 0,78 | ✓ (medição isolada: 1,00/0,96) |
| Busca indexada | `Θ(m + Q)` | −0,10 | ✓ (independente de `N`) |
| Merge Sort | `Θ(n log n)` | 1,29 | ✓ (comparações: 1,19) |
| Seleção Top-k | `Θ(k)` | −0,02 | ✓ (independente de `n`) |

A coluna "predito" vem da Seção 4; a coluna "medido" de
`7_resultados/analise_assintotica.json`. O desvio da extração de texto e da
busca linear em `n` pequeno está discutido na Seção 4.5 e no README.

---

## 7. Verificação empírica da corretude (Etapa 8)

Além da prova, a corretude da ordenação é verificada por **equivalência
posicional contra implementações de referência** em
`7_resultados/avaliacao_robustez.json`:

| Verificação | Resultado |
|---|---|
| Ordem completa da equipe idêntica à de `sorted()` — carga real (75 candidatos) | ✅ idêntica |
| Ordem completa idêntica à de `sorted()` — 7 cargas sintéticas (75 a 4 800) | ✅ idênticas |
| Top-k idêntico ao de `sorted()` (Timsort) | ✅ |
| Top-k idêntico ao de `heapq.nsmallest` | ✅ |
| Top-k da busca linear idêntico ao da busca indexada — 9 consultas | ✅ |
| Exceções não tratadas em 18 execuções | 0 |

A comparação é **posição a posição** sobre a ordem completa, e não apenas sobre
o Top-k, porque dois algoritmos podem coincidir no Top-k e divergir no restante.
Os dados brutos, o script e o comando de reprodução estão em
[`8_avaliar_robustez.py`](./1_scripts/8_avaliar_robustez.py) e
[`7_resultados/avaliacao_robustez.json`](./7_resultados/avaliacao_robustez.json).

O `test_etapa_4.py` complementa a verificação com 14 testes automatizados que
cobrem tokenização, IDF, saturação de TF, normalização por comprimento,
consulta vazia, consulta só de stopwords, termos inexistentes, termos repetidos
e a equivalência linear ≡ indexada.
