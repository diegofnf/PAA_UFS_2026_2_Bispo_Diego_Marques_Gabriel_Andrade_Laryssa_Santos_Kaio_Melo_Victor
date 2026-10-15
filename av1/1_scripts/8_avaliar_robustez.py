"""Etapa 8 — Robustez, Taxa de Falhas e Baseline de Referência.

Este script é aditivo: ele apenas lê os artefatos das etapas 1 a 4 e não modifica
nenhum deles. Ele fecha três lacunas explícitas do edital que não eram cobertas
pelas etapas anteriores.

1. Seção 5.2, item 5 — comparação com biblioteca ou ferramenta de referência.
   O Merge Sort implementado pela equipe é confrontado com duas referências da
   biblioteca padrão do Python: `sorted()` (Timsort) e `heapq.nsmallest()`. Fica
   explícito no relatório que essas duas referências são usadas *apenas* como
   baseline de comparação e que a ordenação do pipeline é a da equipe. A
   comparação também serve de teste de corretude independente: a sequência de
   Top-k produzida pela equipe tem de ser idêntica à das duas referências.

2. Seção 7.3 — taxa de falhas, resultados vazios ou itens irrelevantes.
   Uma bateria de consultas patológicas (nula, só espaços, só stopwords, fora do
   vocabulário, mista) é executada nas três configurações para medir quantas
   execuções terminam com exceção e quantas devolvem lista vazia. O contrato do
   pipeline é degradar para resultado vazio com aviso explícito, nunca levantar
   exceção.

3. Seção 5.1 — casos de borda. As mesmas consultas documentam o comportamento
   observável nos limites do domínio (consulta sem termos recuperáveis).

Saídas:
    - 7_resultados/avaliacao_robustez.json  (evidência estruturada completa)
    - 7_resultados/tabela_robustez.csv      (taxa de falhas por configuração)
    - 7_resultados/tabela_baseline_ordenacao.csv (Merge Sort vs. referências)
"""

# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DE AMBIENTE
# ==============================================================================

import argparse
import csv
import heapq
import importlib.util
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path


def configurar_saida_padrao() -> None:
    """Garante saída UTF-8 nos consoles legados do Windows."""
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# ==============================================================================
# 2. PROTOCOLO DE MEDIÇÃO
# ==============================================================================

def medir(operacao, repeticoes: int = 5, aquecimentos: int = 2) -> float:
    """Executa `operacao` e devolve a mediana do tempo em milissegundos.

    O aquecimento repete-se antes de cada medição para descontar importações
    tardias e o first-touch das páginas de memória, e a mediana descarta picos
    de contenção da máquina hospedeira, que não é dedicada à medição.
    """
    for _ in range(max(aquecimentos, 1)):
        operacao()

    amostras = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        operacao()
        amostras.append((time.perf_counter() - inicio) * 1000.0)
    return statistics.median(amostras)


def metricas_ordenacao_zeradas() -> dict:
    """Cria o contador de métricas exigido por merge_sort/merge da Etapa 4."""
    return {
        "movimentacoes": 0,
        "chamadas_recursivas": 0,
        "profundidade_maxima": 0,
        "empates_score": 0,
        "comparacoes_score": 0,
        "comparacoes_id_chunk": 0,
        "comparacoes_totais": 0,
    }


def carregar_modulo(caminho: Path, nome: str):
    """Importa dinamicamente um script do pipeline pelo caminho."""
    especificacao = importlib.util.spec_from_file_location(nome, caminho)
    if especificacao is None or especificacao.loader is None:
        raise ImportError(f"Não foi possível carregar o módulo: {caminho}")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def carregar_json(caminho: Path):
    """Lê um artefato JSON do pipeline com encoding UTF-8."""
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


# ==============================================================================
# 3. CHAVE DE ORDENAÇÃO E BASELINES DE REFERÊNCIA
# ==============================================================================

def chave_ordenacao(candidato: dict) -> tuple[float, str]:
    """Chave canônica da ordenação da Etapa 4: score decrescente, id crescente.

    A chave é um par (valor, chave de desempate) e é usada para expressar o
    critério da equipe na linguagem das bibliotecas de referência. Ela existe
    apenas para os baselines: o critério equivalente na implementação própria
    está em `merge()` (Etapa 4), que compara score e depois id_chunk.
    """
    return (-float(candidato["score"]), str(candidato["id_chunk"]))


def ordenar_com_referencia(candidatos: list[dict]) -> list[dict]:
    """Baseline 1: `sorted()` da biblioteca padrão (Timsort).

    Este é o algoritmo de ordenação nativo do Python. Ele não faz parte do
    pipeline entregue; é usado exclusivamente como referência de comparação,
    conforme a Seção 5.2, item 5 do edital.
    """
    return sorted(candidatos, key=chave_ordenacao)


def selecionar_com_referencia(candidatos: list[dict], k: int) -> list[dict]:
    """Baseline 2: `heapq.nsmallest()`, uma seleção Top-k por heap.

    `nsmallest` com a chave canônica devolve exatamente os k menores pares
    (-score, id_chunk), isto é, os k candidatos mais bem colocados. A diferença
    de projeto em relação ao Merge Sort é relevante: aqui não há ordenação
    completa do conjunto, apenas a manutenção de um heap de tamanho k.
    """
    return heapq.nsmallest(k, candidatos, key=chave_ordenacao)


# ==============================================================================
# 4. GERADOR DE CARGAS SINTÉTICAS PARA A VARREDURA DE ESCALA
# ==============================================================================

def gerar_candidatos_sinteticos(n: int, semente: int) -> list[dict]:
    """Gera n candidatos com distribuição de scores assimétrica e empates.

    O corpus real produz apenas 75 candidatos por consulta, o que é estreito
    demais para observar crescimento assintótico. Para a varredura de escala são
    geradas cargas sintéticas com a mesma forma do perfil real: muitos scores
    baixos e poucos altos. Os scores são sorteados de um vocabulário de valores
    menor que n, de modo que os empates ocorrem na mesma ordem de grandeza
    observada no artefato real (14 empates em 75 candidatos). A geração é
    determinística a partir de `semente`, portanto a varredura é reprodutível.

    As cargas sintéticas servem apenas para comparar algoritmos de ordenação
    entre si sobre a mesma entrada; elas não substituem as medições do corpus
    real, que estão nas Etapas 5 a 7.
    """
    rng = random.Random(semente)

    # Vocabulário de 2n valores de score: tirar n amostras de 2n valores distintos
    # produz cerca de 20% de empates, a mesma ordem de grandeza dos 18,7% medidos
    # no artefato real da Etapa 4 (14 empates em 75 candidatos). A taxa efetiva de
    # cada carga é registrada na saída, e não inferida desta escolha.
    tamanho_vocabulario = max(2 * n, 1)
    vocabulario = sorted(
        {round(rng.paretovariate(1.8), 4) or 0.0001 for _ in range(tamanho_vocabulario)},
        reverse=True,
    )

    return [
        {
            "id_chunk": f"chunk_{indice:05d}",
            "score": rng.choice(vocabulario),
        }
        for indice in range(n)
    ]


# ==============================================================================
# 5. REGRESSÃO LOG-LOG DO CUSTO DE ORDENAÇÃO
# ==============================================================================

def expoente_log_log(xs: list[float], ys: list[float]) -> float | None:
    """Expoente p do ajuste y = a * x^p por mínimos quadrados em espaço log-log."""
    if len(xs) < 2:
        return None
    pontos = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x > 0 and y > 0]
    if len(pontos) < 2:
        return None

    media_x = sum(p[0] for p in pontos) / len(pontos)
    media_y = sum(p[1] for p in pontos) / len(pontos)
    numerador = sum((px - media_x) * (py - media_y) for px, py in pontos)
    denominador = sum((px - media_x) ** 2 for px, _ in pontos)
    if denominador == 0:
        return None
    return numerador / denominador


# ==============================================================================
# 6. PARTE A — TAXA DE FALHAS E RESULTADOS VAZIOS (SEÇÃO 7.3)
# ==============================================================================

CONSULTAS_ROBUSTEZ = [
    ("relevante", "critérios para atribuição de bolsas"),
    ("relevante", "aproveitamento de estudos"),
    ("relevante", "estrutura curricular do mestrado"),
    ("nula", ""),
    ("nula", "   "),
    ("nula", "!!! ??? ---"),
    ("apenas_stopwords", "de da do para com os as um uma"),
    ("fora_do_vocabulario", "xilofone quântico blockchain astrofísica"),
    ("mista", "de bolsas xilofone"),
]


def executar_configuracao(
    modo: str,
    consulta: str,
    k: int,
    chunks: list[dict],
    chunks_map: dict[str, dict],
    indice_invertido: dict,
    estatisticas_corpus: tuple[int, float, dict[str, int]],
    modulo_busca,
) -> dict:
    """Executa uma configuração sobre uma consulta e resume o resultado observável.

    Devolve o status da execução, quantos candidatos foram recuperados e se o
    Top-k resultou vazio. Exceções não são propagadas: elas são o dado
    experimental de falha, e o campo `erro` registra o tipo e a mensagem.
    """
    resultado = {
        "modo": modo,
        "status": "sucesso",
        "erro": None,
        "total_candidatos": 0,
        "resultados_retornados": 0,
        "aviso": None,
        "top_k_ids": [],
    }

    try:
        if modo == "linear":
            candidatos, metricas = modulo_busca.buscar_linear(
                chunks, consulta, metrica="bm25", estatisticas_corpus=estatisticas_corpus
            )
        else:
            candidatos, metricas = modulo_busca.buscar_indexada(
                indice_invertido,
                chunks_map,
                consulta,
                metrica="bm25",
                estatisticas_corpus=estatisticas_corpus,
            )

        metricas_merge = metricas_ordenacao_zeradas()
        ordenados = modulo_busca.merge_sort(list(candidatos), metricas_merge)
        top_k = modulo_busca.selecionar_topk(ordenados, k)

        resultado["total_candidatos"] = len(candidatos)
        resultado["resultados_retornados"] = len(top_k)
        resultado["aviso"] = metricas.get("aviso")
        resultado["top_k_ids"] = [item["id_chunk"] for item in top_k]
        resultado["comparacoes_merge_sort"] = metricas_merge["comparacoes_totais"]
    except Exception as erro:  # noqa: BLE001 - a exceção é o dado experimental de falha
        resultado["status"] = "falha"
        resultado["erro"] = f"{type(erro).__name__}: {erro}"

    resultado["resultado_vazio"] = (
        resultado["status"] == "sucesso" and resultado["resultados_retornados"] == 0
    )
    return resultado


def avaliar_robustez(
    consultas_bateria: list[tuple[str, str]],
    chunks: list[dict],
    chunks_map: dict[str, dict],
    indice_invertido: dict,
    estatisticas_corpus: tuple[int, float, dict[str, int]],
    k: int,
    modulo_busca,
) -> dict:
    """Executa a bateria de consultas patológicas nas duas configurações de busca."""
    modos = ["linear", "indexada_com_merge_sort"]
    detalhes = []
    sintese = {
        modo: {
            "execucoes": 0,
            "falhas_excecao": 0,
            "resultados_vazios": 0,
            "taxa_falhas": 0.0,
            "taxa_resultados_vazios": 0.0,
        }
        for modo in modos
    }

    for categoria, consulta in consultas_bateria:
        registro = {"categoria": categoria, "consulta": consulta, "configuracoes": {}}
        for modo in modos:
            modo_busca = "linear" if modo == "linear" else "indexada"
            execucao = executar_configuracao(
                modo_busca,
                consulta,
                k,
                chunks,
                chunks_map,
                indice_invertido,
                estatisticas_corpus,
                modulo_busca,
            )
            registro["configuracoes"][modo] = execucao

            agregado = sintese[modo]
            agregado["execucoes"] += 1
            if execucao["status"] == "falha":
                agregado["falhas_excecao"] += 1
            if execucao["resultado_vazio"]:
                agregado["resultados_vazios"] += 1

        # Invariante de consistência entre as duas estratégias de recuperação:
        # para toda consulta, a configuração indexada e a configuração linear
        # têm de devolver o mesmo Top-k. Divergência aqui é defeito de corretude.
        linear = registro["configuracoes"]["linear"]
        indexada = registro["configuracoes"]["indexada_com_merge_sort"]
        registro["top_k_equivalente_entre_configuracoes"] = (
            linear["top_k_ids"] == indexada["top_k_ids"]
        )

        print(
            f"  [{categoria:<18}] consulta={consulta!r} "
            f"linear={linear['resultados_retornados']:>2} itens | "
            f"indexada={indexada['resultados_retornados']:>2} itens | "
            f"status={linear['status']}/{indexada['status']}"
        )
        detalhes.append(registro)

    for modo, agregado in sintese.items():
        execucoes = max(agregado["execucoes"], 1)
        agregado["taxa_falhas"] = round(agregado["falhas_excecao"] / execucoes, 4)
        agregado["taxa_resultados_vazios"] = round(agregado["resultados_vazios"] / execucoes, 4)

    return {
        "k": k,
        "total_consultas_bateria": len(consultas_bateria),
        "consultas": detalhes,
        "sintese": sintese,
        "todas_os_top_k_equivalentes": all(
            registro["top_k_equivalente_entre_configuracoes"] for registro in detalhes
        ),
    }


# ==============================================================================
# 7. PARTE B — BASELINE DE REFERÊNCIA PARA A ORDENAÇÃO (SEÇÃO 5.2, ITEM 5)
# ==============================================================================

def comparar_no_tamanho(
    candidatos: list[dict],
    k: int,
    modulo_busca,
    repeticoes: int,
) -> dict:
    """Compara Merge Sort da equipe, `sorted()` e `heapq.nsmallest()` no mesmo input.

    As três implementações recebem exatamente a mesma lista de candidatos. A
    contagem de comparações só existe para o Merge Sort da equipe, porque as
    rotinas da biblioteca padrão não expõem esse contador; por isso o número de
    comparações é cruzado com o tempo, e não substituído por ele.
    """
    metricas_merge = metricas_ordenacao_zeradas()
    ordenados_equipe = modulo_busca.merge_sort(list(candidatos), metricas_merge)
    top_k_equipe = modulo_busca.selecionar_topk(ordenados_equipe, k)

    ordenados_referencia = ordenar_com_referencia(candidatos)
    top_k_sorted = ordenados_referencia[:k]
    top_k_heapq = selecionar_com_referencia(candidatos, k)

    tempo_equipe = medir(
        lambda: modulo_busca.merge_sort(list(candidatos), metricas_ordenacao_zeradas()),
        repeticoes,
    )
    tempo_sorted = medir(lambda: ordenar_com_referencia(candidatos), repeticoes)
    tempo_heapq = medir(lambda: selecionar_com_referencia(candidatos, k), repeticoes)

    ids_equipe = [item["id_chunk"] for item in top_k_equipe]
    ids_sorted = [item["id_chunk"] for item in top_k_sorted]
    ids_heapq = [item["id_chunk"] for item in top_k_heapq]

    # A ordenação completa também é confrontada posição a posição, e não apenas
    # no recorte do Top-k: é isso que prova que o critério de desempate da
    # equipe coincide com o da referência em todas as posições.
    ids_equipe_completo = [item["id_chunk"] for item in ordenados_equipe]
    ids_sorted_completo = [item["id_chunk"] for item in ordenados_referencia]

    scores = [item["score"] for item in candidatos]
    return {
        "n": len(candidatos),
        "k": k,
        "scores_distintos": len(set(scores)),
        "empates_score": len(scores) - len(set(scores)),
        "comparacoes_merge_sort": metricas_merge["comparacoes_totais"],
        "comparacoes_score": metricas_merge["comparacoes_score"],
        "comparacoes_id_chunk": metricas_merge["comparacoes_id_chunk"],
        "movimentacoes_merge_sort": metricas_merge["movimentacoes"],
        "chamadas_recursivas": metricas_merge["chamadas_recursivas"],
        "profundidade_maxima": metricas_merge["profundidade_maxima"],
        "tempo_ms_merge_sort_equipe": round(tempo_equipe, 6),
        "tempo_ms_sorted_timsort": round(tempo_sorted, 6),
        "tempo_ms_heapq_nsmallest": round(tempo_heapq, 6),
        "razao_referencia_sobre_equipe": (
            round(tempo_sorted / tempo_equipe, 4) if tempo_equipe > 0 else None
        ),
        "ordem_completa_identica_a_sorted": ids_equipe_completo == ids_sorted_completo,
        "top_k_identico_a_sorted": ids_equipe == ids_sorted,
        "top_k_identico_a_heapq": ids_equipe == ids_heapq,
    }


def avaliar_baseline_ordenacao(
    candidatos: list[dict],
    k: int,
    modulo_busca,
    repeticoes: int,
    tamanhos: list[int],
    semente: int,
) -> dict:
    """Executa a comparação com as referências na carga real e na varredura sintética."""
    print("  Carga real (candidatos da Etapa 4):")
    carga_real = comparar_no_tamanho(candidatos, k, modulo_busca, repeticoes)
    print(
        f"    n={carga_real['n']} | empates={carga_real['empates_score']} | "
        f"equipe={carga_real['tempo_ms_merge_sort_equipe']:.4f} ms | "
        f"sorted={carga_real['tempo_ms_sorted_timsort']:.4f} ms | "
        f"ordem idêntica={carga_real['ordem_completa_identica_a_sorted']}"
    )

    print("  Varredura de escala (cargas sintéticas):")
    varredura = []
    for n in tamanhos:
        sinteticos = gerar_candidatos_sinteticos(n, semente)
        amostra = comparar_no_tamanho(sinteticos, k, modulo_busca, repeticoes)
        amostra["carga"] = "sintetica"
        varredura.append(amostra)
        print(
            f"    n={amostra['n']:>5} | empates={amostra['empates_score']:>5} | "
            f"comparacoes={amostra['comparacoes_merge_sort']:>7} | "
            f"equipe={amostra['tempo_ms_merge_sort_equipe']:>8.4f} ms | "
            f"sorted={amostra['tempo_ms_sorted_timsort']:>8.4f} ms | "
            f"top-k ok={amostra['top_k_identico_a_sorted']}"
        )

    ns = [amostra["n"] for amostra in varredura]
    ajustes = {
        "merge_sort_equipe_tempo": expoente_log_log(
            ns, [amostra["tempo_ms_merge_sort_equipe"] for amostra in varredura]
        ),
        "sorted_timsort_tempo": expoente_log_log(
            ns, [amostra["tempo_ms_sorted_timsort"] for amostra in varredura]
        ),
        "heapq_nsmallest_tempo": expoente_log_log(
            ns, [amostra["tempo_ms_heapq_nsmallest"] for amostra in varredura]
        ),
        "merge_sort_equipe_comparacoes": expoente_log_log(
            ns, [amostra["comparacoes_merge_sort"] for amostra in varredura]
        ),
    }

    return {
        "carga_real": carga_real,
        "varredura": varredura,
        "expoentes_log_log": {chave: (round(valor, 4) if valor is not None else None)
                              for chave, valor in ajustes.items()},
        "todas_as_ordens_identicas": all(
            amostra["ordem_completa_identica_a_sorted"] for amostra in varredura
        ) and carga_real["ordem_completa_identica_a_sorted"],
        "todos_os_top_k_identicos": all(
            amostra["top_k_identico_a_sorted"] and amostra["top_k_identico_a_heapq"]
            for amostra in varredura
        ) and carga_real["top_k_identico_a_sorted"] and carga_real["top_k_identico_a_heapq"],
    }


# ==============================================================================
# 8. PERSISTÊNCIA DAS EVIDÊNCIAS
# ==============================================================================

def gravar_json(caminho: Path, dados: dict) -> None:
    """Grava um artefato JSON com encoding UTF-8."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def gravar_csv(caminho: Path, cabecalho: list[str], linhas: list[list]) -> None:
    """Grava uma tabela CSV com separador ponto e vírgula, como nas etapas anteriores."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


def gravar_tabela_robustez(caminho: Path, robustez: dict) -> None:
    """Consolida a taxa de falhas por configuração em CSV."""
    linhas = []
    for registro in robustez["consultas"]:
        for modo, execucao in registro["configuracoes"].items():
            linhas.append([
                registro["categoria"],
                registro["consulta"],
                modo,
                execucao["status"],
                execucao["total_candidatos"],
                execucao["resultados_retornados"],
                "sim" if execucao["resultado_vazio"] else "nao",
                execucao["erro"] or "",
            ])
    gravar_csv(
        caminho,
        ["categoria", "consulta", "configuracao", "status",
         "total_candidatos", "resultados_retornados", "resultado_vazio", "erro"],
        linhas,
    )


def gravar_tabela_baseline(caminho: Path, baseline: dict) -> None:
    """Consolida a comparação Merge Sort vs. referências da biblioteca padrão em CSV."""
    linhas = []
    for amostra in [baseline["carga_real"]] + baseline["varredura"]:
        linhas.append([
            amostra["n"],
            amostra["scores_distintos"],
            amostra["empates_score"],
            amostra["comparacoes_merge_sort"],
            amostra["tempo_ms_merge_sort_equipe"],
            amostra["tempo_ms_sorted_timsort"],
            amostra["tempo_ms_heapq_nsmallest"],
            amostra["razao_referencia_sobre_equipe"],
            "sim" if amostra["ordem_completa_identica_a_sorted"] else "nao",
        ])
    gravar_csv(
        caminho,
        ["n", "scores_distintos", "empates_score", "comparacoes_merge_sort",
         "ms_merge_sort_equipe", "ms_sorted_timsort", "ms_heapq_nsmallest",
         "razao_sorted_sobre_equipe", "ordem_identica_a_sorted"],
        linhas,
    )


# ==============================================================================
# 9. INTERFACE DE LINHA DE COMANDO
# ==============================================================================

def construir_parser() -> argparse.ArgumentParser:
    base = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Etapa 8 — robustez, taxa de falhas e baseline de referência."
    )
    parser.add_argument("--chunks", type=Path, default=base / "4_chunks" / "chunks.json",
                        help="Chunks da Etapa 2 (padrão: 4_chunks/chunks.json).")
    parser.add_argument("--indice", type=Path, default=base / "5_indexacao" / "indice_invertido.json",
                        help="Índice invertido da Etapa 3 (padrão: 5_indexacao/indice_invertido.json).")
    parser.add_argument("--candidatos", type=Path,
                        default=base / "6_busca_lexical" / "candidatos_busca.json",
                        help="Artefato de candidatos da Etapa 4 usado como carga real da comparação "
                             "(padrão: 6_busca_lexical/candidatos_busca.json).")
    parser.add_argument("--consulta", type=str, default="critérios para atribuição de bolsas",
                        help="Consulta usada nas consultas de robustez marcadas como relevantes.")
    parser.add_argument("--k", type=int, default=5, help="Tamanho do Top-k (padrão: 5).")
    parser.add_argument("--repeticao", type=int, default=5,
                        help="Repetições internas por medição de tempo (padrão: 5).")
    parser.add_argument("--pontos", type=int, default=7,
                        help="Quantidade de pontos da varredura de escala (padrão: 7).")
    parser.add_argument("--semente", type=int, default=20260923,
                        help="Semente das cargas sintéticas, para reprodutibilidade (padrão: 20260923).")
    parser.add_argument("--saida", type=Path,
                        default=base / "7_resultados" / "avaliacao_robustez.json",
                        help="JSON consolidado de saída (padrão: 7_resultados/avaliacao_robustez.json).")
    parser.add_argument("--tabela-robustez", type=Path,
                        default=base / "7_resultados" / "tabela_robustez.csv",
                        help="CSV da taxa de falhas (padrão: 7_resultados/tabela_robustez.csv).")
    parser.add_argument("--tabela-baseline", type=Path,
                        default=base / "7_resultados" / "tabela_baseline_ordenacao.csv",
                        help="CSV do baseline de ordenação "
                             "(padrão: 7_resultados/tabela_baseline_ordenacao.csv).")
    return parser


def main() -> int:
    configurar_saida_padrao()
    argumentos = construir_parser().parse_args()

    base = Path(__file__).resolve().parent.parent
    modulo_busca = carregar_modulo(base / "1_scripts" / "4_buscar_e_ordenar.py", "busca_e_ordenar")

    print("Carregando artefatos das etapas 2 a 4...")
    dados_chunks = carregar_json(argumentos.chunks)
    chunks = dados_chunks["chunks"] if isinstance(dados_chunks, dict) else dados_chunks
    chunks_map = {chunk["id_chunk"]: chunk for chunk in chunks}

    dados_indice = carregar_json(argumentos.indice)
    indice_invertido = dados_indice.get("indice_invertido", dados_indice) \
        if isinstance(dados_indice, dict) else dados_indice

    estatisticas_corpus = modulo_busca.calcular_estatisticas_corpus(chunks)
    print(f"  Corpus: {len(chunks)} chunks | vocabulário: {len(indice_invertido)} termos")

    dados_candidatos = carregar_json(argumentos.candidatos)
    candidatos_reais = dados_candidatos["candidatos"] if isinstance(dados_candidatos, dict) \
        else dados_candidatos
    print(f"  Candidatos da Etapa 4: {len(candidatos_reais)}")

    # A consulta relevante da bateria de robustez é a informada na linha de comando.
    consulta_padrao = CONSULTAS_ROBUSTEZ[0][1]
    consultas_bateria = [
        (categoria, argumentos.consulta if categoria == "relevante" and consulta == consulta_padrao
         else consulta)
        for categoria, consulta in CONSULTAS_ROBUSTEZ
    ]

    print("\n[1/2] Bateria de robustez (taxa de falhas e resultados vazios)...")
    robustez = avaliar_robustez(
        consultas_bateria, chunks, chunks_map, indice_invertido,
        estatisticas_corpus, argumentos.k, modulo_busca
    )

    print("\n[2/2] Baseline de referência para a ordenação...")
    tamanhos = sorted({max(int(len(candidatos_reais) * (2 ** passo)), 2)
                       for passo in range(argumentos.pontos)})
    baseline = avaliar_baseline_ordenacao(
        candidatos_reais,
        argumentos.k,
        modulo_busca,
        argumentos.repeticao,
        tamanhos,
        argumentos.semente,
    )

    relatorio = {
        "metadados": {
            "etapa": 8,
            "objetivo": "Robustez, taxa de falhas e baseline de referência "
                        "(Seções 5.1, 5.2 item 5 e 7.3 do edital).",
            "gerado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
            "sistema_operacional": f"{platform.system()} {platform.release()}",
            "arquitetura": platform.machine(),
            "versao_python": platform.python_version(),
            "interpretador": sys.executable,
            "artefatos_de_entrada": {
                "chunks": str(argumentos.chunks),
                "indice_invertido": str(argumentos.indice),
                "candidatos_etapa_4": str(argumentos.candidatos),
            },
            "k": argumentos.k,
            "repeticao_interna_por_medicao": argumentos.repeticao,
            "semente_cargas_sinteticas": argumentos.semente,
            "baselines_de_referencia": [
                "sorted() — Timsort da biblioteca padrão do Python (ordenação completa)",
                "heapq.nsmallest() — seleção Top-k por heap da biblioteca padrão do Python",
            ],
            "nota_metodologica": (
                "As duas referências são usadas apenas como baseline de comparação. "
                "A ordenação entregue pelo pipeline é o Merge Sort implementado pela "
                "equipe em 1_scripts/4_buscar_e_ordenar.py, que não usa sorted() nem "
                "list.sort(). As cargas sintéticas da varredura servem exclusivamente "
                "para comparar os algoritmos entre si sobre a mesma entrada."
            ),
        },
        "robustez": robustez,
        "baseline_ordenacao": baseline,
    }

    gravar_json(argumentos.saida, relatorio)
    gravar_tabela_robustez(argumentos.tabela_robustez, robustez)
    gravar_tabela_baseline(argumentos.tabela_baseline, baseline)

    print("\nEvidências gravadas:")
    print(f"  - {argumentos.saida}")
    print(f"  - {argumentos.tabela_robustez}")
    print(f"  - {argumentos.tabela_baseline}")

    print("\nResumo da robustez (Seção 7.3):")
    for modo, agregado in robustez["sintese"].items():
        print(
            f"  {modo:<28} execuções={agregado['execucoes']} | "
            f"falhas={agregado['falhas_excecao']} ({agregado['taxa_falhas']:.1%}) | "
            f"resultados vazios={agregado['resultados_vazios']} "
            f"({agregado['taxa_resultados_vazios']:.1%})"
        )
    print(f"  Top-k equivalente entre as duas configurações: "
          f"{'sim' if robustez['todas_os_top_k_equivalentes'] else 'NÃO'}")

    print("\nResumo do baseline de ordenação (Seção 5.2, item 5):")
    real = baseline["carga_real"]
    print(f"  Carga real (n={real['n']}): Merge Sort da equipe em "
          f"{real['tempo_ms_merge_sort_equipe']:.4f} ms vs. sorted() em "
          f"{real['tempo_ms_sorted_timsort']:.4f} ms "
          f"({real['razao_referencia_sobre_equipe']:.2f}x)")
    print(f"  Ordem completa idêntica à referência: "
          f"{'sim' if baseline['todas_as_ordens_identicas'] else 'NÃO'}")
    print(f"  Top-k idêntico às duas referências: "
          f"{'sim' if baseline['todos_os_top_k_identicos'] else 'NÃO'}")
    print(f"  Expoentes log-log: {baseline['expoentes_log_log']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
