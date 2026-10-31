"""Testes da Etapa 5 da AV2 — contexto para LLM e orçamento de tokens.

Cobre o núcleo puro (tokenização, deduplicação, orçamento) e a integração com
os artefatos reais da AV2 (`chunks_tokenizados.json`, `selecao_gulosa.json` e
`selecao_pd.json`).
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

import tiktoken


DIRETORIO_SCRIPTS = Path(__file__).resolve().parent
if str(DIRETORIO_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_SCRIPTS))

import montar_contexto_llm as contexto


RAIZ = Path(__file__).resolve().parents[2]
ENC = tiktoken.get_encoding("cl100k_base")
CONSULTA = "critérios para atribuição de bolsas"
TERMOS = ["critérios", "atribuição", "bolsas"]


def criar_chunk(
    id_chunk: str,
    id_documento: str,
    inicio: int,
    texto: str,
    v_i: float = 1.0,
) -> dict:
    """Cria um chunk mínimo no formato de `chunks_tokenizados.json`."""
    return {
        "id_chunk": id_chunk,
        "id_documento": id_documento,
        "nome_arquivo": f"{id_documento}.pdf",
        "paginas": [1],
        "ordem_global": inicio + 1,
        "inicio_palavra": inicio,
        "fim_palavra": inicio + len(texto.split()),
        "quantidade_palavras": len(texto.split()),
        "texto": texto,
        "v_i": v_i,
        "w_i": contexto.contar_tokens(texto, ENC),
    }


def criar_selecao(chunks: list[dict]) -> dict:
    """Cria um cenário de seleção a partir dos chunks canônicos."""
    return {
        "W": sum(chunk["w_i"] for chunk in chunks) + 10,
        "tokens_usados": sum(chunk["w_i"] for chunk in chunks),
        "chunks": [
            {
                "id_chunk": chunk["id_chunk"],
                "ordem_selecao": indice,
                "v_i": chunk["v_i"],
                "w_i": chunk["w_i"],
                "id_documento": chunk["id_documento"],
                "nome_arquivo": chunk["nome_arquivo"],
                "paginas": chunk["paginas"],
                "texto": chunk["texto"],
            }
            for indice, chunk in enumerate(chunks, start=1)
        ],
    }


def montar(
    chunks: list[dict],
    janela: int = 4096,
    estrategia: str = "integral",
    deduplicar: bool = True,
    ordem: str = "relevancia",
    truncar: bool = False,
    **sobrescritas,
) -> contexto.ResultadoCenario:
    """Atalho para montar um cenário sintético."""
    parametros = dict(
        seletor="pd",
        cenario_selecao=criar_selecao(chunks),
        chunks_map={chunk["id_chunk"]: chunk for chunk in chunks},
        consulta=CONSULTA,
        janela=janela,
        estrategia=estrategia,
        deduplicar=deduplicar,
        ordem=ordem,
        encoding=ENC,
        tokens_fixos=contexto.medir_tokens_fixos(CONSULTA, ENC),
        reserva_resposta=128,
        reserva_seguranca=8,
        truncar_ultimo=truncar,
        termos_consulta=TERMOS,
    )
    parametros.update(sobrescritas)
    return contexto.montar_cenario(**parametros)


class TestTokenizacaoEValidacao(unittest.TestCase):
    """Valida `w_i` e o contrato de tokens da AV2."""

    @classmethod
    def setUpClass(cls):
        cls.dados = contexto.carregar_json(contexto.CAMINHO_CHUNKS)
        cls.chunks = cls.dados["chunks"]
        cls.chunks_map = {chunk["id_chunk"]: chunk for chunk in cls.chunks}

    def test_corpus_real_mantem_w_i_exato(self):
        resultado = contexto.verificar_w_i(self.chunks, ENC)
        self.assertEqual(resultado["total_chunks"], 182)
        self.assertEqual(resultado["tokens_individuais_total"], 74055)
        self.assertEqual(resultado["chunks_com_w_i_zero"], 0)

    def test_w_i_divergente_levanta_erro(self):
        chunks = copy.deepcopy(self.chunks[:1])
        chunks[0]["w_i"] += 1
        with self.assertRaises(ValueError):
            contexto.verificar_w_i(chunks, ENC)

    def test_w_i_negativo_levanta_erro(self):
        chunks = copy.deepcopy(self.chunks[:1])
        chunks[0]["w_i"] = -1
        with self.assertRaises(ValueError):
            contexto.verificar_w_i(chunks, ENC)

    def test_encode_ordinary_trata_marcador_como_texto(self):
        texto = "texto <|endoftext|> comum"
        self.assertEqual(
            contexto.contar_tokens(texto, ENC),
            len(ENC.encode_ordinary(texto)),
        )


class TestOrcamentoEDeduplicacao(unittest.TestCase):
    """Valida a equação de orçamento e os recortes de sobreposição."""

    def test_orcamento_desconta_fixos_resposta_e_seguranca(self):
        orcamento = contexto.calcular_orcamento_llm(8192, 190, 512, 64)
        self.assertEqual(orcamento.orcamento_contexto, 7426)

    def test_orcamento_negativo_e_permitido_para_analise(self):
        orcamento = contexto.calcular_orcamento_llm(512, 190, 512, 64)
        self.assertLess(orcamento.orcamento_contexto, 0)

    def test_reservas_negativas_levantam_erro(self):
        with self.assertRaises(ValueError):
            contexto.calcular_orcamento_llm(8192, 190, -1, 64)

    def test_remove_sobreposicao_no_inicio(self):
        texto_b = "i j k l m n o p q r"
        texto, segmentos, removidas = contexto.recortar_sobreposicao(
            texto_b, 8, 18, [(0, 10)]
        )
        self.assertEqual(texto, "k l m n o p q r")
        self.assertEqual(removidas, 2)
        self.assertEqual([segmento[1] for segmento in segmentos], [(10, 18)])

    def test_sobreposicao_no_fim_preserva_inicio(self):
        texto, segmentos, removidas = contexto.recortar_sobreposicao(
            "a b c d e f g h i j", 0, 10, [(8, 18)]
        )
        self.assertEqual(texto, "a b c d e f g h")
        self.assertEqual(removidas, 2)
        self.assertEqual([segmento[1] for segmento in segmentos], [(0, 8)])

    def test_limitar_segmentos_registra_intervalo_real(self):
        segmentos = [("a b c d", (10, 14), 4), ("e f g", (20, 23), 3)]
        texto, intervalos = contexto.limitar_segmentos(segmentos, 6)
        self.assertEqual(texto, "a b c d\ne f […]")
        self.assertEqual(intervalos, [(10, 14), (20, 22)])


class TestPontoDeEntradaOficial(unittest.TestCase):
    """Garante que o arquivo proposto pela atividade delega para a implementação."""

    def test_integrar_contexto_expoe_main(self):
        caminho = RAIZ / "av2" / "integrar_contexto.py"
        self.assertTrue(caminho.is_file())
        especificacao = importlib.util.spec_from_file_location(
            "integrar_contexto_teste", caminho
        )
        modulo = importlib.util.module_from_spec(especificacao)
        sys.modules[especificacao.name] = modulo
        especificacao.loader.exec_module(modulo)
        implementacao = modulo._carregar_implementacao()
        self.assertTrue(callable(implementacao.main))


class TestMedicaoELatencia(unittest.TestCase):
    """Valida o harness de tempo/memória e a estimativa de latência."""

    def test_latencia_soma_prefill_e_decode(self):
        latencia = contexto.estimar_latencia(2000, 500, 1000.0, 50.0)
        self.assertAlmostEqual(latencia["latencia_prefill_s"], 2.0)
        self.assertAlmostEqual(latencia["latencia_decode_s"], 10.0)
        self.assertAlmostEqual(latencia["latencia_total_s"], 12.0)

    def test_taxas_invalidas_levantam_erro(self):
        with self.assertRaises(ValueError):
            contexto.estimar_latencia(100, 100, 0, 50)
        with self.assertRaises(ValueError):
            contexto.estimar_latencia(100, 100, 1000, 0)

    def test_medir_operacao_devolve_resultado_tempo_e_memoria(self):
        resultado, tempo_ms, pico = contexto.medir_operacao(
            lambda: [0] * 10000, 3
        )
        self.assertEqual(len(resultado), 10000)
        self.assertGreaterEqual(tempo_ms, 0.0)
        self.assertGreater(pico, 0)


class TestMontagemSintetica(unittest.TestCase):
    """Valida prompt, ordem, truncamento e determinismo sem depender do corpus."""

    def test_prompt_integral_tem_fontes_e_pergunta(self):
        chunks = [
            criar_chunk("c1", "d1", 0, "critérios de bolsas e matrícula", 5.0),
            criar_chunk("c2", "d1", 10, "atribuição de bolsas do programa", 4.0),
        ]
        resultado = montar(chunks, janela=4096, estrategia="integral")
        prompt = resultado.mensagens[1]["content"]
        self.assertIn("[F1]", prompt)
        self.assertIn("[F2]", prompt)
        self.assertIn(CONSULTA, prompt)
        self.assertIn("Não há evidência suficiente", contexto.INSTRUCOES_SISTEMA)
        self.assertFalse(resultado.estourou_janela)
        self.assertGreater(resultado.tokens_prompt, resultado.tokens_textos_incluidos)

    def test_ordem_relevancia_coloca_maior_v_i_primeiro(self):
        chunks = [
            criar_chunk("c1", "d1", 0, "texto de menor relevância", 1.0),
            criar_chunk("c2", "d2", 0, "texto de maior relevância", 9.0),
        ]
        resultado = montar(chunks, janela=4096, estrategia="integral")
        self.assertEqual(resultado.blocos[0].id_chunk, "c2")
        self.assertEqual(resultado.blocos[0].rotulo, "F1")

    def test_ajustado_respeita_janela_e_descarta(self):
        chunks = [
            criar_chunk("c1", "d1", 0, "palavra " * 150, 9.0),
            criar_chunk("c2", "d1", 150, "termo " * 150, 8.0),
        ]
        resultado = montar(chunks, janela=700, estrategia="ajustado")
        self.assertFalse(resultado.estourou_janela)
        self.assertGreaterEqual(resultado.folga_llm, 0)
        self.assertLess(len(resultado.blocos), len(chunks))
        self.assertGreater(resultado.chunks_descartados, 0)

    def test_ajustado_sem_chunk_que_cabe_gera_contexto_vazio(self):
        chunks = [criar_chunk("c1", "d1", 0, "palavra " * 300, 9.0)]
        resultado = montar(chunks, janela=500, estrategia="ajustado")
        self.assertEqual(resultado.blocos, [])
        self.assertFalse(resultado.estourou_janela)
        self.assertIn("Não há evidência suficiente", contexto.INSTRUCOES_SISTEMA)
        self.assertEqual(resultado.metricas["cobertura_termos"], 0.0)

    def test_integral_pode_estourar_janela(self):
        chunks = [criar_chunk("c1", "d1", 0, "palavra " * 300, 9.0)]
        resultado = montar(chunks, janela=500, estrategia="integral")
        self.assertTrue(resultado.estourou_janela)
        self.assertLess(resultado.folga_llm, 0)

    def test_truncamento_preenche_orcamento(self):
        chunks = [criar_chunk("c1", "d1", 0, "palavra " * 300, 9.0)]
        resultado = montar(
            chunks, janela=550, estrategia="ajustado", truncar=True
        )
        self.assertFalse(resultado.estourou_janela)
        self.assertEqual(len(resultado.blocos), 1)
        self.assertTrue(resultado.blocos[0].truncado)
        self.assertTrue(resultado.blocos[0].texto.endswith("[…]"))

    def test_deduplicacao_reduz_tokens(self):
        texto1 = "palavra " * 100
        texto2 = "palavra " * 30 + "termo " * 70
        chunks = [
            criar_chunk("c1", "d1", 0, texto1, 9.0),
            criar_chunk("c2", "d1", 70, texto2, 8.0),
        ]
        com = montar(chunks, janela=8192, estrategia="integral", deduplicar=True)
        sem = montar(chunks, janela=8192, estrategia="integral", deduplicar=False)
        self.assertGreater(com.economia_dedupe, 0)
        self.assertLessEqual(com.tokens_textos_incluidos, sem.tokens_textos_incluidos)
        self.assertGreater(com.palavras_removidas_sobreposicao, 0)

    def test_montagem_deterministica(self):
        chunks = [
            criar_chunk("c1", "d1", 0, "critérios de bolsas", 9.0),
            criar_chunk("c2", "d1", 10, "atribuição de bolsas", 8.0),
        ]
        primeiro = montar(chunks, janela=4096)
        segundo = montar(chunks, janela=4096)
        self.assertEqual(primeiro.mensagens, segundo.mensagens)
        self.assertEqual(primeiro.tokens_prompt, segundo.tokens_prompt)

    def test_estrategia_invalida_levanta_erro(self):
        chunks = [criar_chunk("c1", "d1", 0, "texto", 1.0)]
        with self.assertRaises(ValueError):
            montar(chunks, estrategia="invalida")

    def test_ordem_invalida_levanta_erro(self):
        chunks = [criar_chunk("c1", "d1", 0, "texto", 1.0)]
        with self.assertRaises(ValueError):
            montar(chunks, ordem="invalida")

    def test_empate_de_relevancia_usa_id_chunk(self):
        chunks = [
            criar_chunk("c2", "d1", 0, "texto do segundo", 5.0),
            criar_chunk("c1", "d2", 0, "texto do primeiro", 5.0),
        ]
        resultado = montar(chunks, janela=4096, estrategia="integral")
        self.assertEqual([bloco.id_chunk for bloco in resultado.blocos], ["c1", "c2"])

    def test_entrada_grande_respeita_orcamento(self):
        chunks = [
            criar_chunk(f"c{indice:03d}", "d1", indice * 5, "palavra " * 5, 1.0)
            for indice in range(60)
        ]
        resultado = montar(chunks, janela=1200, estrategia="ajustado")
        self.assertFalse(resultado.estourou_janela)
        self.assertGreaterEqual(resultado.folga_llm, 0)
        self.assertLessEqual(
            resultado.tokens_contexto,
            resultado.orcamento.orcamento_contexto,
        )
        self.assertGreater(resultado.chunks_descartados, 0)

    def test_caractere_de_controle_e_preservado(self):
        texto = "identi\x00ficadas no texto"
        chunk = criar_chunk("c1", "d1", 0, texto, 9.0)
        resultado = montar([chunk], janela=4096, estrategia="integral")
        self.assertIn("\x00", resultado.blocos[0].texto)
        self.assertEqual(
            resultado.blocos[0].tokens_texto,
            contexto.contar_tokens(texto, ENC),
        )


class TestIntegracaoAV2(unittest.TestCase):
    """Integra com as seleções reais e os quatro orçamentos da AV2."""

    @classmethod
    def setUpClass(cls):
        cls.chunks = contexto.carregar_json(contexto.CAMINHO_CHUNKS)["chunks"]
        cls.chunks_map = {chunk["id_chunk"]: chunk for chunk in cls.chunks}
        cls.instancias = contexto.carregar_json(contexto.CAMINHO_INSTANCIAS)
        cls.selecoes = {
            "guloso": contexto.carregar_json(contexto.CAMINHOS_SELECAO["guloso"]),
            "pd": contexto.carregar_json(contexto.CAMINHOS_SELECAO["pd"]),
        }
        cls.consulta = cls.instancias["metadados"]["consulta"]
        cls.tokens_fixos = contexto.medir_tokens_fixos(cls.consulta, ENC)
        cls.termos = contexto.carregar_termos_consulta(cls.consulta)

    def montar_real(self, seletor: str, W: int, janela: int, **sobrescritas):
        parametros = dict(
            seletor=seletor,
            cenario_selecao=self.selecoes[seletor]["cenarios"][f"W_{W}"],
            chunks_map=self.chunks_map,
            consulta=self.consulta,
            janela=janela,
            estrategia="integral",
            deduplicar=True,
            ordem="relevancia",
            encoding=ENC,
            tokens_fixos=self.tokens_fixos,
            reserva_resposta=512,
            reserva_seguranca=64,
            truncar_ultimo=False,
            termos_consulta=self.termos,
        )
        parametros.update(sobrescritas)
        return contexto.montar_cenario(**parametros)

    def test_w4096_pd_integral_em_8192_cabe(self):
        resultado = self.montar_real("pd", 4096, 8192)
        self.assertEqual(resultado.chunks_selecionados, 11)
        self.assertEqual(resultado.tokens_w_i_selecionados, 4093)
        self.assertGreater(resultado.tokens_prompt, resultado.tokens_w_i_selecionados)
        self.assertFalse(resultado.estourou_janela)
        self.assertGreaterEqual(resultado.folga_llm, 0)
        self.assertEqual(resultado.metricas["cobertura_termos"], 1.0)

    def test_w4096_pd_ajustado_em_4096_descarta_e_cabe(self):
        resultado = self.montar_real(
            "pd", 4096, 4096, estrategia="ajustado", truncar_ultimo=True
        )
        self.assertFalse(resultado.estourou_janela)
        self.assertGreaterEqual(resultado.folga_llm, 0)
        self.assertLess(len(resultado.blocos), 11)
        self.assertLess(resultado.relevancia_incluida, 60.3138)

    def test_w512_ajustado_em_1024_nao_cabe_nem_um_chunk(self):
        resultado = self.montar_real("guloso", 512, 1024, estrategia="ajustado")
        self.assertEqual(resultado.blocos, [])
        self.assertFalse(resultado.estourou_janela)
        self.assertEqual(resultado.metricas["cobertura_termos"], 0.0)

    def test_pd_supera_guloso_em_w4096(self):
        pd = self.montar_real("pd", 4096, 8192)
        guloso = self.montar_real("guloso", 4096, 8192)
        self.assertGreater(pd.relevancia_incluida, guloso.relevancia_incluida)
        self.assertGreater(pd.tokens_prompt, guloso.tokens_prompt)

    def test_pd_nao_supera_guloso_em_w2048(self):
        """Teste que pode refutar a hipótese de que a PD sempre melhora o contexto."""
        pd = self.montar_real("pd", 2048, 8192)
        guloso = self.montar_real("guloso", 2048, 8192)
        self.assertAlmostEqual(pd.relevancia_incluida, guloso.relevancia_incluida, 4)
        self.assertEqual(pd.tokens_prompt, guloso.tokens_prompt)

    def test_dedupe_real_economiza_tokens_em_w4096(self):
        com = self.montar_real("pd", 4096, 8192, deduplicar=True)
        sem = self.montar_real("pd", 4096, 8192, deduplicar=False)
        self.assertGreater(com.economia_dedupe, 0)
        self.assertLessEqual(com.tokens_textos_incluidos, sem.tokens_textos_incluidos)
        self.assertGreater(com.palavras_removidas_sobreposicao, 0)

    def test_exportar_contextos_tem_oito_cenarios(self):
        exportado = contexto.exportar_contextos(
            selecoes=self.selecoes,
            chunks_map=self.chunks_map,
            consulta=self.consulta,
            encoding=ENC,
            tokens_fixos=self.tokens_fixos,
            janela=8192,
            estrategia="ajustado",
            deduplicar=True,
            ordem="relevancia",
            reserva_resposta=512,
            reserva_seguranca=64,
            truncar_ultimo=False,
            termos_consulta=self.termos,
            modelo="gpt-4-turbo",
        )
        self.assertEqual(len(exportado["cenarios"]), 8)
        for cenario in exportado["cenarios"].values():
            self.assertEqual(len(cenario["mensagens"]), 2)
            self.assertEqual(cenario["uso_sugerido"]["model"], "gpt-4-turbo")
            self.assertEqual(cenario["uso_sugerido"]["temperature"], 0.0)
            self.assertIn("fontes", cenario)
            self.assertEqual(
                len(cenario["fontes"]),
                cenario["metricas"]["chunks_incluidos"],
            )
            for fonte in cenario["fontes"]:
                self.assertIn("rotulo", fonte)
                self.assertIn("id_chunk", fonte)
                self.assertNotIn("texto", fonte)


if __name__ == "__main__":
    unittest.main()
