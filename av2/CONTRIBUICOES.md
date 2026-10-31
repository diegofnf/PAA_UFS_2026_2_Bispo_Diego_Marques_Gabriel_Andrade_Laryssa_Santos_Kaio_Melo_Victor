# Contribuição individual — AV2

| Integrante | Etapa | Contribuição principal | Evidência |
|---|---|---|---|
| Diego Bispo | 1 | Ingestão, tokenização e preparação das instâncias | `1_scripts/preparar_instancias.py`, `2_dados_tokenizados/`, `3_instancias/` |
| Kaio Santos | 2 | Baseline guloso por densidade de relevância | `1_scripts/selecionar_guloso.py`, `4_selecao_contexto/selecao_gulosa.json` |
| Diego Bispo e Kaio Santos | 3 | Programação dinâmica exata da mochila 0/1 | `1_scripts/selecionar_pd.py`, `4_selecao_contexto/selecao_pd.json` |
| Gabriel Marques | 4 | Corretude, contraexemplo e benchmark comparativo | `1_scripts/gerar_relatorio_corretude.py`, `5_resultados/relatorio_corretude_limites.json` |
| Victor Melo | 5 | Integração com LLM, orçamento de tokens, análise de tempo/memória e riscos | `integrar_contexto.py`, `1_scripts/montar_contexto_llm.py`, `CONTEXTO_LLM.md`, `7_contexto_llm/` |

## Revisão e validação

- Todos os integrantes participaram da definição do corpus, da consulta e da
  interpretação dos resultados.
- A Etapa 5 foi revisada por Victor Melo com apoio de testes automatizados.
- A declaração de uso de IA está em [`DECLARACAO_IA.md`](DECLARACAO_IA.md).
- O vídeo e a apresentação são entregas coletivas; o roteiro da Etapa 5 está em
  [`VIDEO.md`](VIDEO.md).
