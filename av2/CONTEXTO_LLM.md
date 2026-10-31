# Etapa 5 (AV2) — Complexidade e integração IA

**Responsável:** Victor Melo.

> Esta etapa integra as seleções da Etapa 2 (guloso) e da Etapa 3 (PD) a um
> payload de chat. Ela **não** chama LLM: mede o custo do contexto e deixa o
> envio para um cliente com credencial própria. O ponto de entrada oficial é
> [`integrar_contexto.py`](integrar_contexto.py), que reutiliza a implementação
> detalhada de [`1_scripts/montar_contexto_llm.py`](1_scripts/montar_contexto_llm.py).

## 1. O problema específico da AV2

A AV2 não usa Top-k. Ela resolve uma mochila 0/1 com `W ∈ {512, 1024, 2048, 4096}`
e dois seletores:

- **guloso** por densidade `v_i / w_i`, tempo `O(n log n)`, espaço `O(n)`;
- **PD** exata, tempo `O(nW)`, espaço `O(nW)`.

O custo `w_i` é a contagem exata de `tiktoken==0.14.0`, `cl100k_base`,
`encode_ordinary`, do texto individual de cada chunk. `W` é apenas a soma dos
`w_i` selecionados. **`W` não é a janela da LLM**: instruções, citações,
separadores, pergunta e resposta são custos adicionais. A Etapa 5 precisa
recontar o prompt final, como o próprio `av2/README.md` determina.

## 2. Fluxo da Etapa 5

```text
av2/2_dados_tokenizados/chunks_tokenizados.json  (texto + w_i + v_i)
av2/3_instancias/instancias.json                 (consulta + W)
av2/4_selecao_contexto/selecao_gulosa.json       (conjunto guloso por W)
av2/4_selecao_contexto/selecao_pd.json           (conjunto ótimo por W)
                         │
                         ▼
av2/integrar_contexto.py  (delega para 1_scripts/montar_contexto_llm.py)
   ├─ verifica w_i contra encode_ordinary
   ├─ ordena por relevância (v_i desc, id_chunk asc)
   ├─ deduplica sobreposição de 30 palavras
   ├─ monta blocos [F1], [F2], ...
   ├─ recontar tokens do prompt final
   ├─ aplica orçamento da LLM (integral ou ajustado)
   └─ mede tempo, memória, tokens, cobertura e latência
                         │
                         ▼
av2/7_contexto_llm/contextos.json               (payloads de chat)
av2/7_contexto_llm/tabela_contexto_llm.csv      (160 execuções)
av2/5_resultados/relatorio_contexto_llm.json    (resumo e benchmark)
```

## 3. Contrato do prompt

O prompt tem duas mensagens:

**Sistema** — restringe o modelo ao contexto e exige abstenção:

```text
Você é um assistente de pesquisa que responde em português do Brasil.
Use exclusivamente as evidências do CONTEXTO fornecido.
1. Cite cada afirmação com o rótulo da fonte entre colchetes, por exemplo [F1].
2. Se o contexto não contiver a resposta, escreva exatamente
   "Não há evidência suficiente no contexto recuperado." e não complete
   com conhecimento externo.
3. Preserve números, prazos e nomes exatamente como aparecem nas fontes.
4. Não invente referências, páginas ou trechos.
```

**Usuário** — contexto numerado e pergunta:

```text
CONTEXTO RECUPERADO:

[F1] Resolucao_04_2021_CONEPE_Normas_Academicas_Pos_Graduacao.pdf | páginas 19 | chunk_0131 | BM25 9.6206
<texto do chunk>

[F2] ...

PERGUNTA: critérios para atribuição de bolsas e requisitos de matrícula

Responda apenas com base nas fontes acima e cite os rótulos [F1], [F2], ...
```

Cada bloco preserva documento, páginas, `id_chunk` e `v_i`. A ordem padrão é
relevância decrescente, com desempate por `id_chunk`; o CLI permite preservar
`ordem_selecao` ou a ordem do corpus.

O modelo de referência do payload é `gpt-4-turbo`, que usa `cl100k_base` — o
mesmo encoding fixado pela AV2. Modelos como `gpt-4o` usam `o200k_base`; para
eles é obrigatório recontar o prompt com o encoding correto. O script aceita
`--encoding` e `--modelo`, mas não valida a correspondência entre os dois.

## 4. Orçamento e reparo

```text
orcamento_contexto = janela_llm
                   − tokens_fixos
                   − reserva_resposta
                   − reserva_seguranca
```

- `tokens_fixos` medidos: **190 tokens** (sistema + moldura da pergunta).
- `reserva_resposta`: 512 tokens no experimento padrão.
- `reserva_seguranca`: 64 tokens para diferenças de template/chat.
- Portanto, em 8 192 tokens, o orçamento para chunks é **7 426 tokens**.

Estratégias:

- **integral**: inclui todos os chunks não redundantes; pode estourar a janela.
  É o *baseline* que mostra o custo real do prompt.
- **ajustado**: inclui os chunks na ordem de relevância enquanto couberem;
  descarta os demais. Se `--truncar-ultimo` for usado, o último chunk é cortado
  por busca binária de palavras.

Depois da montagem, o script recalcula o prompt e, no modo ajustado, remove o
último bloco até `tokens_prompt + resposta + segurança ≤ janela`. Isso protege
contra a diferença de tokenização nas bordas da concatenação.

## 5. Deduplicação

Os chunks da AV1 têm 200 palavras e passo 170; 30 palavras se repetem entre
chunks vizinhos. Por documento, o script guarda a união dos intervalos
`[inicio_palavra, fim_palavra)` já incluídos e remove essa interseção do próximo
chunk. Os intervalos reais incluídos são registrados, e não a janela nominal,
porque a sobreposição pode estar no início ou no fim do chunk.

Em `W=4096`, a deduplicação remove 30 palavras e economiza **57 tokens** tanto
no guloso quanto na PD. O efeito é pequeno em `W` baixos porque os chunks
selecionados raramente são vizinhos.

## 6. Complexidade

Sejam `n=75` candidatos, `k` chunks selecionados, `m` palavras por chunk e `C`
caracteres do prompt.

| Operação | Tempo | Espaço |
|---|---|---|
| Seleção gulosa | `O(n log n)` | `O(n)` |
| Seleção por PD | `O(nW)` | `O(nW)` |
| Ordenação para o prompt | `O(k log k)` | `O(k)` |
| Deduplicação | `O(k·m + k² log k)` | `O(k+m)` |
| Tokenização BPE do prompt | custo do BPE sobre `O(C)` | `O(tokens)` |
| Montagem final | `O(C)` | `O(prompt)` |

A PD é pseudo-polinomial em `W`: dobrar `W` aproximadamente dobra tempo e
memória. O guloso não cresce com `W`, mas não garante otimalidade. A Etapa 5
acrescenta um custo de montagem independente de `W` (depende de `k` e do texto),
pequeno diante da seleção PD e da geração.

Valores medidos nesta máquina (mediana de 7 execuções, mesmo harness):

| Método | `W` | Tempo da seleção | Pico de memória | Chunks | Relevância |
|---|---:|---:|---:|---:|---:|
| Guloso | 512 | 0,05 ms | 2 064 B | 1 | 9,6206 |
| Guloso | 1 024 | 0,06 ms | 2 304 B | 2 | 16,6484 |
| Guloso | 2 048 | 0,07 ms | 2 928 B | 5 | 33,8168 |
| Guloso | 4 096 | 0,08 ms | 4 064 B | 10 | 57,5855 |
| PD | 512 | 5,24 ms | 642 328 B | 1 | 9,6206 |
| PD | 1 024 | 14,57 ms | 1 342 200 B | 2 | 16,6484 |
| PD | 2 048 | 32,77 ms | 2 924 592 B | 5 | 33,8168 |
| PD | 4 096 | 75,03 ms | 6 723 864 B | 11 | 60,3138 |

A PD cresce quase linearmente com `W` neste intervalo; o guloso é ordens de
grandeza mais barato. Nesta execução, para `W` de 512 a 4 096 na janela 8 192,
a montagem do contexto ficou entre **1,2 ms e 31,3 ms** e **19,7 KB e
630,4 KB**. O pior caso de toda a matriz ficou em 31,3 ms e 630,4 KB; a
memória da PD é a dominante no fluxo completo. Os tempos variam entre execuções;
por isso o relatório registra a mediana de 7 repetições por célula.

## 7. Protocolo experimental

- **Seletores**: guloso e PD.
- **Orçamentos `W`**: 512, 1 024, 2 048 e 4 096.
- **Janelas da LLM**: 1 024, 2 048, 4 096, 8 192 e 16 384.
- **Estratégias**: integral e ajustado.
- **Deduplicação**: com e sem.
- **Total**: 2 × 4 × 5 × 2 × 2 = **160 execuções**; 7 repetições por célula no
  relatório. O notebook usa 5 repetições para reduzir o tempo de execução, ainda
  acima do mínimo de 3 exigido pela atividade.
- **Tempo**: `time.perf_counter` ao redor da montagem e da recontagem.
- **Memória**: pico de `tracemalloc` (não inclui buffers nativos do `tiktoken`).
- **Tokenização**: `tiktoken==0.14.0`, `cl100k_base`, `encode_ordinary`.
- **Latência**: prefill a 2 000 tokens/s e decode a 60 tokens/s, valores
  declarados como hipótese, não medidos no provedor.

## 8. Resultados com os artefatos reais

Validação: 182 chunks, **74 055 tokens individuais**, nenhum `w_i` zero e
nenhuma divergência entre `w_i` e `encode_ordinary`.

### 8.1 Prompt final e overhead

Janela 8 192, deduplicação ativa, estratégia integral:

| Seletor | `W` | Chunks | Soma `w_i` | Textos recontados (sem dedupe) | Textos incluídos | Contexto com cabeçalhos | Prompt final | Overhead | Delta final vs `w_i` | Relevância | Relevância/1k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Guloso | 512 | 1 | 370 | 370 | 370 | 416 | 607 | 237 | 0 | 9,6206 | 15,85 |
| Guloso | 1 024 | 2 | 761 | 762 | 762 | 843 | 1 033 | 271 | 1 | 16,6484 | 16,12 |
| Guloso | 2 048 | 5 | 1 905 | 1 908 | 1 908 | 2 113 | 2 304 | 396 | 3 | 33,8168 | 14,68 |
| Guloso | 4 096 | 10 | 3 820 | 3 828 | 3 771 | 4 203 | 4 394 | 623 | −49 | 57,5855 | 13,11 |
| PD | 512 | 1 | 370 | 370 | 370 | 416 | 607 | 237 | 0 | 9,6206 | 15,85 |
| PD | 1 024 | 2 | 761 | 762 | 762 | 843 | 1 033 | 271 | 1 | 16,6484 | 16,12 |
| PD | 2 048 | 5 | 1 905 | 1 908 | 1 908 | 2 113 | 2 304 | 396 | 3 | 33,8168 | 14,68 |
| PD | 4 096 | 11 | 4 093 | 4 102 | 4 045 | 4 521 | 4 712 | 667 | −48 | 60,3138 | 12,80 |

Leituras:

1. **O overhead é grande em `W` pequeno**: 237 tokens em `W=512` equivalem a
   64% do custo dos chunks. Em `W=4 096`, cai para ~16%.
2. **O delta final pode ser negativo**: concatenar chunks pode fundir tokens
   nas fronteiras e a dedupe remove palavras repetidas. Em `W=4 096`, o texto
   incluído tem 48–49 tokens menos que a soma dos `w_i` individuais.
3. **A dedupe economiza 57 tokens** em `W=4 096`; por isso o texto incluído
   fica ainda menor que o texto selecionado.
4. **A cobertura lexical satura em `W=2 048`**: 60% em 512, 80% em 1 024 e
   100% a partir de 2 048. A relevância por 1 000 tokens é máxima em 1 024
   (16,12) e cai em 4 096 (12,80 na PD), indicando sobre-recuperação.

### 8.2 Janela mínima e impacto da limitação de contexto

Com resposta de 512 e segurança de 64:

| `W` | Menor janela que comporta toda a seleção | Menor janela com ao menos 1 chunk |
|---:|---:|---:|
| 512 | 2 048 | 2 048 |
| 1 024 | 2 048 | 2 048 |
| 2 048 | 4 096 | 2 048 |
| 4 096 | 8 192 | 2 048 |

Em **1 024 tokens**, o orçamento para contexto é 258 tokens; nenhum chunk
inteiro cabe (o menor bloco tem ~416 tokens), então o modo ajustado produz
contexto vazio e cobertura 0%. Uma janela de 1 024 já não serve para esta
seleção com resposta de 512 — instruções + resposta + segurança consomem
766 dos 1 024 tokens.

Quando a janela não comporta tudo, o modo ajustado perde relevância:

| Seleção | Janela | Chunks incluídos | Relevância incluída | Perda |
|---|---:|---:|---:|---:|
| PD `W=4 096` | 4 096 | 8/11 | 47,3258 | 12,9880 |
| PD `W=4 096` | 2 048 | 3/11 | 22,7680 | 37,5458 |
| Guloso `W=4 096` | 4 096 | 7/10 | 43,6467 | 13,9388 |
| Guloso `W=4 096` | 2 048 | 3/10 | 22,7680 | 34,8175 |

O modo **integral** deixa isso explícito: 28 das 80 execuções integrais
estouram a janela. Nas janelas analisadas (≥ 1 024), o ajustado nunca estourou,
mas pagou com perda de contexto. Abaixo de 766 tokens nem o prompt fixo mais a
resposta cabem; esse caso não faz parte da matriz e deve ser rejeitado pelo
cliente.

### 8.3 PD versus guloso

| `W` | Ganho de relevância da PD | Δ tokens de prompt | Δ relevância/1k |
|---:|---:|---:|---:|
| 512 | 0,0000 | 0 | 0,00 |
| 1 024 | 0,0000 | 0 | 0,00 |
| 2 048 | 0,0000 | 0 | 0,00 |
| 4 096 | **+2,7283 (+4,7%)** | **+318** | **−0,31** |

A PD só supera o guloso em `W=4 096`, como já mostrava a Etapa 4. O ganho de
relevância custa 318 tokens de prompt; em relevância por 1 000 tokens, o guloso
é ligeiramente mais eficiente (13,11 contra 12,80). Para uma janela apertada,
o guloso entrega quase a mesma cobertura lexical com menos contexto.

## 9. Latência

Com prefill de 2 000 tokens/s e decode de 60 tokens/s:

| Cenário | Prompt | Prefill | Decode (512) | Total | Decode |
|---|---:|---:|---:|---:|---:|
| `W=512` | 607 | 0,30 s | 8,53 s | 8,84 s | 96% |
| `W=1 024` | 1 033 | 0,52 s | 8,53 s | 9,05 s | 94% |
| `W=2 048` | 2 304 | 1,15 s | 8,53 s | 9,69 s | 88% |
| Guloso `W=4 096` | 4 394 | 2,20 s | 8,53 s | 10,73 s | 80% |
| PD `W=4 096` | 4 712 | 2,36 s | 8,53 s | 10,89 s | 78% |

O decode domina. Aumentar a resposta reservada de 512 para 1 024 tokens
acrescenta 8,53 s e reduz o orçamento de contexto em 512 tokens. O custo local
de montagem (poucas dezenas de ms nesta execução) é desprezível diante da geração, mas é o único custo sob
controle do algoritmo de contexto.

A atenção do Transformer é quadrática no comprimento da sequência; o modelo
linear acima não captura esse termo. Para os tamanhos deste corpus (≤ 4,7 mil
tokens de prompt), o decode continua sendo o termo dominante.

## 10. Qualidade: o que foi e o que não foi medido

Foram medidos proxies offline:

- cobertura dos termos da consulta: 60% (`W=512`), 80% (`W=1 024`), 100%
  (`W≥2 048`);
- documentos distintos: 1, 2, 3 e 4, respectivamente;
- redundância de 5-gramas: 0%, 0,25%, 1,86% e 2,50% no guloso; 3,25% na PD
  em `W=4 096`;
- relevância por 1 000 tokens de prompt;
- perda de relevância quando a janela corta chunks.

**Não foi medido** se a resposta gerada é correta, fiel ou útil. Isso exige um
LLM ou avaliador humano, com perguntas de referência, rubrica e `temperature=0`.
O payload está pronto em `7_contexto_llm/contextos.json`, mas o envio não foi
feito. Em 31/10/2026 o ambiente foi verificado: não havia chave de provedor
(`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY` ou
`AZURE_OPENAI_API_KEY`), o GitHub CLI não estava autenticado e o Copilot CLI
respondeu `No authentication information found`. O registro está em
`6_evidencias/avaliacao_llm.json`; nenhuma credencial é armazenada no
repositório. Assim, a qualidade textual continua **não medida**, e os números
de tempo e memória não incluem latência de rede ou de inferência.

Cobertura lexical não é qualidade: um contexto pode conter todos os termos e
ainda assim omitir a exceção, misturar normas de anos diferentes ou citar o
termo em outro sentido. A recuperação é BM25, não semântica.

## 11. Ameaças à validade

1. **Uma consulta**: todos os números são da consulta versionada; não há
   generalização estatística para outras perguntas.
2. **Tokenizer fixo**: `cl100k_base` é a unidade da AV2; um modelo com outro
   vocabulário pode contar tokens de forma diferente. O modo `tiktoken` deve ser
   reexecutado com o encoding do modelo escolhido.
3. **Template de chat não medido**: a moldura real da API pode adicionar
   tokens; a reserva de 64 tokens é uma margem declarada, não uma medição do
   provedor.
4. **Latência estimada**: as taxas de prefill/decode são hipóteses; não foram
   medidas em API paga.
5. **Memória**: `tracemalloc` cobre objetos Python, não os buffers nativos do
   `tiktoken` nem a memória do provedor.
6. **Deduplicação textual**: remover 30 palavras pode eliminar uma fronteira
   de frase útil; o corte é lexical e não semântico.
7. **Ordem**: a ordem por relevância coloca a melhor fonte em `[F1]`, mas não
   foi medido o efeito *lost in the middle*.

## 12. Reprodutibilidade

```bash
python -m pip install -r av2/requirements.txt
python av2/integrar_contexto.py
python -m pytest av2/1_scripts/test_montar_contexto_llm.py -q
```

Variações úteis:

```bash
# varredura completa (160 execuções, 7 repetições)
python av2/integrar_contexto.py --repeticoes 7

# exportar payloads para uma janela específica
python av2/integrar_contexto.py --janela-exportacao 4096 --estrategia-exportacao ajustado

# truncar o último chunk em vez de descartá-lo
python av2/integrar_contexto.py --truncar-ultimo
```

Artefatos:

| Arquivo | Conteúdo |
|---|---|
| `7_contexto_llm/contextos.json` | 8 payloads (2 seletores × 4 `W`) na janela de exportação |
| `7_contexto_llm/prompt_exemplo.md` | prompt legível da PD em `W=4 096` |
| `7_contexto_llm/tabela_contexto_llm.csv` | 160 linhas experimentais |
| `7_contexto_llm/grafico_prompt_por_w.png` | prompt final por `W` e seletor |
| `7_contexto_llm/grafico_folga_janela.png` | folga da janela por `W` |
| `7_contexto_llm/grafico_latencia_contexto.png` | latência estimada vs prompt |
| `5_resultados/relatorio_contexto_llm.json` | validação, benchmark, resumo e comparação |

## 13. Conclusão

A Etapa 5 fecha a AV2 com uma separação explícita entre **orçamento de seleção**
(`W`, soma de `w_i`) e **orçamento de prompt** (janela da LLM menos instruções,
resposta e segurança). Nos dados reais, o prompt é 237–667 tokens maior que a
soma dos `w_i`; em `W=512`, esse overhead é 64% do custo dos chunks.

A PD ganha relevância apenas em `W=4 096` (+4,7%), ao custo de 318 tokens e de
ordens de grandeza a mais em tempo/memória. O guloso é mais eficiente por token
e domina os orçamentos menores. A deduplicação economiza 57 tokens em `W=4 096`.
Janelas de 1 024 tokens não comportam nem o menor chunk após as reservas; com
4 096, a PD perde 12,99 de relevância ao ajustar a seleção.

O próximo passo experimental é enviar os payloads a um LLM com perguntas de
referência e medir corretude, fidelidade e abstenção — o que este repositório
deliberadamente não faz sem credencial e sem modelo definido.

## 14. Material para o relatório e a apresentação

**Resumo pronto para o relatório:**

> A Etapa 5 integra os resultados dos algoritmos de seleção de chunks a um
> fluxo compatível com LLMs, construindo um contexto organizado para geração de
> respostas. A etapa realiza a análise experimental e teórica da complexidade
> dos métodos, considerando tempo de execução, consumo de memória e quantidade
> de tokens. Também discute os impactos da limitação de contexto das LLMs, a
> necessidade de reservar tokens para instruções e resposta, e os efeitos na
> latência e na qualidade das respostas geradas.

**Roteiro sugerido de slides:**

1. Problema: `W` é orçamento de seleção, não janela da LLM.
2. Entrada: seleções gulosa/PD e `w_i` exato da AV2.
3. Arquitetura: `integrar_contexto.py` → prompt → `contextos.json`.
4. Orçamento: 190 fixos + 512 resposta + 64 segurança.
5. Complexidade: guloso `O(N log N)`, PD `O(NW)`, montagem `O(k·m + C)`.
6. Resultados: prompt final, overhead, dedupe e PD × guloso.
7. Limitação: janelas pequenas, perda de relevância e ajuste.
8. Latência: prefill/decode e dominância do decode.
9. Riscos: qualidade não medida, `\x00`, uma consulta, memória nativa.
10. Próximos passos: chamada real ao LLM e avaliação por rubrica.

**Figuras disponíveis:** `7_contexto_llm/grafico_prompt_por_w.png`,
`7_contexto_llm/grafico_folga_janela.png` e
`7_contexto_llm/grafico_latencia_contexto.png`.
