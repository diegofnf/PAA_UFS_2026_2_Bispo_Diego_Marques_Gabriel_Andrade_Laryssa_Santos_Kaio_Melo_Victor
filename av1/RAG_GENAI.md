# Relação com IA generativa e RAG

Este documento responde à **Seção 8 (Parte D) — Relação com IA generativa** da
atividade, cobrindo os sete itens exigidos. Todos os números citados são
reprodutíveis pelos artefatos commitados; as referências de arquivo são
indicadas em cada seção.

---

## Contexto do sistema

O pipeline produz um índice invertido sobre 7 documentos normativos do
PROCC/UFS e normas correlatas (83 páginas, 182 chunks de 200 palavras com
sobreposição de 30), pontua candidatos com Okapi BM25 e devolve um Top-k
ordenado. Um sistema RAG usa essa saída como **contexto** para um LLM: a lista
de chunks recuperados é inserida no prompt e o modelo é instruído a responder
somente com base nela.

O limite quantitativo que governa todas as discussões abaixo é: **para `k = 5`,
o contexto recuperado é de exatamente 1 000 palavras — 6 299 caracteres**
(5 chunks de 200 palavras, medidos em `6_busca_lexical/candidatos_topk.json`).
Em tokenização BPE de modelos multilíngues, português consome entre 1,5 e 1,9
token por palavra, o que situa o contexto recuperado em aproximadamente
**1 500 a 1 900 tokens**, contra 37 269 tokens do corpus integral. Ou seja: o
Top-k entrega cerca de **4% do corpus** por consulta.

---

## 1. Como os documentos ou chunks seriam incorporados ao prompt

A arquitetura de referência é *retrieval-augmented generation* com o
recuperador sendo exatamente o pipeline deste repositório:

```
consulta do usuário (q)
   ↓  tokenizar → remover stopwords (NLTK, pt-BR)   [1_scripts/4_buscar_e_ordenar.py:64]
   ↓  buscar_indexada: postings lists do índice     [1_scripts/4_buscar_e_ordenar.py:347]
   ↓  score = Σ_t IDF(t)·TF_BM25(t, D)              [1_scripts/4_buscar_e_ordenar.py:185]
   ↓  merge_sort por (−score, id_chunk)  +  Top-k   [1_scripts/4_buscar_e_ordenar.py:521]
   ↓  montagem do prompt
```

Os atributos disponíveis por chunk recuperado são exatamente os que um sistema
RAG precisa para citar: `id_chunk`, `id_documento`, `nome_arquivo`, `paginas`,
`score` e `texto` (ver `6_busca_lexical/candidatos_topk.json`). A montagem
concreta do prompt usa esses campos para produzir blocos rotulados:

```
[1] Resolucao_04_2021_CONEPE_Normas_Academicas_Pos_Graduacao.pdf, p. 19
    Elaboração de Pesquisa e os critérios de avaliação de desempenho do
    discente; IV. o formato do trabalho a ser entregue pelo discente ...
[2] Edital_CAPES_14_2023_PRAPG.pdf, p. 7
    ...
```

Três decisões de projeto **já implementadas** importam para o RAG:

1. **Ordenação determinística.** O critério de desempate
   `(−score, id_chunk)` torna a lista de contexto reproduzível: duas execuções
   da mesma consulta produzem o mesmo prompt na mesma ordem. Isso é
   pré-requisito para avaliar um sistema RAG, porque sem determinismo não se
   consegue atribuir uma mudança de resposta a uma mudança de recuperação.
2. **Rótulo de origem e página no próprio candidato.** A rastreabilidade
   (item 6) não requer trabalho extra de metadados: `nome_arquivo` e `paginas`
   já vêm do artefato da Etapa 4.
3. **Coerência entre busca linear e indexada.** As duas configurações devolvem
   Top-k idêntico em todas as 9 consultas da Etapa 8, o que significa que trocar
   a estratégia de recuperação para ganhar desempenho **não** altera o contexto
   entregue ao LLM. É a propriedade que permite otimizar custo sem regressão de
   qualidade recuperada.

---

## 2. Impacto de `k`, tamanho de chunk e ordenação sobre o custo de contexto

O custo de contexto é, em primeira ordem, `k × tamanho_do_chunk` em tokens:

| `k` | Palavras no contexto (`tamanho_chunk = 200`) | Tokens (est.) | Fração do corpus | Cobertura de documentos distintos |
|---|---|---|---|---|
| 1 | 200 | 300 – 380 | 0,8% | 1 |
| **5 (adotado)** | **1 000** | **1 500 – 1 900** | **4%** | **3** |
| 10 | 2 000 | 3 000 – 3 800 | 8% | 3 |
| 20 | 4 000 | 6 000 – 7 600 | 16% | 3 |

Os números das duas últimas colunas não são estimativas: o Top-5 real do corpus
cobre 3 documentos distintos (`Resolucao_04_2021_CONEPE`,
`Edital_CAPES_14_2023_PRAPG` e `Resolucao_29_2022_CONEPE`), com 2 chunks de cada
um dos dois primeiros. O crescimento do custo é **linear em `k`** e o custo não
tem teto: os 182 chunks somam 37 269 tokens, de modo que `k = 182` injetaria o
corpus inteiro no prompt.

**Tamanho de chunk.** O chunking de 200 palavras (`--tamanho-chunk 200`,
`--overlap 30`) foi escolhido como compromisso entre duas falhas opostas:

- *chunks pequenos* (por exemplo 50 palavras) reduzem a granularidade da
  citação e elevam o número de candidatos para cobrir a mesma informação: o
  contexto fica fragmentado e o prompt precisa de mais `k` para o mesmo
  conteúdo, encarecendo o contexto total;
- *chunks grandes* (por exemplo 1 000 palavras) diluem o score BM25, porque
  `TF_BM25` é normalizado por `|D| / avgdl` e o termo consultado passa a ser uma
  fração ínfima do chunk; além disso, o contexto gasto por unidade de informação
  útil piora, já que cada chunk carrega muito texto irrelevante.

A sobreposição de 30 palavras existe para que uma passagem que cruza a fronteira
entre dois chunks não seja perdida: **80 dos 182 chunks (43,96%) atravessam
fronteira de página**, o que mostra que o fenômeno não é marginal neste corpus.

**Ordenação.** A posição do chunk no prompt não altera o número de tokens
enviados, mas altera o comportamento do LLM. Como os candidatos são entregues em
ordem de score decrescente, o material mais bem pontuado fica no início e no fim
do bloco — as posições com maior atenção efetiva em modelos de contexto longo
("lost in the middle"). Inverter a ordem desperdiçaria o custo já pago pelo
Merge Sort, que existe precisamente para produzir essa ordem.

**Custo de recuperação versus custo de geração.** Vale registrar a assimetria:
recuperar o Top-5 custa **2,70 ms** (Configuração 3, medido na Etapa 5, in-process),
enquanto gerar uma resposta sobre 1 500–1 900 tokens custa centenas de
milissegundos a segundos. Ou seja, **o gargalo é a geração, não a busca**. O
ganho de 11× da busca indexada sobre a linear é relevante para o *throughput* de
indexação e de recuperação em lote, mas não é ele que determina a latência
percebida pelo usuário de um RAG.

---

## 3. Recuperar conteúdo lexicalmente similar *versus* semanticamente relevante

O pipeline é **puramente lexical**: o índice mapeia termos normalizados
(Unicode NFC, `[^\W_]+` sobre minúsculas) a postings lists, e a relevância é
BM25. Isso tem consequências concretas e observáveis:

**O que o sistema acerta.** Termos do domínio com grafia estável — `bolsas`,
`matrícula`, `credenciamento`, `trancamento` — são exatamente os termos que o
usuário digita quando conhece a terminologia normativa. Nesse regime, a busca
lexical é precisa e barata: 4 061 termos e 21 530 postings resolvem a consulta
com 90 postings consultadas, ou seja, 0,42% do índice.

**Onde o sistema falha.** A busca lexical não reconhece paráfrase, sinônimo nem
variação morfológica não prevista. Se o usuário pergunta
"*quando perco o direito ao auxílio?*" e o documento escreve
"*suspensão do benefício*", a sobreposição de termos pode ser nula e o chunk
correto **nunca entra no Top-k** — não há como o reranker ou o LLM recuperá-lo
depois. A busca vetorial com *embeddings* (Sentence Transformers, FAISS)
resolveria esse caso, mas traz de volta o custo `Θ(d · n)` que o modelo RAM
deste trabalho não contempla (a dimensão `d` sequer existe nos parâmetros da
Seção 6.1) e a necessidade de GPU para indexação em escala.

**O caso misto como evidência.** A bateria da Etapa 8 inclui a consulta
`"de bolsas xilofone"`: as stopwords `de` são removidas e o único termo útil é
`bolsas`, que produz 5 resultados. Isso demonstra que o sistema é robusto a
ruído lexical (ele simplesmente ignora termos fora do vocabulário) e ao mesmo
tempo **mascara** a diferença entre "recuperei o que era relevante" e
"recuperei o que casou com uma palavra". No item 4 esse ponto é quantificado.

**Consequência para o RAG.** Em uma arquitetura híbrida, este recuperador seria
o *recall-oriented first stage* — barato, determinístico e auditável — seguido
de um reranker semântico sobre os `n_c` candidatos. O custo do reranker seria
`Θ(n_c)` e não `Θ(N)`, que é precisamente o ganho estrutural que o índice
invertido entrega.

---

## 4. Riscos de recuperação incompleta, enviesada, desatualizada ou irrelevante

### 4.1 Recuperação incompleta — quantificada

A bateria de robustez da Etapa 8 executou 9 consultas em 2 configurações
(18 execuções, 0 exceções). O resultado é direto:

| Classe de consulta | Consultas | Resultados vazios |
|---|---|---|
| Relevante (com termos do domínio) | 3 | 0 |
| Nula (`""`, `"   "`, `"!!! ??? ---"`) | 3 | 3 |
| Apenas stopwords (`"de da do para com os as um uma"`) | 1 | 1 |
| Fora do vocabulário (`"xilofone quântico blockchain astrofísica"`) | 1 | 1 |
| Mista (`"de bolsas xilofone"`) | 1 | 0 |
| **Total** | **9** | **5 (55,6%)** |

Do ponto de vista de engenharia, **0% de taxa de falhas** é o resultado
desejado: o sistema nunca lança exceção, degrada para lista vazia e registra
`aviso` em `relatorio_busca.json`. Do ponto de vista de um RAG, porém, a **taxa
de 55,6% de contexto vazio** é o risco mais grave: em 5 das 9 consultas o LLM
receberia **zero** contexto. Um sistema RAG ingênuo, sem verificação de
contexto vazio, responderia mesmo assim — e é exatamente aí que nasce a alucinação
do item 5.

Fontes estruturais de incompletude, todas verificáveis no repositório:

1. **Cobertura do corpus.** São 7 documentos. Uma pergunta sobre um tema que não
   esteja neles ("como funciona o doutorado sanduíche?") não tem resposta
   recuperável, e o sistema não distingue "não existe no corpus" de "não
   encontrei".
2. **Página em branco.** O `doc_006` (Resolução 04/2021/CONEPE) tem uma página
   que é apenas imagem, sem camada de texto: a extração devolve vazio e o
   conteúdo é **irrecuperável** por qualquer consulta. A falha está documentada
   em `3_dados/relatorio_processamento.json`.
3. **Remoção de stopwords.** Consultas formuladas apenas com palavras funcionais
   devolvem vazio por construção, não por ausência de conteúdo.

### 4.2 Viés e cobertura

- **Viés temático.** O corpus é dominado por normas do PROCC/UFS sobre bolsas,
  credenciamento e estrutura curricular. Consultas fora desse recorte têm
  cobertura sistematicamente pior — e o Top-5 real é ilustrativo de como isso
  funciona na prática: **4 dos 5 chunks recuperados vêm de apenas 2 documentos**
  (Resolução 04/2021 e Edital CAPES 14/2023). A distribuição do contexto
  recuperado é fortemente concentrada, o que pode enviesar a resposta do LLM
  para a perspectiva desses dois documentos.
- **Viés de formulação.** Como a relevância é lexical, a recuperação depende de
  o usuário usar a terminologia do documento. Usuários que não conhecem o jargão
  normativo ("auxílio" em vez de "bolsa") são sistematicamente prejudicados.
- **Idioma único.** Todo o corpus é pt-BR; uma consulta em inglês produz 0
  postings.

### 4.3 Desatualização

O corpus foi acessado em **02/09/2026** e é uma fotografia: alterações
posteriores nas normas não são refletidas. O risco é agravado pela própria
natureza do material — instruções normativas e resoluções são revogadas com
frequência, e o índice não tem noção de vigência. Um chunk revogado tem
exatamente o mesmo score de um chunk vigente. Mitigação exigiria metadados de
vigência e reingestão periódica, hoje inexistentes.

### 4.4 Irrelevância

Cinco dos 75 candidatos da carga real compõem o Top-5; os outros 70 foram
descartados por score. O filtro `score > 0` remove apenas o que não casa
**nenhum** termo: um chunk que casa um único termo genérico (`critérios`, com
`DF = 36`) sobrevive ao filtro com score pequeno. Como o corte do Top-k é por
posição, não por limiar de score, o chunk de posição 5 pode ter score
arbitrariamente baixo sem que o sistema sinalize isso. Um limiar de score
mínimo — ou a devolução do score junto ao contexto, para que o LLM saiba o
quanto confiar — seria a mitigação natural.

---

## 5. Risco de o LLM gerar afirmações não sustentadas pelo contexto recuperado

O risco é **estrutural** neste desenho, por quatro razões verificáveis:

1. **A recuperação é lexical, e lexicalidade não implica relevância.** No item 3
   mostrou-se que o sistema pode devolver 5 chunks que compartilham uma palavra
   com a consulta sem responder a ela. Um LLM que recebe esses 5 chunks
   "relacionados mas não pertinentes" tende a produzir uma resposta plausível
   costurando fragmentos — sem que nenhum trecho sustente a afirmação.
2. **O contexto vazio é silencioso.** Os 55,6% de resultados vazios do item 4.1
   chegam ao prompt como uma seção vazia. Sem uma regra explícita do tipo "se o
   contexto estiver vazio, responda que não há base documental", o modelo
   responde por conhecimento paramétrico — que pode estar desatualizado ou
   simplesmente errado para o PROCC/UFS.
3. **Chunks são recortes de 200 palavras.** Um chunk isolado pode conter a
   oração subordinada sem a oração principal, invertendo o sentido de uma regra
   ("...é vedado ao discente [cujo pedido foi indeferido]..."). O modelo é
   instruído a não inferir além do trecho, mas nada no artefato impede que ele
   complete a lacuna.
4. **Score não é transmitido.** Se o prompt não incluir o score, o modelo trata
   o chunk de score 5,50 e o de score 9,62 com a mesma autoridade.

**Contramedidas implementáveis sobre o artefato atual** (o repositório já
fornece tudo o que é necessário):

- instruir o modelo a citar `id_chunk`, `nome_arquivo` e `paginas` de cada
  afirmação, e a recusar-se a responder quando a citação não existir;
- tratar `resultados_retornados == 0` como estado explícito de "sem base
  documental" (o campo já existe em `7_resultados/tabela_robustez.csv`);
- enviar o `score` junto ao texto, para calibrar a confiança;
- usar o campo `frequencias_termos` do candidato para exigir que os **termos
  distintos da consulta** apareçam no trecho, e não apenas um deles.

---

## 6. Como fontes, citações e trechos recuperados melhoram a rastreabilidade

Cada candidato carrega a cadeia de proveniência completa, sem custo adicional:

```
score ← frequencias_termos ← id_chunk ← chunk ← id_documento
                                             ← nome_arquivo
                                             ← paginas: [19]
```

Isso permite que a resposta do LLM seja **auditável de ponta a ponta**:

- `nome_arquivo` e `paginas` permitem ao usuário abrir o PDF na página exata e
  conferir a afirmação;
- `id_chunk` permite reexecutar `merge_sort` e verificar que o chunk foi
  selecionado pela regra de ordenação declarada, não por um acaso;
- `score` e `frequencias_termos` permitem explicar **por que** aquele trecho foi
  recuperado e não outro, o que transforma a recuperação em algo inspecionável;
- `paginas` com mais de um elemento (`[7, 8]` no `chunk_0176`) expõe
  explicitamente os casos em que o chunk cruza fronteira de página — um detalhe
  que, em um sistema sem esse metadado, apareceria como citação ambígua.

A ordenação determinística é o que fecha o argumento: como a mesma consulta
produz sempre o mesmo contexto na mesma ordem, é possível registrar o prompt
exato e reproduzir qualquer resposta auditada. Sem determinismo, a
rastreabilidade seria apenas nominal.

---

## 7. Trade-offs entre precisão, tempo de resposta, uso de memória e custo de geração

| Eixo | Configuração 1 (busca linear) | Configuração 2 (indexada) | Configuração 3 (indexada + Merge Sort) |
|---|---|---|---|
| Tempo de consulta (carga 1, 182 chunks) | 41,46 ms | 3,65 ms | 2,70 ms |
| Tempo de consulta (carga 2, 91 chunks) | 23,13 ms | 2,57 ms | 3,37 ms |
| Dependência de `N` | `Θ(N·(\bar{L}+m))` | `Θ(m+Q)` | `Θ(m+Q+n_c log n_c)` |
| Memória do índice | nenhuma (0 postings) | 21 530 postings | 21 530 postings |
| Memória pico por consulta | `Θ(N)` candidatos | `Θ(n_c)` | `Θ(n_c)` + 1 480 B auxiliares |
| Precisão do contexto | maior precisão (BM25 sobre texto integral, sem aproximação) | idem | idem |
| Determinismo | não ordenado | não ordenado | **ordenado e determinístico** |

Leitura dos trade-offs:

1. **Memória contra tempo.** O índice invertido custa 21 530 postings de
   memória permanente para economizar ~38 ms por consulta (41,46 → 3,65 ms).
   A troca é assimétrica a favor do índice em qualquer regime com mais de
   algumas dezenas de consultas. Note que o *pico* de memória por consulta é
   **maior** na busca linear (`Θ(N)` candidatos, até 182 objetos) do que na
   indexada (`Θ(n_c)`, 75 objetos): o índice economiza tempo **e** pico, ao
   preço de memória persistente.
2. **Tempo de consulta contra determinismo.** A Configuração 3 é a única que
   produz uma lista ordenada — e é a que entrega ao RAG um contexto
   reproduzível e priorizado. O custo adicional sobre a Configuração 2 é o
   Merge Sort: cerca de 0,52 ms para 75 candidatos (`Θ(n_c log n_c)`). Em
   compensação, na carga 2 a Configuração 3 mede 3,37 ms contra 2,57 ms da
   Configuração 2: com apenas 32 candidatos, a ordenação custa 0,19 ms e o
   ruído da máquina compartilhada (≈ 0,8 ms entre cargas) passa a dominar a
   diferença. A conclusão honesta é que **a ordenação é barata o suficiente para
   ser sempre incluída**, mesmo quando `n_c` é pequeno.
3. **Custo de geração contra custo de recuperação.** Recuperar custa
   milissegundos; gerar sobre 1 500–1 900 tokens custa ordens de grandeza mais.
   Consequência prática: aumentar `k` de 5 para 10 dobra o custo de geração
   (≈ 3 000–3 800 tokens) em troca de +16% de corpus. A menos que as consultas
   exijam evidência de múltiplos documentos, o retorno por token é decrescente.
4. **Precisão contra cobertura.** Não há, neste trabalho, *trade-off* de
   precisão entre as configurações: as três usam exatamente a mesma função de
   score e devolvem o **mesmo Top-k** (verificado em 9 consultas na Etapa 8). A
   diferença entre elas é de custo, não de qualidade recuperada. Isso é
   deliberado — foi o que permitiu comparar tempos sem confundir a comparação
   com uma mudança de relevância.
5. **Limitação de fundo.** O que nenhuma das três configurações resolve é a
   precisão *semântica*: não há conjunto de relevância anotado neste trabalho, e
   portanto **Precision@k não é reportado** (o edital o exige "quando houver
   referência de relevância", Seção 7.3). As métricas reportadas — taxa de
   falhas, taxa de resultados vazios, número de comparações e equivalência entre
   configurações — são as que podem ser honestamente sustentadas com os
   artefatos disponíveis. Construir esse conjunto anotado é o principal trabalho
   futuro identificado.

---

## Síntese

O sistema entregue é um recuperador lexical determinístico, auditável e barato,
com evidência quantitativa de que a estratégia indexada reduz o custo de
`Θ(N)` para `Θ(m+Q)` sem degradar o Top-k. Como *first stage* de um RAG ele é
adequado; o que ele **não** faz é julgar relevância semântica, e é exatamente aí
que residem os riscos listados nos itens 4 e 5 — risco de contexto vazio
(55,6% das consultas patológicas testadas), risco de contexto concentrado em
poucos documentos (4 de 5 chunks vindos de 2 documentos) e risco de o LLM
completar lacunas que o recorte de 200 palavras criou. As contramedidas
propostas (citação obrigatória, estado explícito de contexto vazio, transmissão
do score e exigência de cobertura dos termos da consulta) usam apenas campos que
os artefatos já contêm.
