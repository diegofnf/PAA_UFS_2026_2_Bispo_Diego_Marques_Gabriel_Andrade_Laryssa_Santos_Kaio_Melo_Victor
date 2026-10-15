"""AV2, etapa 1: associa tokens e scores da AV1 e prepara a mochila 0/1."""

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import tiktoken


RAIZ = Path(__file__).resolve().parents[1]
ORCAMENTOS = (512, 1024, 2048, 4096)


def validar_registros(registros, nome):
    """Rejeita IDs ausentes/duplicados antes da associação por chave."""
    if not isinstance(registros, list):
        raise ValueError(f"{nome} deve ser uma lista.")
    mapa = {}
    for item in registros:
        if not isinstance(item, dict):
            raise ValueError(f"Registro inválido em {nome}.")
        cid = item.get("id_chunk")
        if not isinstance(cid, str) or not cid.strip() or cid in mapa:
            raise ValueError(f"id_chunk ausente ou duplicado em {nome}: {cid!r}")
        mapa[cid] = item
    return mapa


def associar_scores(chunks, candidatos):
    """Valida o corpus e associa os scores, sem executar a tokenização."""
    chunks_map = validar_registros(chunks, "chunks")
    candidatos_map = validar_registros(candidatos, "candidatos")
    for cid, candidato in candidatos_map.items():
        if cid not in chunks_map:
            raise ValueError(f"Candidato referencia chunk inexistente: {cid}")
        original = chunks_map[cid]
        for campo in ("texto", "id_documento", "nome_arquivo", "paginas"):
            if candidato.get(campo) != original.get(campo):
                raise ValueError(f"Candidato desatualizado: {cid}, campo {campo}.")
        score = candidato.get("score")
        if (isinstance(score, bool) or not isinstance(score, (int, float))
                or not math.isfinite(score) or score < 0):
            raise ValueError(f"Score deve ser numérico, finito e não negativo: {cid}")

    preparados = []
    for chunk in chunks:
        cid = chunk["id_chunk"]
        texto = chunk.get("texto")
        if not isinstance(texto, str):
            raise ValueError(f"Texto deve ser uma string: {cid}")
        if (not isinstance(chunk.get("id_documento"), str)
                or not chunk["id_documento"].strip()
                or not isinstance(chunk.get("nome_arquivo"), str)
                or not chunk["nome_arquivo"].strip()
                or not isinstance(chunk.get("paginas"), list)
                or not chunk["paginas"]
                or any(type(p) is not int or p <= 0 for p in chunk["paginas"])):
            raise ValueError(f"Origem documental inválida: {cid}")
        valor = candidatos_map.get(cid, {}).get("score", 0)
        preparados.append({**chunk, "v_i": valor})
    return preparados


def tokenizar_itens(itens, encoding):
    """Conta tokens do texto preservado e registra w_i em cópias dos itens."""
    preparados = []
    for item in itens:
        # Marcadores como <|endoftext|> pertencem ao corpus, não são comandos.
        custo = len(encoding.encode_ordinary(item["texto"]))
        if custo == 0 and item["v_i"] > 0:
            raise ValueError(f"Chunk vazio não pode ter relevância positiva: {item['id_chunk']}")
        preparados.append({**item, "w_i": custo})
    return preparados


def criar_instancias(preparados, orcamentos):
    """Mantém todos os candidatos positivos, inclusive itens maiores que W."""
    if (not orcamentos or len(set(orcamentos)) != len(orcamentos)
            or any(type(w) is not int or w < 0 for w in orcamentos)):
        raise ValueError("Orçamentos devem ser inteiros não negativos e distintos.")
    itens = [c for c in preparados if c["v_i"] > 0 and c["w_i"] > 0]
    instancias = []
    for w in orcamentos:
        instancias.append({
            "id_instancia": f"W_{w}",
            "W": w,
            "ids_itens": [c["id_chunk"] for c in itens],
            "total_itens": len(itens),
            "total_itens_acima_W": sum(c["w_i"] > w for c in itens),
        })
    return {"itens": itens, "instancias": instancias}


def ler_entrada(caminho, chave):
    conteudo = caminho.read_bytes()
    dados = json.loads(conteudo)
    if not isinstance(dados, dict) or chave not in dados:
        raise ValueError(f"Entrada deve conter a chave {chave}: {caminho}")
    if not isinstance(dados.get("metadados"), dict):
        raise ValueError(f"Metadados ausentes ou inválidos: {caminho}")
    if not isinstance(dados[chave], list):
        raise ValueError(f"{chave} deve ser uma lista: {caminho}")
    return dados, hashlib.sha256(conteudo).hexdigest()


def git(*args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(RAIZ), *args], text=True, encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def salvar_json(caminho, dados):
    texto = json.dumps(dados, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    caminho.write_text(texto, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=RAIZ / "av1/4_chunks/chunks.json")
    parser.add_argument("--candidatos", type=Path,
                        default=RAIZ / "av1/6_busca_lexical/candidatos_busca.json")
    parser.add_argument("--encoding", default="cl100k_base")
    parser.add_argument("--orcamentos", type=int, nargs="+", default=list(ORCAMENTOS))
    parser.add_argument("--saida", type=Path, default=RAIZ / "av2/dados")
    args = parser.parse_args(argv)
    inicio = time.perf_counter()
    dados_chunks, hash_chunks = ler_entrada(args.chunks, "chunks")
    dados_candidatos, hash_candidatos = ler_entrada(args.candidatos, "candidatos")
    tempo_leitura = time.perf_counter() - inicio
    meta_busca = dados_candidatos["metadados"]
    consulta = meta_busca.get("consulta")
    if not isinstance(consulta, str) or meta_busca.get("metrica_score") not in ("bm25", "simples"):
        raise ValueError("Candidatos devem registrar consulta e metrica_score da AV1.")
    if meta_busca.get("total_candidatos") != len(dados_candidatos["candidatos"]):
        raise ValueError("total_candidatos não confere; use a busca completa, não Top-k.")
    total_chunks = len(dados_chunks["chunks"])
    n_corpus = dados_chunks["metadados"].get("total_chunks", total_chunks)
    n_busca = meta_busca.get("parametros_metrica", {}).get("total_documentos_N", total_chunks)
    if n_corpus != total_chunks or n_busca != total_chunks:
        raise ValueError("Tamanho do corpus diverge dos metadados da AV1; regenere a busca.")

    t0 = time.perf_counter()
    associados = associar_scores(dados_chunks["chunks"], dados_candidatos["candidatos"])
    tempo_associacao = time.perf_counter() - t0
    t0 = time.perf_counter()
    encoding = tiktoken.get_encoding(args.encoding)
    tempo_tokenizer = time.perf_counter() - t0
    t0 = time.perf_counter()
    preparados = tokenizar_itens(associados, encoding)
    tempo_tokenizacao = time.perf_counter() - t0
    t0 = time.perf_counter()
    instancias = criar_instancias(preparados, args.orcamentos)
    tempo_instancias = time.perf_counter() - t0
    arquivos_saida = [args.saida / nome for nome in (
        "chunks_tokenizados.json", "instancias.json", "relatorio_preparacao.json")]
    entradas = {args.chunks.resolve(), args.candidatos.resolve()}
    if entradas.intersection(p.resolve() for p in arquivos_saida):
        raise ValueError("A saída não pode sobrescrever os arquivos de entrada.")

    status_git = git("status", "--porcelain")
    metadados = {
        "etapa": "av2_1_ingestao_tokenizacao",
        "versao_schema": 1,
        "consulta": consulta,
        "metrica_score": meta_busca["metrica_score"],
        "parametros_metrica": meta_busca.get("parametros_metrica", {}),
        "tokenizer": {"biblioteca": "tiktoken", "versao": version("tiktoken"),
                      "encoding": encoding.name, "metodo": "encode_ordinary",
                      "modelo_llm": None},
        "orcamento": "soma dos tokens individuais dos textos dos chunks; exclui overhead do prompt",
        "politica_candidatos": "todos com score positivo; sem truncamento Top-k; ordem do corpus",
        "entradas": {
            "chunks": {"arquivo": args.chunks.name, "sha256": hash_chunks},
            "candidatos": {"arquivo": args.candidatos.name, "sha256": hash_candidatos},
        },
        "versionamento": {
            "commit_execucao": git("rev-parse", "HEAD"),
            "tag_av1_commit": git("rev-parse", "av1-entrega^{}"),
            "arvore_suja_antes_gravar": None if status_git is None else bool(status_git),
            "sha256_preparador": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    instancias = {"metadados": metadados, **instancias}
    custos = [c["w_i"] for c in preparados]
    relatorio = {
        "metadados": metadados,
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "ambiente": {"python": platform.python_version(), "sistema": platform.platform(),
                     "maquina": platform.machine(), "processador": platform.processor()},
        "comando_argv": sys.argv if argv is None else ["preparar_instancias.py", *argv],
        "total_chunks": len(preparados),
        "total_documentos": len({c["id_documento"] for c in preparados}),
        "total_candidatos_positivos": len(instancias["itens"]),
        "total_chunks_vazios": sum(c["w_i"] == 0 for c in preparados),
        "tokens": {"total": sum(custos), "minimo": min(custos, default=0),
                   "maximo": max(custos, default=0)},
        "instancias": [{k: v for k, v in i.items() if k != "ids_itens"}
                       for i in instancias["instancias"]],
        "tempos_segundos": {
            "leitura_entradas_io": tempo_leitura,
            "validacao_associacao_ram": tempo_associacao,
            "carregamento_tokenizer": tempo_tokenizer,
            "tokenizacao_ram": tempo_tokenizacao,
            "montagem_instancias_ram": tempo_instancias,
        },
    }
    args.saida.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    salvar_json(arquivos_saida[0], {"metadados": metadados, "chunks": preparados})
    salvar_json(arquivos_saida[1], instancias)
    relatorio["tempos_segundos"]["serializacao_gravacao_dados_io"] = time.perf_counter() - t0
    relatorio["tempos_segundos"]["total_antes_gravar_relatorio"] = time.perf_counter() - inicio
    salvar_json(arquivos_saida[2], relatorio)
    print(f"AV2: {len(preparados)} chunks; {len(instancias['itens'])} candidatos positivos; "
          f"W={args.orcamentos}; tokenizer={encoding.name}.")
    print(f"Saída: {args.saida}")


if __name__ == "__main__":
    main()
