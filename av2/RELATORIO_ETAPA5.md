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
| PD 0/1 | `O(NW)` | `O(NW)` | duas matrizes `dp` e `take`, `N=182`, `W≤4 096` |
| Ordenação dos selecionados | `O(k log k)` | `O(k)` | `k` é o número de chunks selecionados |
| Deduplicação | `O(k² log k)` no pior caso | `O(k)` | mescla de intervalos; `k` pequeno na prática |
| Recontagem de tokens | `O(C)` | `O(C)` | `C` é o número de tokens/caracteres do prompt |
| Matriz experimental | `O(160 · custo)` | `O(custo de uma execução)` | 2 seletores × 4 `W` × 5 janelas × 2 estratégias × 2 dedupes |

O tempo da PD cresce com `N·W`; o guloso cresce com a ordenação. A montagem do
contexto é dominada pela tokenização e pela cópia dos trechos, não pela escolha.

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
- A PD ganha +2,7283 de relevância (+4,7%) em `W=4 096`, mas gasta 318 tokens de
  prompt a mais; por 1 000 tokens, o guloso é ligeiramente melhor.
- Em `W=4 096`, a PD levou 75,03 ms e 6,72 MB; o guloso, 0,08 ms e 4,06 KB.
- A montagem do contexto levou poucas dezenas de ms e 20–630 KB.
- 28 de 80 execuções integrais transbordaram a janela; a estratégia ajustada não
  transbordou para janelas ≥1 024, mas pode esvaziar o contexto quando nenhum
  chunk inteiro cabe.

## 5. Latência e qualidade

Com prefill de 2 000 tokens/s e decode de 60 tokens/s, o decode de 512 tokens
domina a latência. Aumentar a reserva de resposta de 512 para 1 024 tokens
acrescenta cerca de 8,5 s e reduz o espaço para chunks; portanto, a reserva é
uma decisão de qualidade, não apenas de segurança.

Foram medidos proxies offline: cobertura dos termos da consulta (60%, 80%,
100% e 100%), documentos distintos (1, 2, 3 e 4), redundância de 5-gramas e
relevância por 1 000 tokens. **Não foi medida** a correção, fidelidade ou
utilidade das respostas: não havia credencial de LLM no ambiente. O protocolo
está em `CONTEXTO_LLM.md` §10 e o registro da verificação em
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

## 7. Evidências e reprodução

```bash
python av2/integrar_contexto.py
python -m pytest av2/1_scripts/test_montar_contexto_llm.py -q
python av2/1_scripts/validar_notebook.py --saida notebook_executado.ipynb
```

- 34 testes da Etapa 5; 92 testes da AV2; 160 execuções da matriz.
- Execução completa do notebook em cópia limpa no commit `6b815ca`, sem falhas.
- Artefatos: `7_contexto_llm/contextos.json`, `tabela_contexto_llm.csv`,
  `prompt_exemplo.md`, três gráficos e `5_resultados/relatorio_contexto_llm.json`.

## 8. Roteiro de slides (10 slides)

1. **Problema:** `W` é orçamento de seleção, não janela da LLM.
2. **Entrada:** 182 chunks, 75 candidatos positivos, `w_i` exato.
3. **Arquitetura:** `integrar_contexto.py` → prompt → `contextos.json`.
4. **Orçamento:** 190 fixos + 512 resposta + 64 segurança; prompt final medido.
5. **Complexidade:** guloso `O(N log N)`, PD `O(NW)`, montagem `O(k² log k)`.
6. **Resultados:** prompt, overhead, dedupe e comparação PD × guloso.
7. **Memória:** PD 6,72 MB × guloso 4,06 KB em `W=4 096`.
8. **Latência:** prefill/decode e dominância do decode.
9. **Riscos:** qualidade não medida, `\x00`, uma consulta, memória nativa.
10. **Conclusão:** contexto reprodutível e limitações declaradas; próximo passo
    é a avaliação real com rubrica e `temperature=0`.

**Figuras:** `7_contexto_llm/grafico_prompt_por_w.png`,
`grafico_folga_janela.png` e `grafico_latencia_contexto.png`.
