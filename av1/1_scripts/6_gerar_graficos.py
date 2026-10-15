"""Etapa 6 — Geração de Gráficos e Consolidação Tabular dos Resultados Experimentais.

Atende à Seção 7.3 do edital ("Apresente resultados em tabelas e inclua pelo menos
um gráfico") consumindo exclusivamente os artefatos JSON produzidos pelas etapas 1 a 5.

Figuras geradas em `7_resultados/`:

1. `grafico_tempo_execucao.png` ........... tempo total médio por configuração (12 baterias);
2. `grafico_busca_comparativo.png` ........ busca linear vs. indexada: tempo e trabalho realizado;
3. `grafico_escalabilidade_merge_sort.png`  comparações empíricas do Merge Sort vs. Θ(n log n);
4. `grafico_zipf.png` ..................... distribuição de vocabulário (Lei de Zipf, log-log);
5. `grafico_memoria_configuracoes.png` .... pico de memória residente por configuração;
6. `grafico_etapas_pipeline.png` .......... custo temporal de cada etapa do pipeline.

Além disso, consolida a tabela `7_resultados/tabela_resultados.csv`.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import random
import re
import statistics
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

# ==============================================================================
# 1. PALETA, FORMATAÇÃO E ESTILO
# ==============================================================================

CORES_CONFIG = ["#dc2626", "#1d4ed8", "#059669"]
COR_DESTAQUE = "#1d4ed8"
COR_REFERENCIA = "#94a3b8"
COR_NEUTRA = "#475569"
COR_INGESTAO = ["#7c3aed", "#0891b2", "#1d4ed8", "#dc2626", "#059669", "#ea580c"]


def configurar_saida_padrao() -> None:
    """Força UTF-8 em stdout/stderr para não quebrar em consoles legados do Windows (cp1252)."""
    for fluxo in (sys.stdout, sys.stderr):
        if fluxo is not None and hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8", errors="replace")


def configurar_estilo() -> None:
    """Aplica um estilo único a todas as figuras do relatório."""
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "--",
            "axes.axisbelow": True,
            "legend.frameon": False,
        }
    )


def milhar(valor: float) -> str:
    """Formata um número inteiro com ponto como separador de milhar (padrão pt-BR)."""
    return f"{valor:,.0f}".replace(",", ".")


def decimal(valor: float, casas: int = 2) -> str:
    """Formata um número decimal com vírgula (padrão pt-BR)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def encurtar_rotulo(nome_configuracao: str) -> str:
    """Converte 'Configuração 1 (Baseline — Busca Linear)' em rótulo curto para eixos."""
    for numero in (1, 2, 3):
        nome_configuracao = nome_configuracao.replace(
            f"Configuração {numero} (", f"C{numero} ("
        )
    return nome_configuracao


def _sufixo_carga(nome_carga: str) -> str:
    """Deriva um sufixo de coluna estável a partir do nome da carga experimental.

    'Carga 1 (Corpus Integral)' -> 'carga_1'; o descritor entre parênteses é
    editorial e pode mudar sem quebrar o cabeçalho do CSV.
    """
    base = nome_carga.split("(")[0].strip().lower()
    return re.sub(r"[^0-9a-z]+", "_", base).strip("_") or "carga"


# ==============================================================================
# 2. CARREGAMENTO DOS ARTEFATOS
# ==============================================================================


def carregar_json(caminho: Path) -> dict:
    """Lê um artefato JSON do pipeline em UTF-8."""
    if not caminho.exists():
        raise FileNotFoundError(f"Artefato não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def carregar_modulo_busca(caminho: Path):
    """Importa dinamicamente `4_buscar_e_ordenar.py` (o nome do arquivo inicia com dígito)."""
    especificacao = importlib.util.spec_from_file_location("buscar_e_ordenar", caminho)
    if especificacao is None or especificacao.loader is None:
        raise ImportError(f"Não foi possível carregar o módulo de busca: {caminho}")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def resumir_por_configuracao(experimentos: dict) -> list[dict]:
    """Agrega as execuções bem-sucedidas de cada configuração experimental.

    A síntese por configuração passou a ser aninhada por carga depois que o
    protocolo da Etapa 5 deixou de usar duas cargas apontando para o mesmo
    arquivo: hoje "Carga 1" é o corpus integral (182 chunks) e "Carga 2" é um
    subconjunto real (91 chunks), de modo que agregá-las num único tempo médio
    misturaria regimes de tamanho e esconderia o efeito de n. O tempo global da
    configuração é exposto separadamente em `tempo_global_ms`.
    """
    resumos = []
    for nome_configuracao, sintese in experimentos["sintese_metricas"].items():
        execucoes = [
            e
            for e in experimentos["execucoes"]
            if e.get("configuracao") == nome_configuracao and e.get("status") == "sucesso"
        ]
        tempos = [e["tempo_execucao_ms"] for e in execucoes]
        memorias = [
            e["pico_memoria_mb"]
            for e in execucoes
            if isinstance(e.get("pico_memoria_mb"), (int, float))
        ]
        cargas = {
            nome_carga: {
                "tempo_medio_ms": dados["tempo_medio_ms"],
                "desvio_padrao_ms": dados["desvio_padrao_ms"],
                "amostras": dados["amostras"],
            }
            for nome_carga, dados in sintese.items()
        }
        resumos.append(
            {
                "configuracao": nome_configuracao,
                "rotulo": encurtar_rotulo(nome_configuracao),
                "modo_busca": execucoes[0]["modo_busca"] if execucoes else "-",
                "metrica_score": execucoes[0]["metrica_score"] if execucoes else "-",
                "amostras": len(tempos),
                "cargas": cargas,
                "tempo_global_ms": statistics.fmean(tempos) if tempos else 0.0,
                "tempo_desvio_ms": statistics.pstdev(tempos) if len(tempos) > 1 else 0.0,
                "tempo_min_ms": min(tempos) if tempos else 0.0,
                "tempo_max_ms": max(tempos) if tempos else 0.0,
                "tempos": tempos,
                "memoria_media_mb": statistics.fmean(memorias) if memorias else 0.0,
                "memoria_max_mb": max(memorias) if memorias else 0.0,
            }
        )
    return resumos


# ==============================================================================
# 3. FIGURA 1 — TEMPO TOTAL POR CONFIGURAÇÃO
# ==============================================================================


def figura_tempo_execucao(resumos: list[dict], destino: Path) -> None:
    """Compara o tempo médio por configuração, separando o corpus integral do reduzido.

    As duas cargas deixaram de compartilhar o mesmo arquivo de chunks, então o
    tempo do corpus integral (182 chunks) e o do reduzido (91 chunks) são
    grandezas distintas e não devem ser fundidas numa média única: fazê-lo
    misturaria o efeito de n com o da configuração. O gráfico exibe os dois
    grupos lado a lado, um por carga.
    """
    nomes_cargas = list(resumos[0]["cargas"].keys()) if resumos else []
    largura = 0.8 / max(len(nomes_cargas), 1)
    figura, eixo = plt.subplots(figsize=(10.5, 5.8))

    for indice_carga, nome_carga in enumerate(nomes_cargas):
        deslocamento = (indice_carga - (len(nomes_cargas) - 1) / 2) * largura
        medias = [r["cargas"][nome_carga]["tempo_medio_ms"] for r in resumos]
        desvios = [r["cargas"][nome_carga]["desvio_padrao_ms"] for r in resumos]
        posicoes = [i + deslocamento for i in range(len(resumos))]

        eixo.bar(
            posicoes,
            medias,
            yerr=desvios,
            width=largura * 0.92,
            capsize=5,
            color=CORES_CONFIG if len(nomes_cargas) == 1 else None,
            edgecolor="white",
            linewidth=0.8,
            error_kw={"ecolor": COR_NEUTRA, "elinewidth": 1.4},
            zorder=3,
            label=nome_carga,
        )

        for posicao, media, desvio in zip(posicoes, medias, desvios):
            eixo.text(
                posicao,
                media + desvio + max(medias) * 0.03,
                f"{decimal(media)}",
                ha="center",
                va="bottom",
                fontsize=9,
                color=COR_NEUTRA,
            )

    eixo.set_xticks(range(len(resumos)))
    eixo.set_xticklabels([r["rotulo"] for r in resumos])
    eixo.set_ylabel("Tempo médio da busca (ms)")
    eixo.set_title(
        "Tempo médio por configuração e carga — medição in-process do laço de busca"
    )
    eixo.set_ylim(0, max(
        r["cargas"][c]["tempo_medio_ms"] + r["cargas"][c]["desvio_padrao_ms"]
        for r in resumos
        for c in nomes_cargas
    ) * 1.2)
    eixo.legend(loc="upper right", fontsize=9, title="Carga")

    figura.savefig(destino)
    plt.close(figura)


# ==============================================================================
# 4. FIGURA 2 — BUSCA LINEAR vs. INDEXADA
# ==============================================================================


def figura_busca_comparativo(
    relatorio_linear: dict, relatorio_indexada: dict, destino: Path
) -> None:
    """Contrasta tempo de consulta e volume de trabalho entre as duas estratégias de busca.

    Ambas as execuções retornam exatamente os mesmos 75 candidatos, o que torna a
    comparação direta (mesmo resultado, custos diferentes).
    """
    tempo_linear_ms = relatorio_linear["tempo_busca_segundos"] * 1000
    tempo_indexada_ms = relatorio_indexada["tempo_busca_segundos"] * 1000
    trabalho_linear = relatorio_linear["total_tokens_examinados"]
    trabalho_indexada = relatorio_indexada["total_postings_consultadas"]

    figura, (eixo_tempo, eixo_trabalho) = plt.subplots(1, 2, figsize=(11.5, 5.2))

    paineis = (
        (
            eixo_tempo,
            [tempo_linear_ms, tempo_indexada_ms],
            ["Busca linear", "Busca indexada"],
            "Tempo de consulta (ms, escala log)",
            lambda v: f"{decimal(v, 4)} ms",
            "Tempo (ms)",
        ),
        (
            eixo_trabalho,
            [trabalho_linear, trabalho_indexada],
            ["Varredura completa", "Acesso via postings"],
            "Trabalho realizado (escala log)",
            milhar,
            "Itens examinados\n(tokens vs. postings)",
        ),
    )

    for eixo, valores, rotulos, titulo, formatador, rotulo_y in paineis:
        barras = eixo.bar(
            rotulos,
            valores,
            color=[CORES_CONFIG[0], CORES_CONFIG[1]],
            width=0.5,
            edgecolor="white",
            linewidth=0.8,
            zorder=3,
        )
        eixo.set_yscale("log")
        eixo.set_title(titulo, fontsize=10.5)
        eixo.set_ylabel(rotulo_y)
        eixo.set_ylim(min(valores) / 5, max(valores) * 4)
        for barra, valor in zip(barras, valores):
            eixo.text(
                barra.get_x() + barra.get_width() / 2,
                valor * 1.25,
                formatador(valor),
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
                color=COR_NEUTRA,
            )

    ganho_tempo = tempo_linear_ms / tempo_indexada_ms
    ganho_trabalho = trabalho_linear / trabalho_indexada
    candidatos = relatorio_indexada["total_candidatos"]

    figura.suptitle(
        f"Busca linear vs. indexada — mesmo resultado ({candidatos} candidatos), "
        f"{decimal(ganho_tempo, 1)}× mais rápida e {milhar(ganho_trabalho)}× menos trabalho",
        fontsize=12,
        fontweight="bold",
    )
    figura.text(
        0.5,
        0.005,
        "Índice invertido: apenas os termos da consulta são visitados, em vez dos 182 chunks completos.",
        ha="center",
        va="bottom",
        fontsize=8.5,
        color=COR_NEUTRA,
    )
    figura.tight_layout(rect=(0, 0.04, 1, 0.93))
    figura.savefig(destino)
    plt.close(figura)


# ==============================================================================
# 5. FIGURA 3 — ESCALABILIDADE DO MERGE SORT
# ==============================================================================


def medir_comparacoes_merge_sort(
    modulo_busca, tamanhos: list[int], repeticoes: int, semente: int = 20262
) -> dict[int, list[int]]:
    """Reexecuta o Merge Sort real da Etapa 4 e coleta as comparações por tamanho de entrada."""
    gerador = random.Random(semente)
    medicoes: dict[int, list[int]] = {}

    for tamanho in tamanhos:
        medicoes[tamanho] = []
        for _ in range(repeticoes):
            candidatos = [
                {"id_chunk": f"chunk_{i:05d}", "score": gerador.random() * 100}
                for i in range(tamanho)
            ]
            metricas = {
                "movimentacoes": 0,
                "chamadas_recursivas": 0,
                "profundidade_maxima": 0,
                "empates_score": 0,
                "comparacoes_score": 0,
                "comparacoes_id_chunk": 0,
                "comparacoes_totais": 0,
            }
            modulo_busca.merge_sort(candidatos, metricas)
            medicoes[tamanho].append(metricas["comparacoes_totais"])

    return medicoes


def ajuste_potencia(tamanhos: list[int], medias: list[float]) -> tuple[float, float, float]:
    """Ajusta comparacoes = a · n^b por mínimos quadrados em escala log-log.

    Retorna (a, b, R²). O expoente b é o expoente local observado; para uma função
    n log n medida na faixa n ∈ [8, 2048] espera-se b ≈ 1,27–1,35, pois o expoente
    local de n log n vale 1 + log(log n)/log(n), que decresce lentamente com n.
    Um b ≈ 1,0 indicaria linearidade e b ≈ 2, quadraticidade.
    """
    xs = [math.log(n) for n in tamanhos]
    ys = [math.log(valor) for valor in medias]
    media_x = statistics.fmean(xs)
    media_y = statistics.fmean(ys)
    covariancia = sum((x - media_x) * (y - media_y) for x, y in zip(xs, ys))
    variancia = sum((x - media_x) ** 2 for x in xs)
    expoente = covariancia / variancia
    intercepto = media_y - expoente * media_x
    previstos = [intercepto + expoente * x for x in xs]
    residuo = sum((y - p) ** 2 for y, p in zip(ys, previstos))
    total = sum((y - media_y) ** 2 for y in ys)
    r2 = 1 - residuo / total if total else 1.0
    return math.exp(intercepto), expoente, r2


def figura_escalabilidade_merge_sort(
    medicoes: dict[int, list[int]], destino: Path
) -> dict:
    """Valida empiricamente a recorrência T(n) = 2T(n/2) + Θ(n) do Merge Sort da Etapa 4.

    O painel superior mostra as comparações medidas contra a referência n·log₂ n.
    O painel inferior aplica o teste do "achatamento": se o custo é Θ(n log n), então
    comparações / (n·log₂ n) deve permanecer aproximadamente constante quando n cresce.
    """
    tamanhos = sorted(medicoes)
    medias = [statistics.fmean(medicoes[n]) for n in tamanhos]
    minimos = [min(medicoes[n]) for n in tamanhos]
    maximos = [max(medicoes[n]) for n in tamanhos]

    base_n_log_n = [n * math.log2(n) for n in tamanhos]
    normalizadas = [media / base for media, base in zip(medias, base_n_log_n)]
    constante = statistics.fmean(normalizadas)
    curva_n_log_n = [constante * base for base in base_n_log_n]

    ajuste_a, expoente, r2 = ajuste_potencia(tamanhos, medias)
    variacao = statistics.pstdev(normalizadas) / constante

    figura, (eixo, eixo_razao) = plt.subplots(
        2,
        1,
        figsize=(9.8, 8.6),
        gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.34},
    )

    # --- Painel superior: comparações absolutas vs. referência Θ(n log n) ---
    eixo.fill_between(
        tamanhos,
        minimos,
        maximos,
        color=CORES_CONFIG[2],
        alpha=0.18,
        zorder=2,
        label="Faixa mín–máx. observada",
    )
    eixo.plot(
        tamanhos,
        medias,
        marker="o",
        markersize=6,
        color=CORES_CONFIG[2],
        linewidth=2,
        label="Merge Sort medido (média)",
        zorder=4,
    )
    eixo.plot(
        tamanhos,
        curva_n_log_n,
        linestyle="--",
        linewidth=1.8,
        color=COR_REFERENCIA,
        label=f"Referência Θ(n log₂ n) · c, com c = {decimal(constante, 2)}",
        zorder=3,
    )
    eixo.set_xscale("log", base=2)
    eixo.set_xticks(tamanhos)
    eixo.set_xticklabels([str(n) for n in tamanhos], fontsize=8.5)
    eixo.set_xlabel("n — número de candidatos a ordenar")
    eixo.set_ylabel("Comparações de score")
    eixo.set_title("Escalabilidade do Merge Sort: comparações empíricas vs. Θ(n log n)")
    eixo.legend(loc="upper left", fontsize=9)
    eixo.annotate(
        f"ajuste de potência em log-log:\n"
        f"comparações ≈ {decimal(ajuste_a, 2)} · n^{decimal(expoente, 3)}   (R² = {decimal(r2, 4)})\n"
        f"expoente local esperado para n log n nesta faixa: ≈ 1,27–1,35",
        xy=(0.98, 0.06),
        xycoords="axes fraction",
        ha="right",
        va="bottom",
        fontsize=9,
        color=COR_NEUTRA,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": COR_REFERENCIA},
    )

    # --- Painel inferior: teste do achatamento da razão normalizada ---
    eixo_razao.axhspan(
        constante * (1 - variacao),
        constante * (1 + variacao),
        color=COR_REFERENCIA,
        alpha=0.18,
        zorder=2,
        label=f"±1 desvio-padrão ({decimal(100 * variacao, 1)}%)",
    )
    eixo_razao.axhline(constante, color=COR_NEUTRA, linewidth=1.2, zorder=3)
    eixo_razao.plot(
        tamanhos,
        normalizadas,
        marker="s",
        markersize=5,
        color=CORES_CONFIG[1],
        linewidth=1.8,
        zorder=4,
        label="comparações / (n · log₂ n)",
    )
    eixo_razao.set_xscale("log", base=2)
    eixo_razao.set_xticks(tamanhos)
    eixo_razao.set_xticklabels([str(n) for n in tamanhos], fontsize=8.5)
    eixo_razao.set_xlabel("n — número de candidatos a ordenar")
    eixo_razao.set_ylabel("Razão\nnormalizada", fontsize=9)
    eixo_razao.set_title(
        "Teste do achatamento: se o custo é Θ(n log n), a razão normalizada permanece constante",
        fontsize=10,
    )
    eixo_razao.legend(loc="upper right", fontsize=8.5, ncols=2)
    eixo_razao.set_ylim(0, constante * (1 + 6 * variacao))

    figura.savefig(destino)
    plt.close(figura)

    return {
        "expoente_ajustado": expoente,
        "r2_ajuste": r2,
        "constante_n_log_n": constante,
        "razao_minima": min(normalizadas),
        "razao_maxima": max(normalizadas),
        "variacao_relativa": variacao,
    }


# ==============================================================================
# 6. FIGURA 4 — DISTRIBUIÇÃO DE VOCABULÁRIO (ZIPF)
# ==============================================================================


def frequencias_vocabulario(indice_invertido: dict) -> list[int]:
    """Soma as frequências dos postings de cada termo do índice invertido."""
    frequencias = []
    for registro in indice_invertido.values():
        postings = registro.get("chunks") if isinstance(registro, dict) else registro
        if not postings:
            continue
        frequencias.append(sum(p.get("frequencia", 0) for p in postings))
    return sorted(frequencias, reverse=True)


def figura_zipf(frequencias: list[int], total_termos: int, destino: Path) -> None:
    """Verifica a Lei de Zipf na distribuição dos termos do corpus."""
    posicoes = list(range(1, len(frequencias) + 1))

    figura, eixo = plt.subplots(figsize=(9.8, 5.6))
    eixo.loglog(
        posicoes,
        frequencias,
        linewidth=1.8,
        color=CORES_CONFIG[1],
        label="Distribuição observada",
        zorder=4,
    )

    referencia = [frequencias[0] / posicao for posicao in posicoes]
    eixo.loglog(
        posicoes,
        referencia,
        linestyle="--",
        linewidth=1.5,
        color=COR_REFERENCIA,
        label="Referência de Zipf ideal (f ∝ 1/r)",
        zorder=3,
    )

    quantidade_unica = sum(1 for f in frequencias if f == 1)
    eixo.set_xlabel("Posição (rank) do termo, em ordem decrescente de frequência")
    eixo.set_ylabel("Ocorrências no corpus")
    eixo.set_title(f"Distribuição de vocabulário — {milhar(total_termos)} termos distintos")
    eixo.legend(loc="upper right", fontsize=9)

    eixo.annotate(
        f"termo mais frequente: {milhar(frequencias[0])} ocorrências\n"
        f"termos com ocorrência única: {milhar(quantidade_unica)} "
        f"({decimal(100 * quantidade_unica / len(frequencias), 1)}% do vocabulário)",
        xy=(0.04, 0.06),
        xycoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=9,
        color=COR_NEUTRA,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": COR_REFERENCIA},
    )
    figura.savefig(destino)
    plt.close(figura)


# ==============================================================================
# 7. FIGURA 5 — MEMÓRIA POR CONFIGURAÇÃO
# ==============================================================================


def figura_memoria_configuracoes(resumos: list[dict], destino: Path) -> None:
    """Compara o pico de memória residente (RSS) entre as configurações."""
    rotulos = [r["rotulo"] for r in resumos]
    medias = [r["memoria_media_mb"] for r in resumos]
    maximos = [r["memoria_max_mb"] for r in resumos]
    posicoes = list(range(len(rotulos)))

    figura, eixo = plt.subplots(figsize=(9.2, 5.3))
    barras = eixo.bar(
        posicoes,
        medias,
        color=CORES_CONFIG,
        width=0.5,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
        label="Pico médio",
    )
    eixo.scatter(
        posicoes,
        maximos,
        marker="D",
        s=45,
        color=COR_NEUTRA,
        zorder=4,
        label="Pico máximo observado",
    )

    for barra, media in zip(barras, medias):
        eixo.text(
            barra.get_x() + barra.get_width() / 2,
            media + max(maximos) * 0.02,
            f"{decimal(media)} MB",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COR_NEUTRA,
        )

    eixo.set_xticks(posicoes)
    eixo.set_xticklabels(rotulos)
    eixo.set_ylabel("Memória residente (MB)")
    eixo.set_title("Pico de memória residente por configuração")
    eixo.set_ylim(0, max(maximos) * 1.18)
    eixo.legend(loc="upper left", fontsize=9)

    figura.text(
        0.5,
        -0.02,
        "A memória é dominada pela inicialização do interpretador e pela carga do índice "
        "(≈ 2,2 MB de JSON),\nnão pela estrutura de dados de cada estratégia.",
        ha="center",
        va="top",
        fontsize=8.5,
        color=COR_NEUTRA,
    )
    figura.savefig(destino)
    plt.close(figura)


# ==============================================================================
# 8. FIGURA 6 — CUSTO DAS ETAPAS DO PIPELINE
# ==============================================================================


def figura_etapas_pipeline(
    processamento: dict,
    chunking: dict,
    indexacao: dict,
    busca_linear: dict,
    busca_indexada: dict,
    ordenacao: dict,
    destino: Path,
) -> None:
    """Evidencia onde o tempo é realmente gasto: a ingestão domina, a consulta é desprezível."""
    etapas = [
        ("1. Ingestão\nde PDFs", processamento["tempo_processamento_segundos"] * 1000),
        ("2. Chunking", chunking["tempo_execucao_segundos"] * 1000),
        ("3. Índice\ninvertido", indexacao["tempo_construcao_segundos"] * 1000),
        ("4a. Busca\nlinear", busca_linear["tempo_busca_segundos"] * 1000),
        ("4b. Busca\nindexada", busca_indexada["tempo_busca_segundos"] * 1000),
        ("4c. Merge Sort\n(Top-k)", ordenacao["tempo_ordenacao_segundos"] * 1000),
    ]

    rotulos = [nome for nome, _ in etapas]
    valores_ms = [valor for _, valor in etapas]

    figura, eixo = plt.subplots(figsize=(10.2, 5.4))
    barras = eixo.bar(
        rotulos,
        valores_ms,
        color=COR_INGESTAO,
        width=0.6,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    eixo.set_yscale("log")
    eixo.set_ylabel("Tempo (ms, escala logarítmica)")
    eixo.set_title("Custo temporal das etapas do pipeline — execução única")
    eixo.set_ylim(min(valores_ms) / 4, max(valores_ms) * 3.2)

    for barra, valor in zip(barras, valores_ms):
        eixo.text(
            barra.get_x() + barra.get_width() / 2,
            valor * 1.18,
            f"{decimal(valor, 3)} ms",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color=COR_NEUTRA,
        )

    custo_ingestao = sum(valores_ms[:3])
    razao = custo_ingestao / valores_ms[4]
    eixo.annotate(
        f"construção (etapas 1–3): {decimal(custo_ingestao, 1)} ms\n"
        f"consulta ao índice: {decimal(valores_ms[4], 3)} ms\n"
        f"razão ≈ {milhar(razao)}×",
        xy=(0.02, 0.96),
        xycoords="axes fraction",
        ha="left",
        va="top",
        fontsize=9,
        color=COR_NEUTRA,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "white", "edgecolor": COR_REFERENCIA},
    )
    figura.tight_layout()
    figura.savefig(destino)
    plt.close(figura)


# ==============================================================================
# 9. TABELA CONSOLIDADA (SEÇÃO 7.3 DO EDITAL)
# ==============================================================================


def gerar_tabela_csv(
    resumos: list[dict],
    relatorio_linear: dict,
    relatorio_indexada: dict,
    ordenacao: dict,
    indexacao: dict,
    experimentos: dict,
    destino: Path,
) -> None:
    """Consolida a tabela de resultados exigida pela Seção 7.3 do edital.

    Como as duas cargas passaram a ter tamanhos distintos (corpus integral e
    reduzido), o tempo é reportado por carga em colunas próprias; uma coluna
    única de "tempo médio" só faria sentido se ambas medissem o mesmo n.
    """
    nomes_cargas = list(resumos[0]["cargas"].keys()) if resumos else []
    colunas = [
        "configuracao",
        "modo_busca",
        "metrica_score",
        "execucoes",
        "tempo_total_medio_ms",
        "tempo_total_desvio_ms",
        "tempo_busca_em_memoria_ms",
        "unidade_de_trabalho_medida",
        "pico_memoria_media_mb",
        "chunks_no_corpus",
        "k",
    ]
    for nome_carga in nomes_cargas:
        sufixo = _sufixo_carga(nome_carga)
        colunas.append(f"tempo_medio_{sufixo}_ms")
        colunas.append(f"tempo_desvio_{sufixo}_ms")
        colunas.append(f"amostras_{sufixo}")

    comparacoes_por_configuracao = {
        resumos[0]["configuracao"]: f"{relatorio_linear['total_comparacoes_termos']} comparações termo-a-termo",
        resumos[1]["configuracao"]: f"{relatorio_indexada['total_postings_consultadas']} postings consultadas",
        resumos[2]["configuracao"]: (
            f"{ordenacao['num_comparacoes_score']} comparações de score + "
            f"{ordenacao['num_comparacoes_id_chunk']} desempates por id_chunk"
        ),
    }
    tempo_busca_por_configuracao = {
        resumos[0]["configuracao"]: relatorio_linear["tempo_busca_segundos"] * 1000,
        resumos[1]["configuracao"]: relatorio_indexada["tempo_busca_segundos"] * 1000,
        resumos[2]["configuracao"]: relatorio_indexada["tempo_busca_segundos"] * 1000,
    }

    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(colunas)
        for resumo in resumos:
            configuracao = resumo["configuracao"]
            linha = [
                configuracao,
                resumo["modo_busca"],
                resumo["metrica_score"],
                resumo["amostras"],
                decimal(resumo["tempo_global_ms"], 4),
                decimal(resumo["tempo_desvio_ms"], 4),
                decimal(tempo_busca_por_configuracao[configuracao], 4),
                comparacoes_por_configuracao[configuracao],
                decimal(resumo["memoria_media_mb"], 2),
                indexacao["total_chunks_entrada"],
                experimentos["metadados"]["k_definido"],
            ]
            for nome_carga in nomes_cargas:
                dados = resumo["cargas"][nome_carga]
                linha.extend(
                    [
                        decimal(dados["tempo_medio_ms"], 4),
                        decimal(dados["desvio_padrao_ms"], 4),
                        dados["amostras"],
                    ]
                )
            escritor.writerow(linha)


def figura_analise_assintotica(analise: dict, destino: Path) -> None:
    """Desenha uma grade de curvas tempo × n por etapa, em escala log-log.

    A faixa de n cobre cerca de uma década em cada etapa, o que basta para o
    ajuste de expoente usado na classificação, mas é estreita demais para que o
    R² separe O(n) de O(n log n) — por isso cada painel mostrará as curvas
    teóricas de referência e o expoente medido, deixando a decisão auditável.
    """
    estagios = list(analise["estagios"].values())
    colunas = 4
    linhas = math.ceil(len(estagios) / colunas)
    figura, eixos = plt.subplots(
        linhas, colunas, figsize=(4.1 * colunas, 3.3 * linhas), squeeze=False
    )

    for eixo, estagio in zip(eixos.ravel(), estagios):
        medicoes = sorted(estagio["medicoes"], key=lambda m: m["n"])
        xs = [float(m["n"]) for m in medicoes]
        ys = [m["tempo_ms"] for m in medicoes]

        eixo.plot(xs, ys, marker="o", markersize=4.5, color=COR_DESTAQUE, zorder=4,
                  label="medido")

        # As curvas teóricas são ancoradas no primeiro ponto medido, de modo que
        # o que se compara visualmente é a inclinação, não a constante.
        x_ref = [xs[0] * (xs[-1] / xs[0]) ** (i / 80) for i in range(81)]
        for rotulo, funcao in (
            ("O(n)", lambda n: n),
            ("O(n log n)", lambda n: n * math.log2(max(n, 2.0))),
        ):
            base = funcao(xs[0])
            if base <= 0:
                continue
            eixo.plot(
                x_ref,
                [ys[0] * funcao(n) / base for n in x_ref],
                linestyle="--",
                linewidth=1.1,
                alpha=0.7,
                zorder=2,
                label=rotulo,
            )


        eixo.set_xscale("log")
        eixo.set_yscale("log")
        eixo.set_title(
            f"{estagio['estagio']}\n"
            f"eleito: {estagio['modelo_eleito']} (p={decimal(estagio['expoente_empirico'], 2)})",
            fontsize=9.5,
        )
        eixo.set_xlabel(estagio["unidade_entrada"], fontsize=8)
        eixo.set_ylabel("tempo (ms)", fontsize=8)
        eixo.tick_params(labelsize=7.5)
        eixo.grid(True, which="both", linestyle=":", alpha=0.35, zorder=0)
        eixo.legend(fontsize=7, loc="upper left")

    for eixo in eixos.ravel()[len(estagios):]:
        eixo.axis("off")

    figura.suptitle(
        "Análise assintótica do pipeline — tempo por tamanho de entrada (escala log-log)",
        fontsize=12,
    )
    figura.tight_layout(rect=(0, 0, 1, 0.965))
    figura.savefig(destino)
    plt.close(figura)


def gerar_tabela_analise_assintotica(analise: dict, destino: Path) -> None:
    """Consolida a análise assintótica do pipeline (item 7.1 do edital) em CSV.

    O item 7.1 pede a complexidade de cada etapa do pipeline, não só a dos
    algoritmos centrais; a tabela reúne, por etapa, o que foi observado e o
    modelo eleito, para que a defesa contra a teoria fique auditável.
    """
    colunas = [
        "estagio",
        "unidade_entrada",
        "n_minimo",
        "n_maximo",
        "pontos_medidos",
        "complexidade_teorica",
        "complexidade_observada",
        "expoente_empirico",
        "r2_melhor_ajuste",
        "modelo_eleito",
        "tempo_min_ms",
        "tempo_max_ms",
    ]
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(colunas)
        for chave, estagio in analise["estagios"].items():
            medicoes = estagio["medicoes"]
            escritor.writerow(
                [
                    estagio["estagio"],
                    estagio["unidade_entrada"],
                    min(m["n"] for m in medicoes),
                    max(m["n"] for m in medicoes),
                    len(medicoes),
                    estagio["complexidade_teorica"],
                    estagio["modelo_eleito"],
                    decimal(estagio["expoente_empirico"], 3),
                    decimal(
                        estagio["ajustes"].get(estagio["modelo_eleito"], {}).get("r2", 0.0), 5
                    ),
                    estagio["comparacao_modelos"]["modelo_preferido_por_r2"],
                    decimal(estagio["tempo_min_ms"], 4),
                    decimal(estagio["tempo_max_ms"], 4),
                ]
            )


# ==============================================================================
# 10. EXECUÇÃO PRINCIPAL (CLI)
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Etapa 6 — Geração dos gráficos e da tabela consolidada de resultados (PAA/UFS)."
    )
    parser.add_argument("--resultados", type=Path, default=Path("7_resultados"))
    parser.add_argument(
        "--experimentos", type=Path, default=Path("7_resultados/relatorio_experimentos.json")
    )
    parser.add_argument(
        "--busca-linear", type=Path, default=Path("6_busca_lexical/relatorio_busca_linear.json")
    )
    parser.add_argument(
        "--busca-indexada", type=Path, default=Path("6_busca_lexical/relatorio_busca.json")
    )
    parser.add_argument(
        "--ordenacao", type=Path, default=Path("6_busca_lexical/relatorio_ordenacao.json")
    )
    parser.add_argument(
        "--indexacao", type=Path, default=Path("5_indexacao/relatorio_indexacao.json")
    )
    parser.add_argument("--indice", type=Path, default=Path("5_indexacao/indice_invertido.json"))
    parser.add_argument("--chunking", type=Path, default=Path("4_chunks/relatorio_chunking.json"))
    parser.add_argument(
        "--processamento", type=Path, default=Path("3_dados/relatorio_processamento.json")
    )
    parser.add_argument(
        "--analise-assintotica",
        type=Path,
        default=Path("7_resultados/analise_assintotica.json"),
        help="Saída da Etapa 7, consolidada na tabela do item 7.1 do edital.",
    )
    parser.add_argument(
        "--script-busca",
        type=Path,
        default=Path("1_scripts/4_buscar_e_ordenar.py"),
        help="Script cujo Merge Sort é reexecutado para medir a curva de escalabilidade.",
    )
    parser.add_argument(
        "--tamanhos-escala",
        type=int,
        nargs="+",
        default=[8, 16, 32, 64, 128, 256, 512, 1024, 2048],
        help="Tamanhos de entrada usados na curva experimental do Merge Sort.",
    )
    parser.add_argument(
        "--repeticoes-escala",
        type=int,
        default=30,
        help="Repetições por tamanho na curva experimental do Merge Sort.",
    )
    args = parser.parse_args()

    configurar_saida_padrao()
    configurar_estilo()
    args.resultados.mkdir(parents=True, exist_ok=True)

    experimentos = carregar_json(args.experimentos)
    relatorio_linear = carregar_json(args.busca_linear)
    relatorio_indexada = carregar_json(args.busca_indexada)
    ordenacao = carregar_json(args.ordenacao)
    indexacao = carregar_json(args.indexacao)
    chunking = carregar_json(args.chunking)
    processamento = carregar_json(args.processamento)

    resumos = resumir_por_configuracao(experimentos)

    print("=" * 74)
    print("ETAPA 6 — GERAÇÃO DE GRÁFICOS E CONSOLIDAÇÃO DOS RESULTADOS (PAA / UFS)")
    print("=" * 74)

    figura_tempo_execucao(resumos, args.resultados / "grafico_tempo_execucao.png")
    print("[1/7] grafico_tempo_execucao.png")

    figura_busca_comparativo(
        relatorio_linear, relatorio_indexada, args.resultados / "grafico_busca_comparativo.png"
    )
    print("[2/7] grafico_busca_comparativo.png")

    modulo_busca = carregar_modulo_busca(args.script_busca)
    medicoes = medir_comparacoes_merge_sort(
        modulo_busca, sorted(args.tamanhos_escala), args.repeticoes_escala
    )
    estatisticas_escala = figura_escalabilidade_merge_sort(
        medicoes, args.resultados / "grafico_escalabilidade_merge_sort.png"
    )
    print(
        "[3/7] grafico_escalabilidade_merge_sort.png "
        f"(b={decimal(estatisticas_escala['expoente_ajustado'], 3)}, "
        f"R²={decimal(estatisticas_escala['r2_ajuste'], 4)}, "
        f"razão n·log₂n = {decimal(estatisticas_escala['constante_n_log_n'], 3)} "
        f"± {decimal(100 * estatisticas_escala['variacao_relativa'], 2)}%)"
    )

    frequencias = frequencias_vocabulario(carregar_json(args.indice)["indice_invertido"])
    figura_zipf(frequencias, indexacao["total_termos"], args.resultados / "grafico_zipf.png")
    print(f"[4/7] grafico_zipf.png ({milhar(len(frequencias))} termos)")

    figura_memoria_configuracoes(resumos, args.resultados / "grafico_memoria_configuracoes.png")
    print("[5/7] grafico_memoria_configuracoes.png")

    figura_etapas_pipeline(
        processamento,
        chunking,
        indexacao,
        relatorio_linear,
        relatorio_indexada,
        ordenacao,
        args.resultados / "grafico_etapas_pipeline.png",
    )
    print("[6/7] grafico_etapas_pipeline.png")

    tabela = args.resultados / "tabela_resultados.csv"
    gerar_tabela_csv(
        resumos, relatorio_linear, relatorio_indexada, ordenacao, indexacao, experimentos, tabela
    )
    print(f"[tabela] {tabela}")

    if args.analise_assintotica.exists():
        analise = carregar_json(args.analise_assintotica)
        figura_analise_assintotica(analise, args.resultados / "grafico_analise_assintotica.png")
        print("[7/7] grafico_analise_assintotica.png")
        destino_asintotica = args.resultados / "tabela_analise_assintotica.csv"
        gerar_tabela_analise_assintotica(analise, destino_asintotica)
        print(f"[tabela] {destino_asintotica}")
    else:
        print(
            f"[aviso] {args.analise_assintotica} não encontrado; "
            "execute 1_scripts/7_analise_assintotica.py para gerar os artefatos do item 7.1."
        )

    print("-" * 74)
    print(f"Todas as figuras foram gravadas em: {args.resultados}")
    print("=" * 74)


if __name__ == "__main__":
    main()
