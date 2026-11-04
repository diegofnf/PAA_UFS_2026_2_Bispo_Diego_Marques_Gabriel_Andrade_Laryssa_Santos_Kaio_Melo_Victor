# Etapa 5 — Complexidade e integração com LLM

**Responsável:** Victor Melo  
**Ponto de entrada oficial:** `av2/integrar_contexto.py`  
**Implementação:** `av2/1_scripts/montar_contexto_llm.py`  
**Análise completa:** `av2/CONTEXTO_LLM.md`

> Material pronto para colar no relatório técnico e nos slides. Os documentos
> externos (Google Docs/Slides) não puderam ser editados porque a sessão do
> navegador não estava autenticada; o conteúdo abaixo preserva os números e as
> ressalvas da execução versionada.

## 1. Objetivo

Integrar os chunks selecionados pelos métodos guloso e de programação dinâmica
a um fluxo compatível com LLMs, construindo um contexto organizado com trechos,
evidências e fontes. A etapa também analisa tempo, memória e tokens, discute a
limitação de contexto e a reserva para instruções/resposta, e avalia os efeitos
na latência e na qualidade.

## 2. Fluxo

```text
chunks tokenizados + instâncias + seleções (guloso/PD)
        │
        ├─ verificação exata de w_i (tiktoken 0.14.0, cl100k_base)
        ├─ ordenação por relevância e deduplicação de sobreposições
        ├─ montagem dos blocos com fontes [F1], [F2], ...
        ├─ orçamento: prompt = W + instruções + resposta + segurança
        ├─ recontagem do prompt final e reparo do orçamento
        └─ contextos.json + CSV + prompt de exemplo + gráficos + relatório
```

O `W` da mochila é o orçamento de **chunks**, não a janela Total da LLM. A
janela de 8 192 tokens reserva 512 para a resposta, 64 de segurança e 190 tokens
fixos de instruções/formatação; o orçamento de chunks em `W=4 096` é 7 426.

## 3. Complexidade

| Etapa | Tempo | Memória | Observação |
|---|---|---|---|
| Guloso | `O(N log N)` | `O(N)` | ordenação por densidade `v_i/w_i`; varredura linear |
| PD 0/1 | `O(NW)` | `O(NW)` | duas matrizes `dp` e `take`, `N=75` candidatos positivos e `W≤4 096` |
| Ordenação dos selecionados | `O(k log k)` | `O(k)` | `k` é o número de chunks selecionados |
| Deduplicação | `O(k·m + k² log k)` no pior caso | `O(k+m)` | mescla de intervalos e varredura das palavras; `k` e `m` pequenos na prática |
| Recontagem de tokens | `O(C)` | `O(C)` | `C` é o número de tokens/caracteres do prompt |
| Matriz experimental | `O(160 · custo)` | `O(custo de uma execução)` | 2 seletores × 4 `W` × 5 janelas × 2 estratégias × 2 dedupes |

O tempo da PD cresce com `N·W`; o guloso cresce com a ordenação. A montagem do
contexto é dominada pela tokenização e pela cópia dos trechos, não pela escolha.

### 3.1 Melhor, pior e caso médio da montagem

| Operação | Melhor caso | Pior caso | Caso médio |
|---|---|---|---|
| Montagem dos blocos | `O(k)` sem dedupe, um bloco por chunk | `O(k·m + k² log k)`, com sobreposição em todos os pares | `O(C)`, dominado pela tokenização do prompt |
| Deduplicação | `O(1)` sem palavra em comum entre chunks consecutivos | `O(k² log k)` quando todos os `k` chunks cobrem o mesmo intervalo | `O(k·m + k log k)`, com `m ≈ 200` palavras |
| Recontagem do prompt | `O(1)` para prompt vazio | `O(C)` com todos os chunks incluídos | `O(C)`, com `C ≈ 4 000` tokens em `W=4 096` |

Nos dados reais vale o caso médio: nenhuma seleção tem sobreposição total e a
maior parte do custo é a codificação BPE do prompt final — não a escolha nem a
dedupe. O custo do algoritmo é separado do custo de tokenização, de I/O de
disco e de chamada de API. **Embeddings não são usados nesta entrega** (a
recuperação é lexical, por BM25), então não há custo vetorial a medir; essa é
uma diferença explícita em relação a um RAG com busca densa.

## 4. Resultados experimentais

Consulta versionada; 182 chunks válidos; 74 055 tokens individuais; nenhuma
divergência de `w_i`; janela de exportação de 8 192 tokens.

| Seletor | `W` | Chunks | Soma `w_i` | Prompt final | Overhead | Relevância | Relevância/1k |
|---|---:|---:|---:|---:|---:|---:|---:|
| Guloso | 512 | 1 | 370 | 607 | 237 | 9,6206 | 15,85 |
| Guloso | 1 024 | 2 | 761 | 1 033 | 271 | 16,6484 | 16,12 |
| Guloso | 2 048 | 5 | 1 905 | 2 304 | 396 | 33,8168 | 14,68 |
| Guloso | 4 096 | 10 | 3 820 | 4 394 | 623 | 57,5855 | 13,11 |
| PD | 4 096 | 11 | 4 093 | 4 712 | 667 | 60,3138 | 12,80 |

- A deduplicação economiza 57 tokens em `W=4 096`.
- A redundância textual (5-gramas) é 0%, 0,24%, 1,93% e 2,53% no guloso e
  3,28% na PD em `W=4 096`; a duplicata de ID é sempre 0 e não serve como
  medida de redundância.
- Em 1 024 tokens de janela, nenhum chunk inteiro cabe após as reservas; o
  contexto ajustado fica vazio. A menor janela que comporta a seleção completa
  é 2 048 para `W≤1 024`, 4 096 para `W=2 048` e 8 192 para `W=4 096`.
- Em `W=4 096`, a PD ganha +2,7283 de relevância (+4,7%), mas gasta 318 tokens
  de prompt a mais; em relevância por 1 000 tokens, o guloso é ligeiramente
  melhor (13,11 contra 12,80).
- A PD é bem mais cara: 58,94 ms e 6,72 MB no `W=4 096`, contra 0,06 ms e
  4,06 KB do guloso. A montagem do contexto levou 1,17–31,89 ms e 20–630 KB.
- 28 de 80 execuções integrais transbordaram a janela; a estratégia ajustada
  não transbordou para janelas ≥1 024, mas pode esvaziar o contexto quando
  nenhum chunk inteiro cabe.

## 5. Latência e qualidade

Com prefill de 2 000 tokens/s e decode de 60 tokens/s, o decode de 512 tokens
domina a latência. Aumentar a reserva de resposta de 512 para 1 024 tokens
acrescenta cerca de 8,5 s e reduz o espaço para chunks; portanto, a reserva é
uma decisão de qualidade, não apenas de segurança.

Foram medidos proxies offline: cobertura dos termos da consulta (60%, 80%,
100% e 100%), documentos distintos (1, 2, 3 e 4), redundância de 5-gramas
(0%, 0,24%, 1,93% e 2,53% no guloso; 3,28% na PD em `W=4 096`) e relevância por
1 000 tokens. **Não foi medida** a correção, fidelidade ou utilidade das
respostas: não havia credencial de LLM no ambiente. O protocolo está em
`CONTEXTO_LLM.md` §10 e o registro da verificação em
`6_evidencias/avaliacao_llm.json`.

## 6. Limitações e riscos

1. Uma única consulta: os números não generalizam para outras perguntas.
2. Tokenizer fixo (`cl100k_base`): outro modelo pode contar tokens de forma
   diferente; a recontagem deve usar o encoding do modelo escolhido.
3. Template de chat real não medido; a moldura da API pode adicionar tokens.
4. `tracemalloc` cobre alocações Python, não buffers nativos do tokenizer ou do
   provedor.
5. O corpus preserva caracteres de controle `\x00` da extração do PDF; APIs
   reais podem rejeitá-los.
6. A latência é estimada por taxas hipotéticas de prefill/decode, não medida
   em rede real.
7. Qualidade textual não medida; cobertura lexical não garante resposta
   correta ou fiel.
8. Tempos de execuções diferentes não são comparáveis: a Etapa 5 (03/11) e a
   Etapa 6 (03/11) foram medidas na mesma máquina, mas a execução histórica de
   cópia limpa usou Python 3.12.14 em outro dia.

## 7. Evidências e reprodução

```bash
python av2/integrar_contexto.py
python -m pytest av2/1_scripts/test_montar_contexto_llm.py -q
python av2/1_scripts/validar_notebook.py --saida notebook_executado.ipynb
```

- 34 testes da Etapa 5; **92 testes da AV2** no total (34 preparação, 10 guloso,
  9 PD, 5 corretude e 34 da Etapa 5) e 14 de regressão da AV1.
- 160 execuções da matriz da Etapa 5 e 48 medições da Etapa 6.
- Execução completa do notebook em cópia limpa no commit `6b815ca`, sem falhas;
  os artefatos da Etapa 5 foram regenerados em 03/11/2026 no commit `5b0fe1d`
  com `arvore_suja_antes_gravar = false`.
- Artefatos: `7_contexto_llm/contextos.json`, `tabela_contexto_llm.csv`,
  `prompt_exemplo.md`, três gráficos e `5_resultados/relatorio_contexto_llm.json`.

## 8. Slides para a apresentação (Victor Melo)

A apresentação tem 10–12 minutos para cinco integrantes; a Etapa 5 ocupa
**4 slides e 1 de reserva**, com cerca de 2 min 45 s de fala (410 palavras).

1. **Do orçamento da mochila ao orçamento do prompt** — reservas da janela
   (8 192 = 190 + 512 + 64 + 7 426), instância de 75 candidatos e os dois
   selecionadores.
2. **Montar o contexto com evidências e fontes** — cabeçalho de fonte, dedupe,
   recontagem e 5-gramas; custo da montagem (1,17–31,89 ms; 20–630 KB).
3. **Prompt, overhead e o preço da otimalidade** — tabela por `W` e
   `7_contexto_llm/grafico_prompt_por_w.png`.
4. **Complexidade: Θ(NW) contra Θ(N log N)** — pseudo-polinomial, 311 mil
   estados e o confronto 58,94 ms × 0,06 ms.
5. **Reserva** — `grafico_folga_janela.png` e `grafico_latencia_contexto.png`
   para perguntas sobre estouro de janela e latência.

Complexidades para a pergunta de reserva:

| Etapa | Tempo | Memória |
|---|---|---|
| Guloso | `O(N log N)` | `O(N)` |
| PD 0/1 | `O(NW)` | `O(NW)` |
| Montagem + dedupe | `O(k·m + k² log k)` no pior caso | `O(k+m)` |
| Recontagem do prompt | `O(C)` | `O(C)` |

Pontos de reserva sobre qualidade: os proxies medidos foram cobertura dos termos
da consulta (60% a 100%), 1 a 4 documentos distintos, redundância de 5-gramas e
relevância por 1 000 tokens; a qualidade textual não foi medida por falta de
credencial de LLM. Riscos a citar: janela de 1 024 pode esvaziar o contexto,
uma única consulta e falso positivo lexical (o chunk de maior BM25 da consulta
trata de outro assunto).

**Demonstração (30 s):** `python av2/integrar_contexto.py` e abrir
`7_contexto_llm/contextos.json`.

## 9. Blocos prontos para colar no relatório

### 9.1 Para a seção “Relação com IA generativa” (§14 do documento)

> A Etapa 5 mede o que a LLM realmente recebe. O `W` da mochila é a soma dos
> custos `w_i` dos chunks, não a janela do modelo: instruções, citação, pergunta,
> separadores e resposta consomem tokens adicionais. Em uma janela de 8 192
> tokens, reservamos 512 para a resposta, 64 de segurança e 190 tokens fixos,
> deixando 7 426 para chunks. Com `W=4 096`, o prompt da PD tem 4 712 tokens e
> overhead de 667; o do guloso, 4 394 e 623. A PD ganha +2,7283 de relevância
> (+4,7%), mas gasta 318 tokens a mais: em relevância por 1 000 tokens o guloso
> é ligeiramente melhor (13,11 contra 12,80). O custo computacional também é
> assimétrico: 58,94 ms e 6,72 MB para a PD contra 0,06 ms e 4,06 KB para o
> guloso em `W=4 096`. A latência é estimada por taxas declaradas de
> prefill/decode; não houve chamada real. O risco principal é o falso positivo
> lexical: o chunk de maior BM25 da consulta trata de outro assunto, e
> maximizar `v_i` não maximiza a chance de o contexto responder à pergunta.
> Também é possível esvaziar o contexto em janelas pequenas (1 024
> tokens) quando nenhum chunk inteiro cabe após as reservas.

### 9.2 Pendências que só a equipe resolve

1. Gravar a participação de cada integrante e publicar o vídeo; inserir a URL
   em `VIDEO.md`, no `README.md` da raiz, no `README.md` da AV2 e na seção
   “URL do vídeo” do relatório.
2. Revisar as seções 16 e 17 do relatório (declaração de IA e contribuição
   individual), já preenchidas, e conferir o texto do bloco 9.1 na seção 14.
3. Inserir os gráficos no relatório: hoje o documento tem 11 páginas e nenhuma
   figura.
4. Unir `av2` à `main` e criar a tag `av2-entrega`, preservando `av1/` e
   `av1-entrega`.
