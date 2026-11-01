from __future__ import annotations

"""Etapa 6 — Métricas, Benchmark Experimental e Avaliação Empírica (AV2 - Trilha A).

Responsável: Laryssa Barbosa de Andrade

Atende integralmente às Seções 5 (Trilha A), 9, 9.1 e 11 do Edital da AV2:
- Compara Baseline Guloso (v_i / w_i) vs. Programação Dinâmica Bottom-Up (Mochila 0/1);
- Executa 48 medições (2 abordagens x 2 escalas x 4 orçamentos W x 3 repetições >= 12);
- Registra tempo de pré-processamento, tempo de seleção, tempo total, memória (tracemalloc),
  tokens usados, relevância/cobertura (BM25), redundância e respeito ao orçamento W;
- Registra SO, linguagem, bibliotecas, hardware, corpus, commit Git, comando e data;
- Valida 8 casos de teste formais (incluindo dado duplicado e caso adversarial) com
  resultado esperado, observado, evidência, status e requisito avaliado.
"""

import json
import csv
import platform
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path


# ==============================================================================
# 1. ALGORITMOS SOB AVALIAÇÃO (BASELINE GULOSO vs. PROGRAMAÇÃO DINÂMICA)
# ==============================================================================

def executar_guloso(itens: list[dict], capacidade: int) -> tuple[list[str], float, int]:
    """Linha de Base Gulosa: seleciona chunks por densidade (v_i / w_i)."""
    if capacidade <= 0 or not itens:
        return [], 0.0, 0

    itens_ordenados = sorted(
        itens,
        key=lambda x: (
            (x["v"] / x["w"]) if x["w"] > 0 else 0.0,
            x["v"],
            -x["w"],
            -x["id_num"],
        ),
        reverse=True,
    )

    selecionados = []
    beneficio_total = 0.0
    custo_total = 0
    vistos = set()

    for item in itens_ordenados:
        # Evita selecionar chunks duplicados pelo mesmo ID
        if item["id"] in vistos:
            continue
        if item["w"] > 0 and custo_total + item["w"] <= capacidade:
            selecionados.append(item["id"])
            vistos.add(item["id"])
            beneficio_total += item["v"]
            custo_total += item["w"]

    return selecionados, round(beneficio_total, 6), custo_total


def executar_programacao_dinamica(itens: list[dict], capacidade: int) -> tuple[list[str], float, int]:
    """Programação Dinâmica (Mochila 0/1 Bottom-Up) com reconstrução por backtracking."""
    if capacidade <= 0 or not itens:
        return [], 0.0, 0

    # Deduplicação preventiva mantendo a primeira ocorrência válida de cada id_chunk
    itens_validos = []
    vistos = set()
    for it in itens:
        if it["w"] > 0 and it["id"] not in vistos:
            itens_validos.append(it)
            vistos.add(it["id"])

    n = len(itens_validos)
    if n == 0:
        return [], 0.0, 0

    dp = [[0.0] * (capacidade + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w_i = itens_validos[i - 1]["w"]
        v_i = itens_validos[i - 1]["v"]
        linha_ant = dp[i - 1]
        linha_atual = dp[i]

        for c in range(capacidade + 1):
            if w_i > c:
                linha_atual[c] = linha_ant[c]
            else:
                sem_item = linha_ant[c]
                com_item = linha_ant[c - w_i] + v_i
                linha_atual[c] = com_item if com_item > sem_item else sem_item

    selecionados = []
    c_restante = capacidade
    for i in range(n, 0, -1):
        if abs(dp[i][c_restante] - dp[i - 1][c_restante]) > 1e-9:
            item = itens_validos[i - 1]
            selecionados.append(item["id"])
            c_restante -= item["w"]

    selecionados.reverse()
    beneficio_otimo = round(dp[n][capacidade], 6)
    custo_total = capacidade - c_restante

    return selecionados, beneficio_otimo, custo_total


# ==============================================================================
# 2. METADADOS DE REPRODUTIBILIDADE E CARREGAMENTO DO CORPUS (§9)
# ==============================================================================

def obter_commit_git() -> str:
    """Obtém o hash curto do commit atual do repositório Git (§9 do Edital)."""
    try:
        repositorio = Path(__file__).resolve().parents[1]
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repositorio,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.stdout.strip() or "commit-local-av2"
    except Exception:
        return "commit-local-av2"


def carregar_itens_instancia(pasta_base: Path) -> tuple[list[dict], float, str]:
    """Carrega os candidatos da AV2 e cronometra o tempo de pré-processamento (§9.1)."""
    t0 = time.perf_counter()
    caminhos_possiveis = [
        pasta_base / "3_instancias" / "instancias.json",
        pasta_base / "2_dados_tokenizados" / "chunks_tokenizados.json",
    ]

    for subpasta in ["3_instancias", "2_dados_tokenizados"]:
        dir_busca = pasta_base / subpasta
        if dir_busca.exists():
            for arq in sorted(dir_busca.glob("*.json")):
                if arq not in caminhos_possiveis:
                    caminhos_possiveis.append(arq)

    dados_brutos = None
    caminho_lido = "Carga sintética de fallback (PROCC/UFS)"
    for cam in caminhos_possiveis:
        if cam.exists():
            try:
                with open(cam, "r", encoding="utf-8") as f:
                    dados_brutos = json.load(f)
                caminho_lido = str(cam.relative_to(pasta_base.parent))
                break
            except Exception:
                continue

    itens_normalizados = []
    if dados_brutos is not None:
        lista_candidatos = []
        if isinstance(dados_brutos, list):
            lista_candidatos = dados_brutos
        elif isinstance(dados_brutos, dict):
            for chave in ["itens", "candidatos", "chunks", "instancias", "dados"]:
                if chave in dados_brutos and isinstance(dados_brutos[chave], list):
                    lista_candidatos = dados_brutos[chave]
                    break
            if not lista_candidatos:
                for val in dados_brutos.values():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        lista_candidatos = val
                        break
                    elif isinstance(val, dict) and "itens" in val:
                        lista_candidatos = val["itens"]
                        break

        for idx, item in enumerate(lista_candidatos):
            if not isinstance(item, dict):
                continue
            id_str = str(item.get("id_chunk") or item.get("id") or f"chunk_{idx:03d}")
            digitos = "".join(ch for ch in id_str if ch.isdigit())
            id_num = int(digitos) if digitos else idx

            w = item.get("w_i") or item.get("w_tokens") or item.get("custo_tokens") or item.get("tokens") or item.get("w") or item.get("peso") or 0
            v = item.get("v_i") or item.get("score_bm25") or item.get("relevancia") or item.get("valor") or item.get("score") or item.get("v") or 0.0

            if int(w) > 0 and float(v) > 0:
                itens_normalizados.append({
                    "id": id_str,
                    "id_num": id_num,
                    "w": int(w),
                    "v": float(v),
                })

    if not itens_normalizados:
        raise RuntimeError(
            "Nenhum item positivo foi carregado dos artefatos da AV2; "
            "a execução foi interrompida para evitar benchmark em dados sintéticos."
        )

    t1 = time.perf_counter()
    tempo_pre_ms = round((t1 - t0) * 1000.0, 4)
    return itens_normalizados, tempo_pre_ms, caminho_lido


# ==============================================================================
# 3. INSTRUMENTAÇÃO DE MÉTRICAS (§9.1) E CASOS DE TESTE (§11)
# ==============================================================================

def medir_execucao(funcao, itens: list[dict], capacidade: int, tempo_pre_ms: float) -> dict:
    """Mede seleção, tempo total, memória RAM, cobertura, redundância e orçamento (§9.1)."""
    copia_itens = [dict(it) for it in itens]

    tracemalloc.start()
    t0 = time.perf_counter()

    selecionados, beneficio, custo = funcao(copia_itens, capacidade)

    t1 = time.perf_counter()
    _, pico_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tempo_selecao_ms = round((t1 - t0) * 1000.0, 4)
    tempo_total_ms = round(tempo_pre_ms + tempo_selecao_ms, 4)

    # Taxa de redundância de IDs selecionados (0.0 indica ausência de duplicatas)
    qtd_total = len(selecionados)
    qtd_unicos = len(set(selecionados))
    taxa_redundancia = round(1.0 - (qtd_unicos / qtd_total), 4) if qtd_total > 0 else 0.0

    return {
        "qtd_selecionados": qtd_total,
        "ids_selecionados": selecionados,
        "beneficio_relevancia_bm25": round(beneficio, 4),
        "tokens_usados": custo,
        "orcamento_W": capacidade,
        "taxa_ocupacao_janela_pct": round((custo / capacidade) * 100.0, 2) if capacidade > 0 else 0.0,
        "redundancia_ids": taxa_redundancia,
        "respeitou_orcamento": custo <= capacidade,
        "tempo_preprocessamento_ms": tempo_pre_ms,
        "tempo_selecao_ms": tempo_selecao_ms,
        "tempo_total_fluxo_ms": tempo_total_ms,
        "pico_memoria_kb": round(pico_bytes / 1024.0, 3),
    }


def executar_casos_de_teste(itens_reais: list[dict]) -> list[dict]:
    """Executa os 8 casos de teste exigidos na Seção 11 com todos os campos obrigatórios."""
    casos = []

    # TC-01: Caso Normal
    sel_pd, ben_pd, cus_pd = executar_programacao_dinamica(itens_reais, 1024)
    casos.append({
        "id": "TC-01",
        "cenario": "Caso Normal (Seleção em W=1024)",
        "requisito_avaliado": "Maximização de relevância respeitando capacidade W (§5 Trilha A)",
        "esperado": "0 < Custo <= 1024 e Benefício ótimo > 0",
        "observado": f"Custo={cus_pd} tokens, Benefício={ben_pd:.4f}, Chunks={len(sel_pd)}",
        "evidencia": f"IDs selecionados: {sel_pd[:4]}...",
        "status": "APROVADO" if (0 < cus_pd <= 1024 and ben_pd > 0) else "FALHOU",
    })

    # TC-02: Fronteira Capacidade Zero
    sel_z, ben_z, cus_z = executar_programacao_dinamica(itens_reais, 0)
    casos.append({
        "id": "TC-02",
        "cenario": "Fronteira: Capacidade Zero (W=0)",
        "requisito_avaliado": "Tratamento de fronteira inferior de orçamento (§6 Parte A)",
        "esperado": "Seleção vazia ([]), custo=0, benefício=0.0",
        "observado": f"Selecionados={sel_z}, Custo={cus_z}, Benefício={ben_z}",
        "evidencia": "Caso base DP[i][0] = 0 verificado sem exceção",
        "status": "APROVADO" if (len(sel_z) == 0 and cus_z == 0 and ben_z == 0.0) else "FALHOU",
    })

    # TC-03: Limite de Tokens Excedido
    item_gigante = [{"id": "chunk_gigante", "id_num": 999, "w": 1721, "v": 50.0}]
    sel_g, ben_g, cus_g = executar_programacao_dinamica(item_gigante, 512)
    casos.append({
        "id": "TC-03",
        "cenario": "Limite de Tokens Excedido (w_i = 1721 > W = 512)",
        "requisito_avaliado": "Poda de chunk individual que excede a janela (§6 Parte A)",
        "esperado": "Item descartado ([]), custo=0, benefício=0.0",
        "observado": f"Selecionados={sel_g}, Custo={cus_g}, Benefício={ben_g}",
        "evidencia": "Condição w_i > c preserva linha_ant[c] = 0",
        "status": "APROVADO" if (len(sel_g) == 0 and cus_g == 0) else "FALHOU",
    })

    # TC-04: Entrada Grande / Capacidade Ampla
    soma_w = sum(it["w"] for it in itens_reais[:15])
    sel_all, ben_all, cus_all = executar_programacao_dinamica(itens_reais[:15], soma_w)
    casos.append({
        "id": "TC-04",
        "cenario": "Entrada Ampla com Capacidade Suficiente (W = soma total)",
        "requisito_avaliado": "Cobertura integral quando orçamento comporta todos os itens (§11)",
        "esperado": "Todos os 15 chunks selecionados sem perda",
        "observado": f"Selecionados={len(sel_all)}/15, Custo={cus_all}/{soma_w}",
        "evidencia": f"Benefício acumulado integral = {ben_all:.4f}",
        "status": "APROVADO" if len(sel_all) == 15 and cus_all == soma_w else "FALHOU",
    })

    # TC-05: Empate de Relevância e Custo
    itens_empate = [
        {"id": "chunk_002", "id_num": 2, "w": 100, "v": 10.0},
        {"id": "chunk_001", "id_num": 1, "w": 100, "v": 10.0},
    ]
    sel_emp, _, _ = executar_guloso(itens_empate, 100)
    casos.append({
        "id": "TC-05",
        "cenario": "Caso de Empate (Mesma densidade, valor e peso)",
        "requisito_avaliado": "Critério de desempate determinístico por menor ID (§6 e §11)",
        "esperado": "Priorizar menor identificador ['chunk_001']",
        "observado": f"Selecionado={sel_emp}",
        "evidencia": "Chave de ordenação (-id_num) garantiu determinismo",
        "status": "APROVADO" if sel_emp == ["chunk_001"] else "FALHOU",
    })

    # TC-06: Corpus Vazio
    sel_vazio, ben_vazio, cus_vazio = executar_programacao_dinamica([], 1024)
    casos.append({
        "id": "TC-06",
        "cenario": "Caso Vazio (Corpus/Lista de candidatos vazia N=0)",
        "requisito_avaliado": "Robustez contra entrada vazia ou consulta sem match (§6 e §11)",
        "esperado": "Retorno imediato ([], 0.0, 0) sem falha",
        "observado": f"Selecionados={sel_vazio}, Benefício={ben_vazio}, Custo={cus_vazio}",
        "evidencia": "Guarda inicial if not itens retornou estado nulo seguro",
        "status": "APROVADO" if (len(sel_vazio) == 0 and cus_vazio == 0) else "FALHOU",
    })

    # TC-07: Dado Duplicado e Não Mutação
    itens_duplicados = [
        {"id": "chunk_dup", "id_num": 1, "w": 200, "v": 15.0},
        {"id": "chunk_dup", "id_num": 1, "w": 200, "v": 15.0},
    ]
    snapshot = json.dumps(itens_duplicados)
    sel_dup_pd, ben_dup_pd, cus_dup_pd = executar_programacao_dinamica(itens_duplicados, 500)
    sel_dup_gul, _, _ = executar_guloso(itens_duplicados, 500)
    intacto = json.dumps(itens_duplicados) == snapshot
    casos.append({
        "id": "TC-07",
        "cenario": "Dado Duplicado e Imutabilidade da Entrada",
        "requisito_avaliado": "Prevenção de redundância por documento duplicado (§6 e §11)",
        "esperado": "Selecionar 'chunk_dup' apenas 1 vez (custo=200) e preservar lista original",
        "observado": f"PD={sel_dup_pd} (custo={cus_dup_pd}), Guloso={sel_dup_gul}, Original intacta={intacto}",
        "evidencia": "Filtro de conjunto 'vistos' bloqueou inserção duplicada na mochila",
        "status": "APROVADO" if (sel_dup_pd == ["chunk_dup"] and sel_dup_gul == ["chunk_dup"] and intacto) else "FALHOU",
    })

    # TC-08: Caso Adversarial (Refutação da Estratégia Gulosa)
    contraexemplo = [
        {"id": "A_denso", "id_num": 1, "w": 6, "v": 30.0},  # densidade 5.0
        {"id": "B_medio", "id_num": 2, "w": 5, "v": 22.0},  # densidade 4.4
        {"id": "C_medio", "id_num": 3, "w": 5, "v": 22.0},  # densidade 4.4
    ]
    sel_gul_adv, ben_gul_adv, cus_gul_adv = executar_guloso(contraexemplo, 10)
    sel_pd_adv, ben_pd_adv, cus_pd_adv = executar_programacao_dinamica(contraexemplo, 10)
    casos.append({
        "id": "TC-08",
        "cenario": "Caso Adversarial (Refutação da Heurística Gulosa em W=10)",
        "requisito_avaliado": "Provar subotimalidade gulosa na Mochila 0/1 e otimalidade da PD (§7 e §11)",
        "esperado": "PD seleciona B+C (v=44.0, w=10) > Guloso seleciona A (v=30.0, w=6)",
        "observado": f"PD={sel_pd_adv} (v={ben_pd_adv:.1f}, w={cus_pd_adv}) vs Guloso={sel_gul_adv} (v={ben_gul_adv:.1f}, w={cus_gul_adv})",
        "evidencia": "Ganho de +46,67% de relevância da PD sobre a escolha gulosa míope",
        "status": "APROVADO" if (ben_pd_adv == 44.0 and ben_gul_adv == 30.0) else "FALHOU",
    })

    return casos


# ==============================================================================
# 4. GERAÇÃO DE GRÁFICOS COMPARATIVOS (§9 e §13)
# ==============================================================================

def gerar_graficos(sintese: list[dict], pasta_saida: Path) -> None:
    """Gera gráficos de Tempo, Memória e Relevância vs. Orçamento W."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[AVISO] matplotlib não encontrado. Gráficos PNG não foram gerados.")
        return

    dados_completos = [d for d in sintese if "Completa" in d["escala"]]
    orcamentos = sorted(list({d["W"] for d in dados_completos}))

    tempos_pd = [next(d["tempo_selecao_medio_ms"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Programacao_Dinamica") for w in orcamentos]
    tempos_gul = [next(d["tempo_selecao_medio_ms"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Baseline_Guloso") for w in orcamentos]

    mem_pd = [next(d["memoria_media_kb"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Programacao_Dinamica") for w in orcamentos]
    mem_gul = [next(d["memoria_media_kb"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Baseline_Guloso") for w in orcamentos]

    score_pd = [next(d["beneficio_relevancia_bm25"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Programacao_Dinamica") for w in orcamentos]
    score_gul = [next(d["beneficio_relevancia_bm25"] for d in dados_completos if d["W"] == w and d["algoritmo"] == "Baseline_Guloso") for w in orcamentos]

    # Gráfico 1: Tempo de Seleção vs. W
    plt.figure(figsize=(8.5, 4.8))
    plt.plot(orcamentos, tempos_pd, marker="o", linewidth=2.2, color="#2563eb", label="Programação Dinâmica O(N·W)")
    plt.plot(orcamentos, tempos_gul, marker="s", linewidth=2.2, color="#10b981", label="Baseline Guloso O(N log N)")
    plt.title("Escalabilidade Temporal: Programação Dinâmica vs. Guloso (AV2)", fontweight="bold")
    plt.xlabel("Orçamento da Janela de Contexto — W (tokens)")
    plt.ylabel("Tempo Médio de Seleção (ms)")
    plt.xticks(orcamentos)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_saida / "grafico_tempo_vs_w.png", dpi=300)
    plt.close()

    # Gráfico 2: Pico de Memória RAM vs. W
    plt.figure(figsize=(8.5, 4.8))
    plt.plot(orcamentos, mem_pd, marker="^", linewidth=2.2, color="#7c3aed", label="Programação Dinâmica (Tabela DP)")
    plt.plot(orcamentos, mem_gul, marker="d", linewidth=2.2, color="#f59e0b", label="Baseline Guloso")
    plt.title("Consumo de Memória RAM (Pico) vs. Orçamento de Tokens (W)", fontweight="bold")
    plt.xlabel("Orçamento da Janela de Contexto — W (tokens)")
    plt.ylabel("Pico de Memória Alocada (KB)")
    plt.xticks(orcamentos)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_saida / "grafico_memoria_vs_w.png", dpi=300)
    plt.close()

    # Gráfico 3: Relevância Acumulada (BM25) vs. W
    plt.figure(figsize=(8.5, 4.8))
    plt.plot(orcamentos, score_pd, marker="o", linewidth=2.2, color="#1d4ed8", label="Programação Dinâmica (Ótimo Exato)")
    plt.plot(orcamentos, score_gul, marker="s", linestyle="--", linewidth=2.0, color="#059669", label="Baseline Guloso (Heurística)")
    plt.title("Qualidade de Seleção: Relevância Acumulada (BM25) vs. Orçamento W", fontweight="bold")
    plt.xlabel("Orçamento da Janela de Contexto — W (tokens)")
    plt.ylabel("Score BM25 Total Acumulado")
    plt.xticks(orcamentos)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(pasta_saida / "grafico_relevancia_vs_w.png", dpi=300)
    plt.close()

    print(f"[OK] 3 gráficos exportados em: {pasta_saida}")


def gravar_tabelas_csv(
    sintese: list[dict], medicoes_brutas: list[dict], pasta_saida: Path
) -> None:
    """Exporta as medições em formato tabular para análise e auditoria."""
    if sintese:
        caminho_sintese = pasta_saida / "tabela_experimentos.csv"
        with caminho_sintese.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(sintese[0].keys()), lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(sintese)

    if medicoes_brutas:
        caminho_brutas = pasta_saida / "medicoes_brutas.csv"
        with caminho_brutas.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=list(medicoes_brutas[0].keys()), lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(medicoes_brutas)


# ==============================================================================
# 5. ORQUESTRAÇÃO PRINCIPAL DO BENCHMARK
# ==============================================================================

def main() -> None:
    pasta_av2 = Path(__file__).resolve().parent
    pasta_saida = pasta_av2 / "5_resultados"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("ETAPA 6 — BENCHMARK EXPERIMENTAL E CASOS DE TESTE (AV2 - PAA / PROCC-UFS)")
    print("=" * 80)

    itens_totais, tempo_pre_ms, fonte_corpus = carregar_itens_instancia(pasta_av2)
    n_total = len(itens_totais)
    n_meio = max(1, n_total // 2)

    escalas = {
        f"Escala_Reduzida_N{n_meio}": itens_totais[:n_meio],
        f"Escala_Completa_N{n_total}": itens_totais,
    }
    orcamentos_w = [512, 1024, 2048, 4096]
    repeticoes = 3

    medicoes_brutas = []
    sintese_medias = []

    id_medicao = 1
    total_corridas = len(escalas) * len(orcamentos_w) * 2 * repeticoes

    for nome_escala, lista_itens in escalas.items():
        for W in orcamentos_w:
            for nome_algo, func_algo in [
                ("Baseline_Guloso", executar_guloso),
                ("Programacao_Dinamica", executar_programacao_dinamica),
            ]:
                tempos_sel = []
                tempos_tot = []
                memorias = []
                ultimo_res = None

                for rep in range(1, repeticoes + 1):
                    res = medir_execucao(func_algo, lista_itens, W, tempo_pre_ms)
                    registro = {
                        "id_medicao": id_medicao,
                        "escala": nome_escala,
                        "N": len(lista_itens),
                        "W": W,
                        "algoritmo": nome_algo,
                        "repeticao": rep,
                        **res,
                    }
                    medicoes_brutas.append(registro)
                    tempos_sel.append(res["tempo_selecao_ms"])
                    tempos_tot.append(res["tempo_total_fluxo_ms"])
                    memorias.append(res["pico_memoria_kb"])
                    ultimo_res = res
                    id_medicao += 1

                sintese_medias.append({
                    "escala": nome_escala,
                    "N": len(lista_itens),
                    "W": W,
                    "algoritmo": nome_algo,
                    "tempo_preprocessamento_ms": tempo_pre_ms,
                    "tempo_selecao_medio_ms": round(sum(tempos_sel) / len(tempos_sel), 4),
                    "tempo_total_medio_ms": round(sum(tempos_tot) / len(tempos_tot), 4),
                    "memoria_media_kb": round(sum(memorias) / len(memorias), 3),
                    "beneficio_relevancia_bm25": ultimo_res["beneficio_relevancia_bm25"],
                    "tokens_usados": ultimo_res["tokens_usados"],
                    "taxa_ocupacao_janela_pct": ultimo_res["taxa_ocupacao_janela_pct"],
                    "redundancia_ids": ultimo_res["redundancia_ids"],
                    "respeitou_orcamento": ultimo_res["respeitou_orcamento"],
                    "qtd_selecionados": ultimo_res["qtd_selecionados"],
                })

    casos_teste = executar_casos_de_teste(itens_totais)

    # Impressão da Tabela Resumo
    print(f"\nFonte de dados: {fonte_corpus} | Pré-processamento: {tempo_pre_ms:.4f} ms")
    print("=" * 95)
    print(f"{'Escala':<23} | {'W':<5} | {'Algoritmo':<20} | {'Tempo(ms)':<10} | {'Mem(KB)':<9} | {'BM25':<9} | {'Tokens':<6}")
    print("-" * 95)
    for s in sintese_medias:
        print(
            f"{s['escala']:<23} | {s['W']:<5} | {s['algoritmo']:<20} | "
            f"{s['tempo_selecao_medio_ms']:<10.4f} | {s['memoria_media_kb']:<9.2f} | "
            f"{s['beneficio_relevancia_bm25']:<9.4f} | {s['tokens_usados']:<6}"
        )
    print("=" * 95)

    print("\nMATRIZ DOS 8 CASOS DE TESTE OBRIGATÓRIOS (§11):")
    for tc in casos_teste:
        print(f"  [{tc['status']}] {tc['id']} ({tc['cenario']}) -> {tc['observado']}")

    # Metadados completos exigidos na Seção 9 do Edital
    relatorio = {
        "metadados_reprodutibilidade": {
            "etapa": "Etapa 6 — Métricas, Benchmark e Casos de Teste (AV2 - Trilha A)",
            "responsavel": "Laryssa Barbosa de Andrade",
            "sistema_operacional": f"{platform.system()} {platform.release()} ({platform.platform()})",
            "linguagem": f"Python {platform.python_version()}",
            "bibliotecas": ["json", "time", "tracemalloc", "pathlib", "matplotlib"],
            "hardware": f"{platform.machine()} / {platform.processor() or 'Apple Silicon / CPU Padrao'}",
            "corpus": f"7 Documentos Normativos PROCC/UFS ({fonte_corpus})",
            "commit_git": obter_commit_git(),
            "parametros_experimentais": {
                "escalas_N": [n_meio, n_total],
                "orcamentos_W": orcamentos_w,
                "repeticoes_por_cenario": repeticoes,
                "total_medicoes": total_corridas,
            },
            "comando_execucao": "python3 av2/medir_experimentos.py",
            "data_execucao": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "sintese_medias": sintese_medias,
        "casos_de_teste": casos_teste,
        "medicoes_brutas": medicoes_brutas,
    }

    caminho_json = pasta_saida / "relatorio_experimentos.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Relatório JSON salvo em: {caminho_json}")
    gravar_tabelas_csv(sintese_medias, medicoes_brutas, pasta_saida)
    print(f"[OK] Tabelas CSV salvas em: {pasta_saida}")
    gerar_graficos(sintese_medias, pasta_saida)
    print("=" * 80)


if __name__ == "__main__":
    main()
