"""AV2 — Etapa 3: Seleção ótima de contexto por Programação Dinâmica (Mochila 0/1).

Responsáveis: Diego Bispo e Kaio Santos.
Trilha A: Seleção de contexto com orçamento de tokens via solução exata por PD.

Este script:
1. Carrega as instâncias de `av2/3_instancias/instancias.json`;
2. Resolve o Problema da Mochila 0/1 exata via tabulação bottom-up
   utilizando a Equação de Bellman:
       DP[i][c] = max(DP[i-1][c], DP[i-1][c - w_i] + v_i)
3. Reconstrói o conjunto ótimo de chunks selecionados via backtracking
   a partir de DP[n][W], garantindo que cada chunk entre no máximo uma vez
   e que a soma dos tokens não exceda W;
4. Grava os chunks selecionados em `av2/4_selecao_contexto/selecao_pd.json`
   e o sumário executivo em `av2/5_resultados/relatorio_pd.json`.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]


def resolver_mochila_pd(
    itens_candidatos: list[dict],
    W: int,
) -> tuple[list[dict], int, float, int]:
    """Resolve a Mochila 0/1 exata para a capacidade W via Programação Dinâmica bottom-up.
    
    Retorna:
        - selecionados: lista de registros de chunks incluídos na solução ótima;
        - tokens_usados: soma dos tokens w_i dos chunks selecionados (<= W);
        - relevancia_total: relevância máxima obtida sum(v_i);
        - total_avaliados: total de candidatos considerados (n).
    """
    if W < 0:
        raise ValueError(f"Capacidade W deve ser não negativa: {W}")

    n = len(itens_candidatos)
    if W == 0 or n == 0:
        return [], 0, 0.0, n

    # Matriz DP de dimensões (n + 1) x (W + 1)
    # dp[i][c] armazena a relevância máxima usando um subconjunto dos primeiros i itens com capacidade c
    dp: list[list[float]] = [[0.0] * (W + 1) for _ in range(n + 1)]
    # Matriz booleana de decisões para backtracking determinístico
    take: list[list[bool]] = [[False] * (W + 1) for _ in range(n + 1)]

    # Preenchimento bottom-up da tabela DP
    for i in range(1, n + 1):
        item = itens_candidatos[i - 1]
        w_i = int(item["w_i"])
        v_i = float(item["v_i"])

        for c in range(W + 1):
            if w_i <= c:
                val_com = dp[i - 1][c - w_i] + v_i
                val_sem = dp[i - 1][c]
                # Tolerância numérica de 1e-9 para desempate estável em floats
                if val_com > val_sem + 1e-9:
                    dp[i][c] = val_com
                    take[i][c] = True
                else:
                    dp[i][c] = val_sem
                    take[i][c] = False
            else:
                dp[i][c] = dp[i - 1][c]
                take[i][c] = False

    # Backtracking determinístico a partir de (n, W)
    curr_c = W
    indices_selecionados: list[int] = []

    for i in range(n, 0, -1):
        if take[i][curr_c]:
            indices_selecionados.append(i - 1)
            curr_c -= int(itens_candidatos[i - 1]["w_i"])

    indices_selecionados.reverse()

    selecionados: list[dict] = []
    tokens_usados = 0
    relevancia_acumulada = 0.0

    for ordem, idx in enumerate(indices_selecionados, start=1):
        item = itens_candidatos[idx]
        w_i = int(item["w_i"])
        v_i = float(item["v_i"])
        tokens_usados += w_i
        relevancia_acumulada += v_i
        densidade = round(v_i / w_i, 6) if w_i > 0 else 0.0

        selecionados.append({
            "id_chunk": item["id_chunk"],
            "ordem_selecao": ordem,
            "v_i": round(v_i, 4),
            "w_i": w_i,
            "densidade": densidade,
            "id_documento": item.get("id_documento", ""),
            "nome_arquivo": item.get("nome_arquivo", ""),
            "paginas": item.get("paginas", []),
            "texto": item.get("texto", ""),
        })

    return selecionados, tokens_usados, round(relevancia_acumulada, 4), n


def executar_selecao_pd_completa(
    dados_instancias: dict,
) -> tuple[dict, dict, dict]:
    """Executa a seleção por Programação Dinâmica para todas as instâncias do JSON.
    
    Retorna:
        - saida_selecao: dicionário formatado para 4_selecao_contexto/selecao_pd.json;
        - saida_relatorio: dicionário formatado para 5_resultados/relatorio_pd.json;
        - tempos: dicionário de tempos de execução.
    """
    t_inicio = time.perf_counter()

    itens_raw = dados_instancias.get("itens", [])
    instancias_raw = dados_instancias.get("instancias", [])
    metadados_entrada = dados_instancias.get("metadados", {})

    if not isinstance(itens_raw, list) or not itens_raw:
        raise ValueError("Entrada deve conter uma lista não vazia de 'itens'.")
    if not isinstance(instancias_raw, list) or not instancias_raw:
        raise ValueError("Entrada deve conter uma lista não vazia de 'instancias'.")

    # Indexação hash O(n)
    itens_map: dict[str, dict] = {}
    for item in itens_raw:
        cid = item.get("id_chunk")
        if not cid or cid in itens_map:
            raise ValueError(f"id_chunk ausente ou duplicado: {cid!r}")
        w_i = item.get("w_i")
        v_i = item.get("v_i")
        if type(w_i) is not int or w_i <= 0:
            raise ValueError(f"Item {cid} possui custo w_i inválido: {w_i!r}")
        if not isinstance(v_i, (int, float)) or not math.isfinite(v_i) or v_i < 0:
            raise ValueError(f"Item {cid} possui score v_i inválido: {v_i!r}")
        itens_map[cid] = item

    cenarios_selecao: dict[str, dict] = {}
    resumo_cenarios: list[dict] = []

    t_processamento_inicio = time.perf_counter()

    for inst in instancias_raw:
        id_instancia = inst.get("id_instancia", f"W_{inst.get('W')}")
        W = inst.get("W")
        if type(W) is not int or W < 0:
            raise ValueError(f"Capacidade W inválida na instância {id_instancia}: {W!r}")

        ids_candidatos = inst.get("ids_itens", list(itens_map.keys()))
        candidatos = []
        for cid in ids_candidatos:
            if cid not in itens_map:
                raise ValueError(f"Instância {id_instancia} referencia chunk inexistente: {cid}")
            candidatos.append(itens_map[cid])

        selecionados, tokens_usados, relevancia_total, total_avaliados = (
            resolver_mochila_pd(candidatos, W)
        )

        saldo_W = W - tokens_usados
        taxa_ocupacao = round((tokens_usados / W * 100.0), 2) if W > 0 else 0.0

        cenarios_selecao[id_instancia] = {
            "id_instancia": id_instancia,
            "W": W,
            "tokens_usados": tokens_usados,
            "saldo_W": saldo_W,
            "taxa_ocupacao_percentual": taxa_ocupacao,
            "relevancia_total": relevancia_total,
            "total_chunks_selecionados": len(selecionados),
            "total_candidatos_avaliados": total_avaliados,
            "ids_selecionados": [c["id_chunk"] for c in selecionados],
            "chunks": selecionados,
        }

        resumo_cenarios.append({
            "id_instancia": id_instancia,
            "W": W,
            "tokens_usados": tokens_usados,
            "saldo_W": saldo_W,
            "taxa_ocupacao_percentual": taxa_ocupacao,
            "relevancia_total": relevancia_total,
            "total_chunks_selecionados": len(selecionados),
            "ids_selecionados": [c["id_chunk"] for c in selecionados],
        })

    tempo_pd_ram = time.perf_counter() - t_processamento_inicio
    tempo_total_processamento = time.perf_counter() - t_inicio

    saida_selecao = {
        "metadados": {
            "etapa": "av2_3_selecao_otima_programacao_dinamica",
            "responsaveis": ["Diego Bispo", "Kaio Santos"],
            "estrategia": "mochila_01_exata_tabulacao_bellman",
            "garantia_matematica": "otimo_global_exato",
            "consulta": metadados_entrada.get("consulta", ""),
            "metrica_score": metadados_entrada.get("metrica_score", ""),
            "total_itens_universo": len(itens_map),
            "instancias_processadas": [inst.get("W") for inst in instancias_raw],
        },
        "cenarios": cenarios_selecao,
    }

    saida_relatorio = {
        "metadados": {
            "etapa": "av2_3_relatorio_programacao_dinamica",
            "responsaveis": ["Diego Bispo", "Kaio Santos"],
            "data_utc": datetime.now(timezone.utc).isoformat(),
            "consulta": metadados_entrada.get("consulta", ""),
            "metrica_score": metadados_entrada.get("metrica_score", ""),
            "total_candidatos_positivos": len(itens_map),
            "algoritmo": "programacao_dinamica_bottom_up",
            "equacao_recorrencia": "DP[i][c] = max(DP[i-1][c], DP[i-1][c - w_i] + v_i)",
            "complexidade_assintotica": {
                "tempo": "O(n * W)",
                "espaco": "O(n * W)",
            },
        },
        "resumo_cenarios": resumo_cenarios,
        "tempos_segundos": {
            "selecao_pd_ram": tempo_pd_ram,
            "tempo_processamento_total": tempo_total_processamento,
        },
    }

    return saida_selecao, saida_relatorio, {
        "selecao_ram": tempo_pd_ram,
        "total": tempo_total_processamento,
    }


def salvar_json(caminho: Path, dados: dict) -> None:
    """Salva dados em formato JSON UTF-8 com indentação padronizada."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    caminho.write_text(texto, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """Função principal com suporte a execução CLI e funcional."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instancias",
        type=Path,
        default=RAIZ / "av2/3_instancias/instancias.json",
        help="Caminho do arquivo de instâncias de entrada.",
    )
    parser.add_argument(
        "--saida-selecao",
        type=Path,
        default=RAIZ / "av2/4_selecao_contexto/selecao_pd.json",
        help="Arquivo JSON de saída dos contextos ótimos selecionados.",
    )
    parser.add_argument(
        "--saida-relatorio",
        type=Path,
        default=RAIZ / "av2/5_resultados/relatorio_pd.json",
        help="Arquivo JSON com métricas e sumário executivo da PD.",
    )
    args = parser.parse_args(argv)

    if not args.instancias.is_file():
        sys.stderr.write(f"Erro: arquivo de instâncias não encontrado: {args.instancias}\n")
        return 1

    t0 = time.perf_counter()
    conteudo_bytes = args.instancias.read_bytes()
    dados_instancias = json.loads(conteudo_bytes.decode("utf-8"))
    tempo_io_leitura = time.perf_counter() - t0

    saida_selecao, saida_relatorio, tempos = executar_selecao_pd_completa(dados_instancias)

    t_escrita = time.perf_counter()
    salvar_json(args.saida_selecao, saida_selecao)
    salvar_json(args.saida_relatorio, saida_relatorio)
    tempo_io_escrita = time.perf_counter() - t_escrita

    saida_relatorio["tempos_segundos"]["leitura_io"] = tempo_io_leitura
    saida_relatorio["tempos_segundos"]["escrita_io"] = tempo_io_escrita
    salvar_json(args.saida_relatorio, saida_relatorio)

    print("=== AV2 - Etapa 3: Seleção por Programação Dinâmica Concluída ===")
    print(f"Instâncias lidas de: {args.instancias}")
    for resumo in saida_relatorio["resumo_cenarios"]:
        print(
            f"  [W={resumo['W']:4d}] "
            f"Chunks: {resumo['total_chunks_selecionados']:2d} | "
            f"Tokens: {resumo['tokens_usados']:4d}/{resumo['W']:4d} (Saldo: {resumo['saldo_W']:3d}, Ocupação: {resumo['taxa_ocupacao_percentual']:5.1f}%) | "
            f"Relevância total: {resumo['relevancia_total']:7.4f}"
        )
    print(f"Contexto ótimo salvo em: {args.saida_selecao}")
    print(f"Relatório de PD salvo em: {args.saida_relatorio}")
    print(f"Tempo em RAM: {tempos['selecao_ram']:.6f}s | Tempo total: {tempo_io_leitura + tempos['selecao_ram'] + tempo_io_escrita:.6f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())

