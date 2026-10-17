"""AV2 — Etapa 2: Seleção de contexto por baseline guloso (Mochila 0/1).

Responsável: Kaio Santos.
Trilha A: Seleção de contexto com orçamento de tokens via heurística gulosa.

Este script:
1. Carrega as instâncias de `av2/3_instancias/instancias.json`;
2. Ordena os candidatos por densidade de relevância decrescente:
       r_i = v_i / w_i  (score BM25 por token)
   com desempate determinístico estrito:
       maior v_i (desc), menor w_i (asc), menor id_chunk (asc);
3. Seleciona itens indivisíveis que cabem no saldo de W para cada capacidade
   (W in {512, 1024, 2048, 4096}), sem interromper a busca ao pular itens que excedem o saldo;
4. Grava os chunks selecionados em `av2/4_selecao_contexto/selecao_gulosa.json`
   e o sumário executivo em `av2/5_resultados/relatorio_guloso.json`.
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


def chave_ordenacao_gulosa(item: dict) -> tuple[float, float, int, str]:
    """Retorna a chave determinística para ordenação da heurística gulosa.
    
    Critérios:
        1. Densidade de relevância decrescente: r_i = v_i / w_i (usamos -r_i para sort asc);
        2. Maior relevância bruta decrescente: -v_i;
        3. Menor custo de tokens crescente: w_i;
        4. Identificador lexicográfico crescente: id_chunk.
    """
    v_i = float(item.get("v_i", 0.0))
    w_i = int(item.get("w_i", 0))
    densidade = (v_i / w_i) if w_i > 0 else 0.0
    cid = str(item.get("id_chunk", ""))
    return (-densidade, -v_i, w_i, cid)


def selecionar_guloso_instancia(
    itens_candidatos: list[dict],
    W: int,
) -> tuple[list[dict], int, float, int]:
    """Aplica o algoritmo guloso sobre uma lista de candidatos para uma capacidade W.
    
    Retorna:
        - selecionados: lista de registros de chunks incluídos no contexto;
        - tokens_usados: total de tokens w_i acumulados na mochila;
        - relevancia_total: soma das relevâncias v_i obtidas;
        - total_avaliados: quantidade de itens candidatos inspecionados.
    """
    if W < 0:
        raise ValueError(f"Capacidade W deve ser não negativa: {W}")

    # Ordenação determinística O(n log n)
    itens_ordenados = sorted(itens_candidatos, key=chave_ordenacao_gulosa)

    tokens_usados = 0
    relevancia_total = 0.0
    selecionados: list[dict] = []

    for rank, item in enumerate(itens_ordenados, start=1):
        custo = item["w_i"]
        relevancia = item["v_i"]

        # Se o item cabe no saldo restante, seleciona
        if tokens_usados + custo <= W:
            tokens_usados += custo
            relevancia_total += relevancia
            densidade = round(relevancia / custo, 6) if custo > 0 else 0.0

            selecionados.append({
                "id_chunk": item["id_chunk"],
                "ordem_selecao": len(selecionados) + 1,
                "rank_densidade": rank,
                "v_i": round(relevancia, 4),
                "w_i": custo,
                "densidade": densidade,
                "id_documento": item.get("id_documento", ""),
                "nome_arquivo": item.get("nome_arquivo", ""),
                "paginas": item.get("paginas", []),
                "texto": item.get("texto", ""),
            })
        # Se não couber, continua a varredura (itens menores posteriores podem caber)

    return selecionados, tokens_usados, round(relevancia_total, 4), len(itens_ordenados)


def executar_selecao_completa(
    dados_instancias: dict,
) -> tuple[dict, dict, dict]:
    """Executa a seleção gulosa para todas as instâncias descritas no JSON de entrada.
    
    Retorna:
        - saida_selecao: dicionário formatado para 4_selecao_contexto/selecao_gulosa.json;
        - saida_relatorio: dicionário formatado para 5_resultados/relatorio_guloso.json;
        - tempos: dicionário com os tempos de execução em segundos.
    """
    t_inicio = time.perf_counter()

    itens_raw = dados_instancias.get("itens", [])
    instancias_raw = dados_instancias.get("instancias", [])
    metadados_entrada = dados_instancias.get("metadados", {})

    if not isinstance(itens_raw, list) or not itens_raw:
        raise ValueError("Entrada deve conter uma lista não vazia de 'itens'.")
    if not isinstance(instancias_raw, list) or not instancias_raw:
        raise ValueError("Entrada deve conter uma lista não vazia de 'instancias'.")

    # Indexação hash O(n) por id_chunk
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
            selecionar_guloso_instancia(candidatos, W)
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

    tempo_selecao_ram = time.perf_counter() - t_processamento_inicio
    tempo_total_processamento = time.perf_counter() - t_inicio

    saida_selecao = {
        "metadados": {
            "etapa": "av2_2_selecao_baseline_gulosa",
            "responsavel": "Kaio Santos",
            "estrategia": "densidade_relevancia_vi_por_wi",
            "criterio_desempate": "maior_densidade_desc, maior_vi_desc, menor_wi_asc, id_chunk_asc",
            "consulta": metadados_entrada.get("consulta", ""),
            "metrica_score": metadados_entrada.get("metrica_score", ""),
            "total_itens_universo": len(itens_map),
            "instancias_processadas": [inst.get("W") for inst in instancias_raw],
        },
        "cenarios": cenarios_selecao,
    }

    saida_relatorio = {
        "metadados": {
            "etapa": "av2_2_relatorio_baseline_gulosa",
            "responsavel": "Kaio Santos",
            "data_utc": datetime.now(timezone.utc).isoformat(),
            "consulta": metadados_entrada.get("consulta", ""),
            "metrica_score": metadados_entrada.get("metrica_score", ""),
            "total_candidatos_positivos": len(itens_map),
            "algoritmo": "heuristica_gulosa_densidade",
            "complexidade_assintotica": {
                "tempo": "O(n log n + B * n) = O(n log n)",
                "espaco": "O(n)",
            },
        },
        "resumo_cenarios": resumo_cenarios,
        "tempos_segundos": {
            "selecao_gulosa_ram": tempo_selecao_ram,
            "tempo_processamento_total": tempo_total_processamento,
        },
    }

    return saida_selecao, saida_relatorio, {
        "selecao_ram": tempo_selecao_ram,
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
        default=RAIZ / "av2/4_selecao_contexto/selecao_gulosa.json",
        help="Arquivo JSON de saída dos contextos selecionados.",
    )
    parser.add_argument(
        "--saida-relatorio",
        type=Path,
        default=RAIZ / "av2/5_resultados/relatorio_guloso.json",
        help="Arquivo JSON com métricas e sumário executivo.",
    )
    args = parser.parse_args(argv)

    if not args.instancias.is_file():
        sys.stderr.write(f"Erro: arquivo de instâncias não encontrado: {args.instancias}\n")
        return 1

    t0 = time.perf_counter()
    conteudo_bytes = args.instancias.read_bytes()
    dados_instancias = json.loads(conteudo_bytes.decode("utf-8"))
    tempo_io_leitura = time.perf_counter() - t0

    saida_selecao, saida_relatorio, tempos = executar_selecao_completa(dados_instancias)

    t_escrita = time.perf_counter()
    salvar_json(args.saida_selecao, saida_selecao)
    salvar_json(args.saida_relatorio, saida_relatorio)
    tempo_io_escrita = time.perf_counter() - t_escrita

    saida_relatorio["tempos_segundos"]["leitura_io"] = tempo_io_leitura
    saida_relatorio["tempos_segundos"]["escrita_io"] = tempo_io_escrita
    salvar_json(args.saida_relatorio, saida_relatorio)

    print("=== AV2 - Etapa 2: Seleção Gulosa Concluída ===")
    print(f"Instâncias lidas de: {args.instancias}")
    for resumo in saida_relatorio["resumo_cenarios"]:
        print(
            f"  [W={resumo['W']:4d}] "
            f"Chunks: {resumo['total_chunks_selecionados']:2d} | "
            f"Tokens: {resumo['tokens_usados']:4d}/{resumo['W']:4d} (Saldo: {resumo['saldo_W']:3d}, Ocupação: {resumo['taxa_ocupacao_percentual']:5.1f}%) | "
            f"Relevância total: {resumo['relevancia_total']:7.4f}"
        )
    print(f"Contexto salvo em: {args.saida_selecao}")
    print(f"Relatório salvo em: {args.saida_relatorio}")
    print(f"Tempo em RAM: {tempos['selecao_ram']:.6f}s | Tempo total: {tempo_io_leitura + tempos['selecao_ram'] + tempo_io_escrita:.6f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
