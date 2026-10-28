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
- `notebook_executado.ipynb`: células executadas, saídas e resumo das instâncias.
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
do contexto continuam fora do escopo desta execução.
