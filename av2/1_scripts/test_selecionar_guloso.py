"""Testes unitários e de integração para a Etapa 2 da AV2 — Seleção Gulosa.

Compatível com pytest e com o módulo padrão unittest do Python.
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import sys

DIRETORIO_SCRIPTS = Path(__file__).resolve().parent
if str(DIRETORIO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_SCRIPTS))

from selecionar_guloso import (
    chave_ordenacao_gulosa,
    executar_selecao_completa,
    selecionar_guloso_instancia,
)


RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_INSTANCIAS = RAIZ / "av2/3_instancias/instancias.json"


class TesteSelecaoGulosa(unittest.TestCase):
    """Conjunto de testes cobrindo corretude, desempate determinístico e casos de borda."""

    def test_desempate_deterministico_completo(self):
        """Valida os 4 níveis de desempate da ordenação gulosa."""
        # 1. Maior densidade r_i = v_i / w_i
        it_a = {"id_chunk": "c1", "v_i": 10.0, "w_i": 100}  # r = 0.10
        it_b = {"id_chunk": "c2", "v_i": 15.0, "w_i": 100}  # r = 0.15
        self.assertLess(chave_ordenacao_gulosa(it_b), chave_ordenacao_gulosa(it_a))

        # 2. Mesma densidade, maior relevância v_i
        it_c = {"id_chunk": "c3", "v_i": 20.0, "w_i": 200}  # r = 0.10, v = 20
        it_d = {"id_chunk": "c4", "v_i": 10.0, "w_i": 100}  # r = 0.10, v = 10
        self.assertLess(chave_ordenacao_gulosa(it_c), chave_ordenacao_gulosa(it_d))

        # 3. Mesma densidade e mesmo v_i, menor custo w_i
        # (caso matematicamente só possível com v_i=0 ou com frações idênticas, mas checamos a regra)
        it_e = {"id_chunk": "c5", "v_i": 5.0, "w_i": 50}
        it_f = {"id_chunk": "c6", "v_i": 5.0, "w_i": 60}
        # it_e tem maior densidade (0.1 > 0.0833), então it_e vence
        self.assertLess(chave_ordenacao_gulosa(it_e), chave_ordenacao_gulosa(it_f))

        # 4. Todos os valores numéricos iguais, desempate pelo id_chunk lexicográfico
        it_g = {"id_chunk": "chunk_0010", "v_i": 5.0, "w_i": 50}
        it_h = {"id_chunk": "chunk_0020", "v_i": 5.0, "w_i": 50}
        self.assertLess(chave_ordenacao_gulosa(it_g), chave_ordenacao_gulosa(it_h))

    def test_nao_interrupcao_ao_pular_item_que_nao_cabe(self):
        """Garante que a varredura continua e seleciona itens menores subsequentes."""
        itens = [
            {"id_chunk": "c1", "v_i": 10.0, "w_i": 50, "texto": "A"},  # r = 0.20
            {"id_chunk": "c2", "v_i": 15.0, "w_i": 100, "texto": "B"}, # r = 0.15
            {"id_chunk": "c3", "v_i": 3.0, "w_i": 30, "texto": "C"},   # r = 0.10
        ]
        # Orçamento W = 90
        # c1 entra: tokens = 50, saldo = 40
        # c2 não cabe (100 > 40), deve ser pulado!
        # c3 cabe (30 <= 40), deve entrar! tokens = 80, saldo = 10
        sel, tokens, rel, total = selecionar_guloso_instancia(itens, W=90)
        self.assertEqual(len(sel), 2)
        self.assertEqual([c["id_chunk"] for c in sel], ["c1", "c3"])
        self.assertEqual(tokens, 80)
        self.assertEqual(rel, 13.0)
        self.assertEqual(total, 3)

    def test_caso_borda_capacidade_zero(self):
        """W = 0 deve retornar 0 selecionados e saldo 0 sem lançar erro."""
        itens = [{"id_chunk": "c1", "v_i": 10.0, "w_i": 50}]
        sel, tokens, rel, total = selecionar_guloso_instancia(itens, W=0)
        self.assertEqual(sel, [])
        self.assertEqual(tokens, 0)
        self.assertEqual(rel, 0.0)

    def test_caso_borda_todos_maiores_que_w(self):
        """Nenhum item cabe no orçamento."""
        itens = [
            {"id_chunk": "c1", "v_i": 10.0, "w_i": 500},
            {"id_chunk": "c2", "v_i": 20.0, "w_i": 600},
        ]
        sel, tokens, rel, _ = selecionar_guloso_instancia(itens, W=100)
        self.assertEqual(sel, [])
        self.assertEqual(tokens, 0)
        self.assertEqual(rel, 0.0)

    def test_caso_borda_todos_cabem(self):
        """Orçamento abundante que comporta todos os itens."""
        itens = [
            {"id_chunk": "c1", "v_i": 10.0, "w_i": 50},
            {"id_chunk": "c2", "v_i": 20.0, "w_i": 50},
        ]
        sel, tokens, rel, _ = selecionar_guloso_instancia(itens, W=500)
        self.assertEqual(len(sel), 2)
        self.assertEqual(tokens, 100)
        self.assertEqual(rel, 30.0)
        # c2 (r=0.4) deve ser selecionado antes de c1 (r=0.2)
        self.assertEqual([c["id_chunk"] for c in sel], ["c2", "c1"])

    def test_rejeicao_capacidade_negativa(self):
        """Capacidade W < 0 deve disparar ValueError."""
        itens = [{"id_chunk": "c1", "v_i": 1.0, "w_i": 10}]
        with self.assertRaises(ValueError):
            selecionar_guloso_instancia(itens, W=-1)

    def test_validacao_itens_invalidos(self):
        """Valida que itens com w_i inválido ou IDs duplicados são rejeitados."""
        dados_custo_zero = {
            "itens": [{"id_chunk": "c1", "v_i": 1.0, "w_i": 0}],
            "instancias": [{"id_instancia": "W_100", "W": 100, "ids_itens": ["c1"]}],
        }
        with self.assertRaises(ValueError):
            executar_selecao_completa(dados_custo_zero)

        dados_duplicados = {
            "itens": [
                {"id_chunk": "c1", "v_i": 1.0, "w_i": 10},
                {"id_chunk": "c1", "v_i": 2.0, "w_i": 20},
            ],
            "instancias": [{"id_instancia": "W_100", "W": 100, "ids_itens": ["c1"]}],
        }
        with self.assertRaises(ValueError):
            executar_selecao_completa(dados_duplicados)

    def test_nao_mutacao_dos_dados_originais(self):
        """A função de seleção não deve alterar os dicionários de entrada."""
        itens = [
            {"id_chunk": "c1", "v_i": 5.0, "w_i": 100, "texto": "texto c1"},
            {"id_chunk": "c2", "v_i": 8.0, "w_i": 120, "texto": "texto c2"},
        ]
        copia_profunda = copy.deepcopy(itens)
        selecionar_guloso_instancia(itens, W=150)
        self.assertEqual(itens, copia_profunda)

    def test_execucao_integrada_instancias_reais(self):
        """Executa a seleção completa sobre o arquivo oficial `instancias.json`."""
        if not ARQUIVO_INSTANCIAS.is_file():
            self.skipTest(f"Arquivo oficial não encontrado: {ARQUIVO_INSTANCIAS}")

        dados = json.loads(ARQUIVO_INSTANCIAS.read_text(encoding="utf-8"))
        saida_sel, saida_rel, tempos = executar_selecao_completa(dados)

        cenarios = saida_sel["cenarios"]
        self.assertIn("W_512", cenarios)
        self.assertIn("W_1024", cenarios)
        self.assertIn("W_2048", cenarios)
        self.assertIn("W_4096", cenarios)

        # Checagens de viabilidade: tokens_usados <= W para todos os cenários
        for wid, info in cenarios.items():
            W = info["W"]
            tokens = info["tokens_usados"]
            self.assertLessEqual(tokens, W, f"Estouro de capacidade em {wid}")
            self.assertEqual(info["saldo_W"], W - tokens)
            self.assertGreater(info["relevancia_total"], 0.0)

        # W=512 deve selecionar chunk_0131 (maior densidade)
        self.assertEqual(cenarios["W_512"]["ids_selecionados"], ["chunk_0131"])
        self.assertEqual(cenarios["W_512"]["tokens_usados"], 370)
        self.assertEqual(cenarios["W_512"]["saldo_W"], 142)

        # W=1024 deve selecionar chunk_0131 e chunk_0018
        self.assertEqual(cenarios["W_1024"]["ids_selecionados"], ["chunk_0131", "chunk_0018"])
        self.assertEqual(cenarios["W_1024"]["tokens_usados"], 761)

        # O crescimento de relevância deve ser monótono não decrescente com o aumento de W
        rels = [
            cenarios["W_512"]["relevancia_total"],
            cenarios["W_1024"]["relevancia_total"],
            cenarios["W_2048"]["relevancia_total"],
            cenarios["W_4096"]["relevancia_total"],
        ]
        self.assertTrue(rels[0] < rels[1] < rels[2] < rels[3])


def test_pytest_compatibilidade():
    """Função avulsa para reconhecimento direto pelo pytest."""
    item = {"id_chunk": "teste", "v_i": 10.0, "w_i": 100}
    chave = chave_ordenacao_gulosa(item)
    assert chave[0] == -0.1
    assert chave[1] == -10.0
    assert chave[2] == 100
    assert chave[3] == "teste"


if __name__ == "__main__":
    unittest.main()
