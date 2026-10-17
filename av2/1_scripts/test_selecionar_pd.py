"""Testes unitários e de integração para a Etapa 3 da AV2 — Programação Dinâmica.

Compatível com pytest e com o módulo padrão unittest do Python.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


DIRETORIO_SCRIPTS = Path(__file__).resolve().parent
if str(DIRETORIO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_SCRIPTS))

from selecionar_pd import (
    executar_selecao_pd_completa,
    resolver_mochila_pd,
)
from selecionar_guloso import (
    selecionar_guloso_instancia,
)


RAIZ = Path(__file__).resolve().parents[2]
ARQUIVO_INSTANCIAS = RAIZ / "av2/3_instancias/instancias.json"


class TesteSelecaoPD(unittest.TestCase):
    """Testes cobrindo otimalidade global, subestrutura ótima e casos de borda da PD."""

    def test_caso_borda_capacidade_zero(self):
        """W = 0 deve retornar lista vazia, tokens 0 e relevância 0."""
        itens = [{"id_chunk": "c1", "v_i": 10.0, "w_i": 50}]
        sel, tokens, rel, total = resolver_mochila_pd(itens, W=0)
        self.assertEqual(sel, [])
        self.assertEqual(tokens, 0)
        self.assertEqual(rel, 0.0)
        self.assertEqual(total, 1)

    def test_caso_borda_todos_maiores_que_w(self):
        """Nenhum item cabe no orçamento."""
        itens = [
            {"id_chunk": "c1", "v_i": 10.0, "w_i": 500},
            {"id_chunk": "c2", "v_i": 20.0, "w_i": 600},
        ]
        sel, tokens, rel, _ = resolver_mochila_pd(itens, W=100)
        self.assertEqual(sel, [])
        self.assertEqual(tokens, 0)
        self.assertEqual(rel, 0.0)

    def test_caso_borda_todos_cabem(self):
        """Capacidade abundante que comporta todos os itens."""
        itens = [
            {"id_chunk": "c1", "v_i": 10.0, "w_i": 50},
            {"id_chunk": "c2", "v_i": 25.0, "w_i": 70},
        ]
        sel, tokens, rel, _ = resolver_mochila_pd(itens, W=200)
        self.assertEqual(len(sel), 2)
        self.assertEqual(tokens, 120)
        self.assertEqual(rel, 35.0)

    def test_rejeicao_capacidade_negativa(self):
        """Capacidade W < 0 deve disparar ValueError."""
        itens = [{"id_chunk": "c1", "v_i": 1.0, "w_i": 10}]
        with self.assertRaises(ValueError):
            resolver_mochila_pd(itens, W=-1)

    def test_contraexemplo_classico_onde_pd_supera_guloso(self):
        """Cenário clássico de mochila onde a heurística gulosa falha e a PD encontra o ótimo.
        
        Item 1: w=6, v=30 (densidade r=5.0)
        Item 2: w=5, v=22 (densidade r=4.4)
        Item 3: w=5, v=22 (densidade r=4.4)
        Capacidade W = 10:
          - Guloso escolhe Item 1 (w=6, v=30), saldo 4 -> não cabem Item 2 nem 3. Total = 30.
          - PD escolhe Item 2 e Item 3 (w=5+5=10, v=22+22=44). Total = 44 (> 30)!
        """
        itens = [
            {"id_chunk": "c1", "v_i": 30.0, "w_i": 6},
            {"id_chunk": "c2", "v_i": 22.0, "w_i": 5},
            {"id_chunk": "c3", "v_i": 22.0, "w_i": 5},
        ]
        W = 10

        # Execução Gulosa
        sel_g, tokens_g, rel_g, _ = selecionar_guloso_instancia(itens, W)
        self.assertEqual([c["id_chunk"] for c in sel_g], ["c1"])
        self.assertEqual(rel_g, 30.0)
        self.assertEqual(tokens_g, 6)

        # Execução Ótima por PD
        sel_pd, tokens_pd, rel_pd, _ = resolver_mochila_pd(itens, W)
        self.assertEqual([c["id_chunk"] for c in sel_pd], ["c2", "c3"])
        self.assertEqual(rel_pd, 44.0)
        self.assertEqual(tokens_pd, 10)

        # Asserção estrita da superioridade da PD
        self.assertGreater(rel_pd, rel_g)

    def test_nao_mutacao_dos_dados_originais(self):
        """Garante que a função da PD não altera a lista ou os dicionários de entrada."""
        itens = [
            {"id_chunk": "c1", "v_i": 5.0, "w_i": 100, "texto": "texto c1"},
            {"id_chunk": "c2", "v_i": 8.0, "w_i": 120, "texto": "texto c2"},
        ]
        copia_profunda = copy.deepcopy(itens)
        resolver_mochila_pd(itens, W=150)
        self.assertEqual(itens, copia_profunda)

    def test_execucao_integrada_instancias_reais_e_invariante_relevancia(self):
        """Validação completa sobre instancias.json assegurando Relevância_PD >= Relevância_Guloso."""
        if not ARQUIVO_INSTANCIAS.is_file():
            self.skipTest(f"Arquivo oficial não encontrado: {ARQUIVO_INSTANCIAS}")

        dados = json.loads(ARQUIVO_INSTANCIAS.read_text(encoding="utf-8"))
        saida_sel_pd, saida_rel_pd, tempos_pd = executar_selecao_pd_completa(dados)

        cenarios_pd = saida_sel_pd["cenarios"]
        itens_map = {it["id_chunk"]: it for it in dados["itens"]}

        for inst in dados["instancias"]:
            wid = inst["id_instancia"]
            W = inst["W"]
            cand_itens = [itens_map[cid] for cid in inst["ids_itens"]]

            info_pd = cenarios_pd[wid]
            sel_pd = info_pd["chunks"]
            tokens_pd = info_pd["tokens_usados"]
            rel_pd = info_pd["relevancia_total"]

            # 1. Restrição de capacidade
            self.assertLessEqual(tokens_pd, W, f"Estouro de capacidade em {wid}")
            self.assertEqual(info_pd["saldo_W"], W - tokens_pd)

            # 2. Cada chunk entra no máximo uma vez
            ids_sel = [c["id_chunk"] for c in sel_pd]
            self.assertEqual(len(ids_sel), len(set(ids_sel)), f"Chunks duplicados em {wid}")

            # 3. Comparação com o baseline guloso
            sel_g, tokens_g, rel_g, _ = selecionar_guloso_instancia(cand_itens, W)

            # INVARIANTE FUNDAMENTAL: PD é sempre maior ou igual ao guloso
            self.assertGreaterEqual(
                rel_pd,
                rel_g - 1e-4,
                f"PD ({rel_pd}) foi inferior ao guloso ({rel_g}) em {wid}",
            )

        # 4. Verificação empírica no orçamento W=4096: PD é ESTRITAMENTE SUPERIOR ao guloso
        rel_pd_4096 = cenarios_pd["W_4096"]["relevancia_total"]
        sel_g_4096, _, rel_g_4096, _ = selecionar_guloso_instancia(
            [itens_map[cid] for cid in dados["instancias"][3]["ids_itens"]], W=4096
        )
        self.assertGreater(
            rel_pd_4096,
            rel_g_4096,
            "Em W=4096 a Programação Dinâmica deve superar estritamente o guloso!",
        )
        self.assertEqual(cenarios_pd["W_4096"]["tokens_usados"], 4093)
        self.assertEqual(cenarios_pd["W_4096"]["saldo_W"], 3)
        self.assertEqual(round(rel_pd_4096, 4), 60.3138)


def test_pytest_compatibilidade():
    """Função avulsa para reconhecimento direto pelo pytest."""
    itens = [{"id_chunk": "t1", "v_i": 5.0, "w_i": 10}]
    sel, tokens, rel, _ = resolver_mochila_pd(itens, W=10)
    assert len(sel) == 1
    assert tokens == 10
    assert rel == 5.0


if __name__ == "__main__":
    unittest.main()

