# Verificação da etapa 1

Data: 15/10/2026. Código executado:
[`b984f377c101386f27399da683bed644de38e987`](https://github.com/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/commit/b984f377c101386f27399da683bed644de38e987).

O notebook foi executado por inteiro em **cópia limpa**, com ambiente virtual
novo, Windows AMD64 e Python 3.12.14. O registro de geração indica
`arvore_suja_antes_gravar = false` e o commit do código, não a base da AV1.

```bash
python -m pip install -r av2/requirements-validacao.txt
python av2/1_scripts/validar_notebook.py --saida caminho/notebook_executado.ipynb
```

Registro histórico: **48 testes aprovados** (34 da preparação AV2 e 14 da AV1).
Há um aviso preexistente de depreciação do importador `load_module` usado pelos
testes da AV1; nenhum teste falhou. As três células de código do notebook
terminaram sem erro. Isso valida a execução em kernel real; não se afirma
que a execução Windows tenha ocorrido no serviço Colab.

A execução atual das etapas 1 a 3 da AV2, após a inclusão dos seletores e dos
testes de corretude, aprovou **53 testes**: 34 da preparação, 10 do baseline
guloso e 9 da programação dinâmica. A Etapa 4 possui adicionalmente 5 testes
próprios. O resultado consolidado das etapas anteriores está em `testes.xml`.

### Execução atual em cópia limpa (Etapa 5)

Data: 31/10/2026. Commit executado: `6b815ca`. O clone foi criado com
`git clone --branch av2 --single-branch` em diretório temporário, e o notebook
completo rodou em kernel real. As células executaram os testes de cada etapa:
48 da preparação, 9 do guloso, 8 da PD, 5 da corretude e **34 da Etapa 5**,
todas sem falha. O notebook executado está em
`notebook_executado_etapa5.ipynb`, o log em `notebook_execucao.log` e o
registro estruturado em `validacao_notebook.json`.

Essa execução também regenerou, no clone limpo, `av2/4_selecao_contexto/`,
`av2/5_resultados/` e `av2/7_contexto_llm/`, confirmando que os artefatos da
Etapa 5 são reproduzíveis a partir do código versionado.

## Matriz de resultados esperados e observados

Os nomes abaixo correspondem a testes em `av2/1_scripts/test_preparar_instancias.py`.
O XML registra o status de cada execução, incluindo os parâmetros.

| Caso / requisito | Resultado esperado | Resultado observado | Evidência / status |
|---|---|---|---|
| Normal: custo exato, score e origem | `hello world` = 2 tokens; v_i = 2,5; entrada intacta | Vetor `[15339, 1917]`, custo/score e origem conferidos | `test_normal_tokens_exatos_score_e_origem_sem_mutacao`: aprovado |
| Corpus vazio | Itens vazios em todas as capacidades | Quatro cenários com zero itens | `test_corpus_vazio`: aprovado |
| Sem correspondência / texto vazio | Benefício zero; texto vazio com custo zero fora da mochila | Nenhum candidato positivo | `test_sem_correspondencia_e_chunk_vazio`: aprovado |
| Fronteira e orçamento excedido | Item de 2 tokens excede W = 0 e 1; cabe em W = 2 | Contagens acima de W: `[1, 1, 0]`; item mantido na entrada | `test_fronteira_zero_igual_e_item_maior_que_orcamento`: aprovado |
| Empate e texto duplicado | Preservar IDs distintos, ordem do corpus e benefícios | IDs `b`, `a` e scores 2,5 preservados | `test_empate_e_texto_duplicado_preservam_ids_distintos`: aprovado |
| Entrada grande e adversarial | Unicode/marcador especial como texto; custo > 4096; sem alteração | Texto recuperável e contagem conferida | `test_entrada_grande_unicode_e_marcador_especial`: aprovado |
| IDs duplicados | Rejeitar antes da geração dos dados | `ValueError` para corpus e candidatos | `test_rejeita_id_duplicado`: 2 parametrizações aprovadas |
| Fonte ou texto desatualizado | Rejeitar ID desconhecido ou divergência documental | `ValueError` nas 5 alterações | `test_rejeita_candidato_desatualizado`: 5 parametrizações aprovadas |
| Score inválido | Rejeitar negativo, NaN, infinito, booleano, string ou nulo | `ValueError` em todos os casos | `test_rejeita_score_invalido`: 6 parametrizações aprovadas |
| Corpus e busca incompatíveis | Rejeitar contagens N divergentes antes de gravar | Nenhuma pasta de saída criada | `test_cli_rejeita_tamanho_de_corpus_incompativel`: 2 parametrizações aprovadas |
| Integração no corpus real | 182 chunks, 75 candidatos, 4 capacidades; scores e entradas preservados | Contagens, scores e bytes das entradas conferidos | `test_cli_real_gera_quatro_instancias_preservando_entradas`: aprovado |
| Associação sem tokenizer | Validar/associar score sem computar w_i | Score associado; entrada não recebe w_i | `test_associacao_independe_do_tokenizer`: aprovado |

Os outros testes parametrizados cobrem metadados ausentes, chunk malformado,
orçamentos inválidos e texto vazio com benefício positivo. O contraexemplo
que refuta a otimalidade do guloso pertence à etapa de corretude dos seletores,
não à preparação dos dados.

## Arquivos e preservação

- `testes.xml`: resultado consolidado das etapas anteriores; a suíte própria da
	Etapa 4 é executada separadamente.
- `notebook_executado.ipynb`: células executadas, saídas e resumo das instâncias
  na execução histórica da etapa 1.
- `notebook_executado_etapa5.ipynb`, `notebook_execucao.log` e
  `validacao_notebook.json`: execução completa no commit `6b815ca`, com as
  etapas 1 a 5.
- `validacao_limpa.json`: resumo da execução e identificação do código.
- `dependencias_validacao.txt`: versões instaladas no ambiente novo.
- `../5_resultados/relatorio_preparacao.json`: custos separados, hashes e ambiente.

A execução real produziu 182 chunks de 7 documentos, 75 candidatos positivos e
as quatro capacidades 512, 1024, 2048 e 4096. O corpus tokenizado soma 74.055
tokens individuais; essa soma inclui a sobreposição herdada entre chunks e
não representa o tamanho de um prompt. Em W = 512, um candidato excede a
capacidade. Nos demais orçamentos, nenhum item excede W individualmente.

Os scripts e artefatos da AV1 foram movidos para `av1/`; seu conteúdo foi
conferido por hashes SHA-256. Os registros desta pasta documentam a execução
histórica no commit indicado acima, anterior à reorganização dos diretórios.
Por isso, o notebook executado preserva os caminhos usados naquela execução;
para executar a versão atual, utilize `../orquestrador_av2.ipynb`. Os hashes das entradas e do preparador conferem com as
saídas. O notebook AV1 agora executa em `av1/`; a célula de preparação foi ajustada
para essa localização, e a seção AV2 foi retirada dele. A verificação
Linux do mesmo notebook é executada no workflow
[`AV2 - Preparacao e notebook`](https://github.com/diegofnf/PAA_UFS_2026_2_Bispo_Diego_Marques_Gabriel_Andrade_Laryssa_Santos_Kaio_Melo_Victor/actions/workflows/av2-etapa1.yml).

## Atendimento da responsabilidade de Diego na etapa 1

| Entrega prevista | Implementação / evidência |
|---|---|
| Preservar pipeline e corpus da AV1 | Arquivos reorganizados em `av1/`, corpus preservado e tag AV1 mantida. |
| Associar custo exato em tokens e relevância | `../1_scripts/preparar_instancias.py`, encoding/versionamento fixos e testes. |
| Estruturar W = 512, 1024, 2048, 4096 | `../3_instancias/instancias.json` e execução integrada. |
| Documentar continuidade e versionamento | Seções “Organização no GitHub” e “Continuidade da AV1” do `../README.md`, relatório técnico e commit de execução. |
| Documentar tokenização e RAM versus I/O | Seção de custos e campos separados no relatório de preparação. |
| Permitir reprodução e uso pelos colegas | Notebook independente, dependências, contrato dos JSONs e workflow Linux. |

## Atendimento da Etapa 4 — Corretude e limites teóricos

Os testes da programação dinâmica incluem casos de borda, não mutação,
contraexemplo operacional da falha gulosa, comparação com força bruta em
instância pequena e invariantes da reconstrução. A prova matemática utiliza
indução sobre `DP[i][c]` e a recorrência de Bellman; a discussão da
pseudo-polinomialidade considera o valor numérico de `W` em relação ao tamanho
binário da entrada.

A Etapa 4 possui a suíte própria `../1_scripts/test_corretude_limites.py`, executada
depois das etapas anteriores. Ela reutiliza os artefatos já produzidos e cobre
o contraexemplo guloso, o oráculo por força bruta, as invariantes do
backtracking, a comparação nos quatro valores de `W` e a geração dos relatórios.

O script `../1_scripts/gerar_relatorio_corretude.py` gera os artefatos próprios da
etapa:

- `../4_selecao_contexto/contraexemplo_guloso.json`: contraexemplo operacional
	com a solução gulosa e a solução ótima da PD;
- `../5_resultados/relatorio_corretude_limites.json`: comparação por orçamento,
  ganhos de relevância e evidências da execução.

Nos quatro cenários atuais, `W` assume 512, 1024, 2048 e 4096. Isso representa
quatro instâncias de capacidade para cada seletor, ou oito combinações
algoritmo-capacidade. As 12 execuções registradas na AV1 são outra matriz
experimental: três configurações, duas cargas e duas repetições; elas não são
12 variações de `W` da AV2 e não devem ser apresentadas como tal.

Resultados principais da Etapa 4:

| W | Relevância gulosa | Relevância PD | Tokens PD |
|---:|---:|---:|---:|
| 512 | 9,6206 | 9,6206 | 370/512 |
| 1024 | 16,6484 | 16,6484 | 761/1024 |
| 2048 | 33,8168 | 33,8168 | 1905/2048 |
| 4096 | 57,5855 | 60,3138 | 4093/4096 |

Essa conclusão cobre a preparação, a seleção, a corretude operacional e os
limites teóricos da Etapa 4. A integração com uma LLM e a avaliação semântica
do contexto continuam fora do escopo da Etapa 4; a montagem do payload e a
análise de tokens são tratadas na Etapa 5, abaixo.

## Atendimento da Etapa 5 — Contexto para LLM

A Etapa 5 implementa a montagem do payload de chat e a análise de tokens sem
chamar serviço externo. O ponto de entrada oficial é `../integrar_contexto.py`,
que delega para `../1_scripts/montar_contexto_llm.py`; a análise completa está
em [`../CONTEXTO_LLM.md`](../CONTEXTO_LLM.md). Responsável: Victor Melo.

Verificações executadas:

| Verificação | Resultado |
|---|---|
| `w_i` dos 182 chunks contra `encode_ordinary` | 74 055 tokens, nenhuma divergência, nenhum `w_i` zero |
| Prompt fixo (sistema + moldura + pergunta) | 190 tokens |
| Matriz seletor × `W` × janela × estratégia × dedupe | 160 execuções, 7 repetições |
| Orçamento ajustado acima da janela | 0 execuções (o modo integral estoura em 28/80) |
| Testes da Etapa 5 | 34 aprovados |
| Suíte completa da AV2 | **92 aprovados** |

Resultados principais (janela 8 192, resposta 512, segurança 64, dedupe):

| Seletor | `W` | Chunks | `w_i` | Prompt | Overhead | Relevância | Relevância/1k |
|---|---:|---:|---:|---:|---:|---:|---:|
| Guloso | 512 | 1 | 370 | 607 | 237 | 9,6206 | 15,85 |
| Guloso | 1 024 | 2 | 761 | 1 033 | 271 | 16,6484 | 16,12 |
| Guloso | 2 048 | 5 | 1 905 | 2 304 | 396 | 33,8168 | 14,68 |
| Guloso | 4 096 | 10 | 3 820 | 4 394 | 623 | 57,5855 | 13,11 |
| PD | 4 096 | 11 | 4 093 | 4 712 | 667 | 60,3138 | 12,80 |

- A PD ganha +2,7283 de relevância em `W=4 096`, mas custa 318 tokens de prompt
  a mais e é ordens de grandeza mais cara (72,38 ms e 6,72 MB contra 0,08 ms e
  4,06 KB do guloso).
- Em 1 024 tokens de janela, nenhum chunk inteiro cabe após instruções,
  resposta e segurança; o contexto ajustado fica vazio.
- A menor janela que comporta a seleção completa é 2 048 (`W≤1 024`), 4 096
  (`W=2 048`) e 8 192 (`W=4 096`).

### Matriz de testes da Etapa 5

| Caso / requisito | Resultado esperado | Resultado observado | Evidência | Status |
|---|---|---|---|---|
| Normal: corpus real | 182 chunks, 74 055 tokens, nenhum `w_i` divergente | Confirmado | `test_corpus_real_mantem_w_i_exato` | Aprovado |
| Vazio: nenhum chunk cabe | Contexto vazio, sem estourar a janela | Confirmado | `test_ajustado_sem_chunk_que_cabe_gera_contexto_vazio` | Aprovado |
| Fronteira: janela apertada | Truncamento preenche o orçamento | Confirmado | `test_truncamento_preenche_orcamento` | Aprovado |
| Empate de relevância | Desempate por `id_chunk` crescente | `c1` antes de `c2` | `test_empate_de_relevancia_usa_id_chunk` | Aprovado |
| Entrada grande | 60 chunks respeitam o orçamento | Sem estouro, com descartes | `test_entrada_grande_respeita_orcamento` | Aprovado |
| Duplicata/sobreposição | Dedupe remove 30 palavras e economiza tokens | 57 tokens em `W=4096` | `test_dedupe_real_economiza_tokens_em_w4096` | Aprovado |
| Adversarial: `\x00` | Caractere preservado e contado | Texto e contagem conferidos | `test_caractere_de_controle_e_preservado` | Aprovado |
| Hipótese: PD sempre melhor | Pode ser refutada quando `W≤2048` | PD empata com guloso em `W=2048` | `test_pd_nao_supera_guloso_em_w2048` | Aprovado |
| Orçamento excedido | Modo integral pode estourar | Estouro registrado | `test_integral_pode_estourar_janela` | Aprovado |
| Ponto de entrada oficial | `av2/integrar_contexto.py` delega para `main` | `callable(main)` | `test_integrar_contexto_expoe_main` | Aprovado |

Artefatos: `../7_contexto_llm/contextos.json`,
`../7_contexto_llm/tabela_contexto_llm.csv`,
`../7_contexto_llm/prompt_exemplo.md`,
`../7_contexto_llm/grafico_prompt_por_w.png`,
`../7_contexto_llm/grafico_folga_janela.png`,
`../7_contexto_llm/grafico_latencia_contexto.png` e
`../5_resultados/relatorio_contexto_llm.json`.
