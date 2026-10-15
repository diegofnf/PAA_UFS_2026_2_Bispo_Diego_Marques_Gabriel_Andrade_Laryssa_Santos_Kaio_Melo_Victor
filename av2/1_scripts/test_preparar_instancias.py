"""Testes da preparação; não substituem os testes futuros da seleção PD/gulosa."""

import copy
import json
from pathlib import Path

import pytest
import tiktoken

from preparar_instancias import ORCAMENTOS, associar_scores, criar_instancias, main, tokenizar_itens


def preparar_itens(chunks, candidatos, encoding):
    return tokenizar_itens(associar_scores(chunks, candidatos), encoding)


@pytest.fixture(scope="module")
def encoding():
    return tiktoken.get_encoding("cl100k_base")


def chunk(cid="c1", texto="hello world"):
    return {"id_chunk": cid, "id_documento": "doc_001", "nome_arquivo": "norma.pdf",
            "paginas": [1, 2], "texto": texto}


def candidato(original, score=2.5):
    return {**original, "score": score}


def test_normal_tokens_exatos_score_e_origem_sem_mutacao(encoding):
    original = chunk()
    copia = copy.deepcopy(original)
    itens = preparar_itens([original], [candidato(original)], encoding)
    assert encoding.encode_ordinary("hello world") == [15339, 1917]
    assert itens == [{**original, "w_i": 2, "v_i": 2.5}]
    assert original == copia
    assert [i["W"] for i in criar_instancias(itens, ORCAMENTOS)["instancias"]] == list(ORCAMENTOS)


def test_corpus_vazio(encoding):
    assert preparar_itens([], [], encoding) == []
    d = criar_instancias([], ORCAMENTOS)
    assert d["itens"] == []
    assert all(i["total_itens"] == 0 for i in d["instancias"])


def test_sem_correspondencia_e_chunk_vazio(encoding):
    preparados = preparar_itens([chunk(), chunk("vazio", "")], [], encoding)
    assert [c["v_i"] for c in preparados] == [0, 0]
    assert preparados[1]["w_i"] == 0
    assert criar_instancias(preparados, [512])["itens"] == []


def test_fronteira_zero_igual_e_item_maior_que_orcamento(encoding):
    c = chunk()
    preparados = preparar_itens([c], [candidato(c)], encoding)
    d = criar_instancias(preparados, [0, 1, 2])
    assert [i["total_itens_acima_W"] for i in d["instancias"]] == [1, 1, 0]
    assert all(i["ids_itens"] == ["c1"] for i in d["instancias"])


def test_empate_e_texto_duplicado_preservam_ids_distintos(encoding):
    chunks = [chunk("b"), chunk("a")]
    preparados = preparar_itens(chunks, [candidato(c) for c in reversed(chunks)], encoding)
    assert [c["id_chunk"] for c in preparados] == ["b", "a"]
    assert [c["v_i"] for c in preparados] == [2.5, 2.5]


def test_entrada_grande_unicode_e_marcador_especial(encoding):
    texto = "Matrícula, bolsa e defesa. <|endoftext|> 🧪\n" * 3000
    c = chunk(texto=texto)
    preparado = preparar_itens([c], [candidato(c)], encoding)[0]
    assert encoding.decode(encoding.encode_ordinary(texto)) == texto
    assert preparado["texto"] == texto
    assert preparado["w_i"] == len(encoding.encode_ordinary(texto)) > 4096


@pytest.mark.parametrize("onde", ["chunks", "candidatos"])
def test_rejeita_id_duplicado(encoding, onde):
    c = chunk()
    chunks = [c, c] if onde == "chunks" else [c]
    candidatos = [candidato(c), candidato(c)] if onde == "candidatos" else []
    with pytest.raises(ValueError, match="duplicado"):
        preparar_itens(chunks, candidatos, encoding)


@pytest.mark.parametrize("campo,valor", [
    ("id_chunk", "inexistente"), ("texto", "outra versão"),
    ("id_documento", "doc_errado"), ("paginas", [3]), ("nome_arquivo", "outro.pdf"),
])
def test_rejeita_candidato_desatualizado(encoding, campo, valor):
    c = chunk()
    with pytest.raises(ValueError, match="inexistente|desatualizado"):
        preparar_itens([c], [{**candidato(c), campo: valor}], encoding)


@pytest.mark.parametrize("score", [-1, float("nan"), float("inf"), True, "3", None])
def test_rejeita_score_invalido(encoding, score):
    c = chunk()
    with pytest.raises(ValueError, match="Score"):
        preparar_itens([c], [candidato(c, score)], encoding)


def test_rejeita_chunk_vazio_com_score_positivo(encoding):
    c = chunk(texto="")
    with pytest.raises(ValueError, match="vazio"):
        preparar_itens([c], [candidato(c)], encoding)


@pytest.mark.parametrize("orcamentos", [[], [-1], [512, 512], [True], [1.5]])
def test_rejeita_orcamento_invalido(orcamentos):
    with pytest.raises(ValueError, match="Orçamentos"):
        criar_instancias([], orcamentos)


@pytest.mark.parametrize("campo,valor", [("texto", None), ("paginas", []),
                                        ("id_documento", ""), ("id_chunk", "")])
def test_rejeita_chunk_malformado(encoding, campo, valor):
    with pytest.raises(ValueError):
        preparar_itens([{**chunk(), campo: valor}], [], encoding)


def test_cli_real_gera_quatro_instancias_preservando_entradas(tmp_path):
    raiz = Path(__file__).resolve().parents[2]
    chunks_path = raiz / "av1/4_chunks/chunks.json"
    candidatos_path = raiz / "av1/6_busca_lexical/candidatos_busca.json"
    antes = [p.read_bytes() for p in (chunks_path, candidatos_path)]
    main(["--saida", str(tmp_path)])
    instancias = json.loads((tmp_path / "3_instancias/instancias.json").read_text(encoding="utf-8"))
    chunks = json.loads((tmp_path / "2_dados_tokenizados/chunks_tokenizados.json").read_text(encoding="utf-8"))
    scores = {c["id_chunk"]: c["score"] for c in json.loads(antes[1])["candidatos"]}
    assert len(chunks["chunks"]) == 182
    assert len(instancias["itens"]) == 75
    assert {c["id_chunk"]: c["v_i"] for c in instancias["itens"]} == scores
    assert [i["W"] for i in instancias["instancias"]] == list(ORCAMENTOS)
    assert instancias["metadados"]["tokenizer"]["encoding"] == "cl100k_base"
    relatorio = json.loads((tmp_path / "5_resultados/relatorio_preparacao.json").read_text(encoding="utf-8"))
    tempos = relatorio["tempos_segundos"]
    assert tempos["tokenizacao_ram"] >= 0
    assert tempos["validacao_associacao_ram"] >= 0
    assert antes == [p.read_bytes() for p in (chunks_path, candidatos_path)]


def test_cli_rejeita_topk_sem_metadados_da_busca(tmp_path):
    p = tmp_path / "topk.json"
    p.write_text(json.dumps({"metadados": {}, "candidatos": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="consulta"):
        main(["--candidatos", str(p), "--saida", str(tmp_path / "saida")])
    assert not (tmp_path / "saida").exists()


def test_associacao_independe_do_tokenizer():
    c = chunk()
    assert associar_scores([c], [candidato(c)]) == [{**c, "v_i": 2.5}]
    assert "w_i" not in c


@pytest.mark.parametrize("metadados_corpus", [True, False])
def test_cli_rejeita_tamanho_de_corpus_incompativel(tmp_path, metadados_corpus):
    raiz = Path(__file__).resolve().parents[2]
    c = json.loads((raiz / "av1/4_chunks/chunks.json").read_text(encoding="utf-8"))
    busca = json.loads((raiz / "av1/6_busca_lexical/candidatos_busca.json").read_text(encoding="utf-8"))
    if metadados_corpus:
        c["metadados"]["total_chunks"] += 1
    else:
        busca["metadados"]["parametros_metrica"]["total_documentos_N"] += 1
    p_chunks, p_busca = tmp_path / "chunks.json", tmp_path / "busca.json"
    p_chunks.write_text(json.dumps(c), encoding="utf-8")
    p_busca.write_text(json.dumps(busca), encoding="utf-8")
    with pytest.raises(ValueError, match="Tamanho do corpus"):
        main(["--chunks", str(p_chunks), "--candidatos", str(p_busca),
              "--saida", str(tmp_path / "saida")])
    assert not (tmp_path / "saida").exists()
