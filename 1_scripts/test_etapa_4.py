"""Testes de unidade e casos de borda da Etapa 4 (BM25 e Pontuação Simples)."""

import json
import math
import sys
import unittest
from pathlib import Path

# Adiciona o diretório dos scripts ao path
diretorio_scripts = Path(__file__).resolve().parent
sys.path.insert(0, str(diretorio_scripts))

from importlib.machinery import SourceFileLoader
buscar_modulo = SourceFileLoader("buscar_e_ordenar", str(diretorio_scripts / "4_buscar_e_ordenar.py")).load_module()


class TestEtapa4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raiz = diretorio_scripts.parent
        caminho_chunks = raiz / "4_chunks" / "chunks.json"
        caminho_indice = raiz / "5_indexacao" / "indice_invertido.json"
        
        assert caminho_chunks.exists(), f"Arquivo não encontrado: {caminho_chunks}"
        assert caminho_indice.exists(), f"Arquivo não encontrado: {caminho_indice}"
        
        cls.chunks = json.loads(caminho_chunks.read_text(encoding="utf-8"))["chunks"]
        cls.chunks_map = {c["id_chunk"]: c for c in cls.chunks}
        cls.indice = json.loads(caminho_indice.read_text(encoding="utf-8"))["indice_invertido"]
        cls.stats = buscar_modulo.calcular_estatisticas_corpus(cls.chunks)

    # --------------------------------------------------------------------------
    # 1. Testes de Tokenização e Stopwords
    # --------------------------------------------------------------------------
    def test_tokenizacao_e_deduplicacao_consulta(self):
        """Testa normalização NFC, casefold e descarte de termos repetidos."""
        consulta = "BOLSA bolsa Bolsa critério CRITÉRIO"
        tokens, sw_rem, filtrados, distintos = buscar_modulo.processar_consulta(consulta)
        self.assertEqual(len(tokens), 5)
        self.assertEqual(distintos, ["bolsa", "critério"])

    def test_remocao_stopwords_nltk(self):
        """Verifica se stopwords comuns como 'de', 'para' são removidas via NLTK e registradas."""
        consulta = "critérios para atribuição de bolsas"
        tokens, sw_rem, filtrados, distintos = buscar_modulo.processar_consulta(consulta)
        self.assertIn("de", sw_rem)
        self.assertIn("para", sw_rem)
        self.assertEqual(filtrados, ["critérios", "atribuição", "bolsas"])
        self.assertEqual(distintos, ["critérios", "atribuição", "bolsas"])

    # --------------------------------------------------------------------------
    # 2. Testes Matemáticos do Okapi BM25
    # --------------------------------------------------------------------------
    def test_bm25_idf_formula(self):
        """Valida a fórmula analítica do IDF: ln(1 + (N - DF + 0.5) / (DF + 0.5))."""
        N = 100
        df = 10
        idf_calculado = buscar_modulo.calcular_idf_bm25(N, df)
        idf_esperado = math.log(1.0 + (100 - 10 + 0.5) / (10 + 0.5))
        self.assertAlmostEqual(idf_calculado, idf_esperado, places=6)
        
        # IDF de termo raro deve ser estritamente maior que IDF de termo frequente
        idf_raro = buscar_modulo.calcular_idf_bm25(100, 2)
        idf_frequente = buscar_modulo.calcular_idf_bm25(100, 50)
        self.assertGreater(idf_raro, idf_frequente)
        
        # IDF com valores limites (zero ou negativos) deve retornar 0.0
        self.assertEqual(buscar_modulo.calcular_idf_bm25(0, 5), 0.0)
        self.assertEqual(buscar_modulo.calcular_idf_bm25(100, 0), 0.0)

    def test_bm25_tf_saturacao(self):
        """Verifica que o TF do BM25 satura assintoticamente em (k1 + 1) e não cresce linearmente."""
        k1 = 1.5
        b = 0.75
        avgdl = 200.0
        doc_len = 200

        tf_1 = buscar_modulo.calcular_tf_bm25(1, doc_len, avgdl, k1, b)
        tf_5 = buscar_modulo.calcular_tf_bm25(5, doc_len, avgdl, k1, b)
        tf_50 = buscar_modulo.calcular_tf_bm25(50, doc_len, avgdl, k1, b)
        tf_1000 = buscar_modulo.calcular_tf_bm25(1000, doc_len, avgdl, k1, b)

        # Crescimento sublinear: ganho marginal decrescente
        self.assertGreater(tf_5, tf_1)
        self.assertLess(tf_5 - tf_1, 4 * tf_1)
        
        # Limite assintótico quando freq -> inf é k1 + 1 = 2.5
        self.assertLess(tf_1000, k1 + 1.0)
        self.assertGreater(tf_1000, 2.45)

    def test_bm25_penalizacao_tamanho_documento(self):
        """Para a mesma frequência, documento mais longo deve pontuar menos que documento conciso."""
        k1 = 1.5
        b = 0.75
        avgdl = 200.0
        freq = 3

        tf_curto = buscar_modulo.calcular_tf_bm25(freq, doc_len=100, avgdl=avgdl, k1=k1, b=b)
        tf_medio = buscar_modulo.calcular_tf_bm25(freq, doc_len=200, avgdl=avgdl, k1=k1, b=b)
        tf_longo = buscar_modulo.calcular_tf_bm25(freq, doc_len=400, avgdl=avgdl, k1=k1, b=b)

        self.assertGreater(tf_curto, tf_medio)
        self.assertGreater(tf_medio, tf_longo)

    # --------------------------------------------------------------------------
    # 3. Teste da Pontuação Simples
    # --------------------------------------------------------------------------
    def test_score_simples_formula(self):
        """Verifica que a pontuação simples é exatamente a soma das frequências brutas."""
        freqs = {"bolsa": 3, "critérios": 2}
        score = buscar_modulo.calcular_score_simples(freqs)
        self.assertEqual(score, 5)

    # --------------------------------------------------------------------------
    # 4. Casos de Borda da Busca
    # --------------------------------------------------------------------------
    def test_caso_borda_consulta_vazia(self):
        """Consulta vazia ou pontuação deve retornar 0 candidatos sem erro (BM25 e Simples)."""
        cands_bm25, met_bm25 = buscar_modulo.buscar_linear(self.chunks, "   !!! ???   ", metrica="bm25")
        self.assertEqual(len(cands_bm25), 0)
        self.assertIn("aviso", met_bm25)

        cands_simp, met_simp = buscar_modulo.buscar_linear(self.chunks, "   !!! ???   ", metrica="simples")
        self.assertEqual(len(cands_simp), 0)
        self.assertIn("aviso", met_simp)

    def test_caso_borda_apenas_stopwords(self):
        """Consulta composta exclusivamente por stopwords deve retornar 0 candidatos."""
        cands, met = buscar_modulo.buscar_linear(self.chunks, "de para em com por", metrica="bm25")
        self.assertEqual(len(cands), 0)
        self.assertIn("aviso", met)

    def test_caso_borda_termos_inexistentes(self):
        """Palavras que não existem no corpus devem resultar em 0 candidatos."""
        cands, met = buscar_modulo.buscar_linear(self.chunks, "palavratotalmenteinexistentexyz123", metrica="bm25")
        self.assertEqual(len(cands), 0)
        self.assertEqual(met["total_candidatos"], 0)

    def test_caso_borda_consulta_termos_repetidos(self):
        """Termos repetidos na consulta devem ser deduplicados, mantendo o score idêntico."""
        c_rep, _ = buscar_modulo.buscar_linear(self.chunks, "recursos financeiros recursos recursos", metrica="bm25")
        c_uni, _ = buscar_modulo.buscar_linear(self.chunks, "recursos financeiros", metrica="bm25")
        scores_rep = {c["id_chunk"]: c["score"] for c in c_rep}
        scores_uni = {c["id_chunk"]: c["score"] for c in c_uni}
        self.assertEqual(scores_rep, scores_uni)

    # --------------------------------------------------------------------------
    # 5. Equivalência Rigorosa: Linear vs. Indexada
    # --------------------------------------------------------------------------
    def test_equivalencia_busca_linear_e_indexada_bm25(self):
        """Garante 100% de identidade matemática entre busca linear e indexada sob Okapi BM25."""
        consulta = "critérios para atribuição de bolsas"
        cands_lin, _ = buscar_modulo.buscar_linear(self.chunks, consulta, metrica="bm25", estatisticas_corpus=self.stats)
        cands_idx, _ = buscar_modulo.buscar_indexada(self.indice, self.chunks_map, consulta, metrica="bm25", estatisticas_corpus=self.stats)

        mapa_lin = {c["id_chunk"]: c["score"] for c in cands_lin}
        mapa_idx = {c["id_chunk"]: c["score"] for c in cands_idx}

        self.assertEqual(len(mapa_lin), len(mapa_idx))
        self.assertEqual(mapa_lin, mapa_idx)

    def test_equivalencia_busca_linear_e_indexada_simples(self):
        """Garante 100% de identidade matemática entre busca linear e indexada sob Pontuação Simples."""
        consulta = "normas acadêmicas da pós graduação"
        cands_lin, _ = buscar_modulo.buscar_linear(self.chunks, consulta, metrica="simples")
        cands_idx, _ = buscar_modulo.buscar_indexada(self.indice, self.chunks_map, consulta, metrica="simples")

        mapa_lin = {c["id_chunk"]: c["score"] for c in cands_lin}
        mapa_idx = {c["id_chunk"]: c["score"] for c in cands_idx}

        self.assertEqual(len(mapa_lin), len(mapa_idx))
        self.assertEqual(mapa_lin, mapa_idx)

    # --------------------------------------------------------------------------
    # 6. Estrutura e Metadados dos Candidatos
    # --------------------------------------------------------------------------
    def test_estrutura_candidato_bm25(self):
        """Verifica schema de candidatos sob BM25: score float positivo e campos obrigatórios."""
        cands, met = buscar_modulo.buscar_linear(self.chunks, "critérios bolsas", metrica="bm25")
        self.assertGreater(len(cands), 0)
        cand = cands[0]

        for campo in ["id_chunk", "id_documento", "paginas", "score", "frequencias_termos", "texto"]:
            self.assertIn(campo, cand)
        self.assertIsInstance(cand["paginas"], list)
        self.assertIsInstance(cand["score"], float)
        self.assertEqual(met["metrica_score"], "bm25")
        self.assertIn("k1", met["parametros_metrica"])

    def test_estrutura_candidato_simples(self):
        """Verifica schema de candidatos sob pontuação simples: score int e campos obrigatórios."""
        cands, met = buscar_modulo.buscar_linear(self.chunks, "critérios bolsas", metrica="simples")
        self.assertGreater(len(cands), 0)
        cand = cands[0]

        self.assertIsInstance(cand["score"], int)
        self.assertEqual(met["metrica_score"], "simples")


if __name__ == "__main__":
    unittest.main()
