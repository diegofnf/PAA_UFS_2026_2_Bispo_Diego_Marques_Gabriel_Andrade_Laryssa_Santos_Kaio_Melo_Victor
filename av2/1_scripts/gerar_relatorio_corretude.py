"""Gera as evidências da Etapa 4 sem reexecutar as etapas anteriores."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
AV2 = RAIZ / "av2"
CAMINHO_INSTANCIAS = AV2 / "3_instancias/instancias.json"
CAMINHO_GULOSO = AV2 / "5_resultados/relatorio_guloso.json"
CAMINHO_PD = AV2 / "5_resultados/relatorio_pd.json"
CAMINHO_CONTRAEXEMPLO = AV2 / "4_selecao_contexto/contraexemplo_guloso.json"
CAMINHO_RELATORIO = AV2 / "5_resultados/relatorio_corretude_limites.json"


def carregar_json(caminho: Path) -> dict:
    if not caminho.is_file():
        raise FileNotFoundError(f"Artefato necessário não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def construir_contraexemplo() -> dict:
    itens = [
        {"id_item": "A", "w_i": 6, "v_i": 30.0, "densidade": 5.0},
        {"id_item": "B", "w_i": 5, "v_i": 22.0, "densidade": 4.4},
        {"id_item": "C", "w_i": 5, "v_i": 22.0, "densidade": 4.4},
    ]
    return {
        "capacidade_W": 10,
        "itens": itens,
        "guloso": {
            "ids_selecionados": ["A"],
            "tokens_usados": 6,
            "relevancia_total": 30.0,
        },
        "programacao_dinamica": {
            "ids_selecionados": ["B", "C"],
            "tokens_usados": 10,
            "relevancia_total": 44.0,
        },
        "conclusao": "A densidade v_i/w_i não garante o ótimo na mochila 0/1.",
    }


def construir_relatorio(dados_guloso: dict, dados_pd: dict) -> dict:
    cenarios_guloso = {
        cenario["W"]: cenario for cenario in dados_guloso["resumo_cenarios"]
    }
    comparacao = []

    for cenario_pd in dados_pd["resumo_cenarios"]:
        capacidade = cenario_pd["W"]
        cenario_guloso = cenarios_guloso[capacidade]
        ganho = round(
            cenario_pd["relevancia_total"] - cenario_guloso["relevancia_total"],
            4,
        )
        if cenario_pd["tokens_usados"] > capacidade:
            raise AssertionError(f"PD excedeu W={capacidade}")
        if cenario_pd["relevancia_total"] < cenario_guloso["relevancia_total"] - 1e-4:
            raise AssertionError(f"PD inferior ao guloso em W={capacidade}")

        comparacao.append({
            "W": capacidade,
            "guloso": {
                "tokens_usados": cenario_guloso["tokens_usados"],
                "relevancia_total": cenario_guloso["relevancia_total"],
                "total_chunks_selecionados": cenario_guloso["total_chunks_selecionados"],
            },
            "programacao_dinamica": {
                "tokens_usados": cenario_pd["tokens_usados"],
                "relevancia_total": cenario_pd["relevancia_total"],
                "total_chunks_selecionados": cenario_pd["total_chunks_selecionados"],
            },
            "ganho_relevancia_pd": ganho,
        })

    return {
        "metadados": {
            "etapa": "av2_4_corretude_e_limites_teoricos",
            "responsavel": "Gabriel Marques",
            "data_utc": datetime.now(timezone.utc).isoformat(),
            "entrada_reutilizada": [
                "3_instancias/instancias.json",
                "5_resultados/relatorio_guloso.json",
                "5_resultados/relatorio_pd.json",
            ],
        },
        "comparacao_por_orcamento": comparacao,
        "testes_especificos": "1_scripts/test_corretude_limites.py",
    }


def main() -> int:
    dados_instancias = carregar_json(CAMINHO_INSTANCIAS)
    dados_guloso = carregar_json(CAMINHO_GULOSO)
    dados_pd = carregar_json(CAMINHO_PD)

    contraexemplo = construir_contraexemplo()
    relatorio = construir_relatorio(dados_guloso, dados_pd)
    relatorio["metadados"]["total_candidatos"] = len(dados_instancias.get("itens", []))
    relatorio["metadados"]["orcamentos"] = [
        cenario["W"] for cenario in dados_instancias.get("instancias", [])
    ]

    salvar_json(CAMINHO_CONTRAEXEMPLO, contraexemplo)
    salvar_json(CAMINHO_RELATORIO, relatorio)

    print(f"Contraexemplo salvo em: {CAMINHO_CONTRAEXEMPLO}")
    print(f"Relatório salvo em: {CAMINHO_RELATORIO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())