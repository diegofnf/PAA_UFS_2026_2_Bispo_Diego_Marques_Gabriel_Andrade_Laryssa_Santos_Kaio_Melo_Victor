"""Testes de corretude e limites teóricos da AV2."""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import pytest


DIRETORIO_SCRIPTS = Path(__file__).resolve().parent
if str(DIRETORIO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_SCRIPTS))

from selecionar_guloso import selecionar_guloso_instancia
from selecionar_pd import resolver_mochila_pd


RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_INSTANCIAS = RAIZ / "av2/3_instancias/instancias.json"
ARQUIVO_CONTRAEXEMPLO = RAIZ / "av2/4_selecao_contexto/contraexemplo_guloso.json"
ARQUIVO_RELATORIO = RAIZ / "av2/5_resultados/relatorio_corretude_limites.json"


def valor_otimo_por_forca_bruta(itens: list[dict], capacidade: int) -> float:
    """Calcula o ótimo de uma instância pequena sem usar a implementação da PD."""
    melhor_valor = 0.0
    for mascara in itertools.product((False, True), repeat=len(itens)):
        peso = sum(
            int(item["w_i"])
            for item, incluir in zip(itens, mascara)
            if incluir
        )
        if peso > capacidade:
            continue
        valor = sum(
            float(item["v_i"])
            for item, incluir in zip(itens, mascara)
            if incluir
        )
        melhor_valor = max(melhor_valor, valor)
    return round(melhor_valor, 4)


def carregar_instancias_reais() -> dict:
    if not ARQUIVO_INSTANCIAS.is_file():
        pytest.fail(f"Arquivo de instâncias não encontrado: {ARQUIVO_INSTANCIAS}")
    return json.loads(ARQUIVO_INSTANCIAS.read_text(encoding="utf-8"))


def test_contraexemplo_operacional_da_falha_gulosa():
    itens = [
        {"id_chunk": "a", "w_i": 6, "v_i": 30.0},
        {"id_chunk": "b", "w_i": 5, "v_i": 22.0},
        {"id_chunk": "c", "w_i": 5, "v_i": 22.0},
    ]

    selecionados_g, tokens_g, valor_g, _ = selecionar_guloso_instancia(itens, 10)
    selecionados_pd, tokens_pd, valor_pd, _ = resolver_mochila_pd(itens, 10)

    assert [item["id_chunk"] for item in selecionados_g] == ["a"]
    assert tokens_g == 6
    assert valor_g == 30.0
    assert [item["id_chunk"] for item in selecionados_pd] == ["b", "c"]
    assert tokens_pd == 10
    assert valor_pd == 44.0
    assert valor_pd > valor_g


def test_pd_atinge_otimo_por_forca_bruta():
    itens = [
        {"id_chunk": "a", "w_i": 4, "v_i": 8.0},
        {"id_chunk": "b", "w_i": 6, "v_i": 11.0},
        {"id_chunk": "c", "w_i": 7, "v_i": 13.0},
        {"id_chunk": "d", "w_i": 3, "v_i": 6.0},
    ]

    selecionados, tokens, valor, _ = resolver_mochila_pd(itens, 10)

    assert valor == valor_otimo_por_forca_bruta(itens, 10)
    assert tokens == sum(item["w_i"] for item in selecionados)
    assert valor == round(sum(item["v_i"] for item in selecionados), 4)


def test_reconstrucao_respeita_invariantes_nos_quatro_orcamentos():
    dados = carregar_instancias_reais()
    itens_por_id = {item["id_chunk"]: item for item in dados["itens"]}

    for instancia in dados["instancias"]:
        candidatos = [itens_por_id[item_id] for item_id in instancia["ids_itens"]]
        selecionados, tokens, valor, total = resolver_mochila_pd(candidatos, instancia["W"])
        ids_selecionados = [item["id_chunk"] for item in selecionados]

        assert total == len(candidatos)
        assert tokens <= instancia["W"]
        assert len(ids_selecionados) == len(set(ids_selecionados))
        assert set(ids_selecionados) <= set(instancia["ids_itens"])
        assert tokens == sum(item["w_i"] for item in selecionados)
        assert valor == round(sum(item["v_i"] for item in selecionados), 4)


def test_pd_empata_ou_supera_guloso_nos_resultados_reais():
    dados = carregar_instancias_reais()
    itens_por_id = {item["id_chunk"]: item for item in dados["itens"]}

    for instancia in dados["instancias"]:
        candidatos = [itens_por_id[item_id] for item_id in instancia["ids_itens"]]
        _, _, valor_guloso, _ = selecionar_guloso_instancia(candidatos, instancia["W"])
        _, _, valor_pd, _ = resolver_mochila_pd(candidatos, instancia["W"])
        assert valor_pd >= valor_guloso - 1e-4

    instancia_4096 = next(item for item in dados["instancias"] if item["W"] == 4096)
    candidatos_4096 = [itens_por_id[item_id] for item_id in instancia_4096["ids_itens"]]
    _, _, valor_guloso_4096, _ = selecionar_guloso_instancia(candidatos_4096, 4096)
    _, _, valor_pd_4096, _ = resolver_mochila_pd(candidatos_4096, 4096)
    assert valor_pd_4096 > valor_guloso_4096


def test_etapa_4_gera_relatorios_evidencias():
    assert ARQUIVO_CONTRAEXEMPLO.is_file()
    assert ARQUIVO_RELATORIO.is_file()

    contraexemplo = json.loads(ARQUIVO_CONTRAEXEMPLO.read_text(encoding="utf-8"))
    relatorio = json.loads(ARQUIVO_RELATORIO.read_text(encoding="utf-8"))

    assert contraexemplo["guloso"]["relevancia_total"] == 30.0
    assert contraexemplo["programacao_dinamica"]["relevancia_total"] == 44.0
    assert relatorio["metadados"]["orcamentos"] == [512, 1024, 2048, 4096]
    assert len(relatorio["comparacao_por_orcamento"]) == 4