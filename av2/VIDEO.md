# Vídeo da AV2

**URL:** a publicar.  
**Duração máxima:** 10 minutos, com participação de todos.  
**Responsável pela Etapa 5:** Victor Melo.

## Roteiro da Etapa 5 (2–3 minutos)

1. **Problema:** `W` é o orçamento de seleção (soma dos `w_i`), não a janela da
   LLM. Instruções, citação, pergunta, separadores e resposta consomem tokens
   adicionais.
2. **Entrada:** seleções gulosa e PD da AV2 e os custos exatos de `tiktoken`
   (`cl100k_base`, `encode_ordinary`).
3. **Montagem:** contexto com rótulos `[F1]...`, documento, páginas, chunk e
   `v_i`; deduplicação de 30 palavras sobrepostas.
4. **Orçamento:** 190 tokens fixos + 512 de resposta + 64 de segurança; em
   8.192 tokens, 7.426 ficam para chunks.
5. **Demonstração:** rodar `python av2/integrar_contexto.py` e abrir
   `7_contexto_llm/contextos.json`.
6. **Resultados:** em `W=4096`, o prompt da PD tem 4.712 tokens e overhead 667;
   o guloso tem 4.394 e 623; a PD ganha +2,7283 de relevância.
7. **Complexidade:** PD `O(NW)` e `O(NW)` de espaço; guloso `O(N log N)` e
   `O(N)`; montagem `O(k·m + C)`.
8. **Limitações:** janelas pequenas não comportam nem um chunk; latência é
   estimada; qualidade da resposta não foi avaliada; o corpus preserva `\x00`.

## Estado

- [ ] Gravar a participação de Victor Melo.
- [ ] Publicar o vídeo e atualizar a URL acima.
- [ ] Inserir a URL no README e no relatório.
