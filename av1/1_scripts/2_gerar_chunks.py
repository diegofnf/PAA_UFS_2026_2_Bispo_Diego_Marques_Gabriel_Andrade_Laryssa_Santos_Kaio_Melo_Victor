"""Gera chunks de texto a partir dos documentos normalizados para indexação."""

import argparse
import json
import re
import time
from pathlib import Path


def mapear_paginas_documento(paginas):
    """Mapeia o texto contínuo do documento e os intervalos de caracteres de cada página."""
    offsets_paginas = []
    partes_texto = []
    cursor = 0

    for pag in paginas:
        texto = pag.get("texto_normalizado", "").strip()
        if not texto:
            continue
        inicio = cursor
        fim = cursor + len(texto)
        offsets_paginas.append({
            "numero_pagina": pag["numero_pagina"],
            "inicio": inicio,
            "fim": fim,
        })
        partes_texto.append(texto)
        cursor = fim + 2  # Separador "\n\n"

    texto_documento = "\n\n".join(partes_texto)
    return texto_documento, offsets_paginas


def identificar_pagina_por_caractere(pos_caractere, offsets_paginas):
    """Localiza o número da página correspondente a uma posição de caractere no texto contínuo."""
    for item in offsets_paginas:
        if item["inicio"] <= pos_caractere <= item["fim"]:
            return item["numero_pagina"]
    return offsets_paginas[-1]["numero_pagina"] if offsets_paginas else 1


def gerar_chunks_documento(texto_documento, offsets_paginas, tamanho_chunk, overlap):
    """Segmenta o texto de um documento em janelas deslizantes com sobreposição entre páginas."""
    matches = list(re.finditer(r"\S+", texto_documento))
    total_palavras = len(matches)
    if total_palavras == 0:
        return []

    # Mapeia a página correspondente ao início de cada palavra
    palavras_info = [
        (m, identificar_pagina_por_caractere(m.start(), offsets_paginas))
        for m in matches
    ]

    passo = tamanho_chunk - overlap
    chunks = []

    for inicio in range(0, total_palavras, passo):
        fim = min(inicio + tamanho_chunk, total_palavras)
        slice_palavras = palavras_info[inicio:fim]

        paginas_cobertas = sorted(list(set(pag for _, pag in slice_palavras)))
        span_inicio = slice_palavras[0][0].start()
        span_fim = slice_palavras[-1][0].end()
        texto_chunk = texto_documento[span_inicio:span_fim]
        quantidade_palavras = fim - inicio

        chunks.append({
            "inicio_palavra": inicio,
            "fim_palavra": fim,
            "quantidade_palavras": quantidade_palavras,
            "quantidade_caracteres": len(texto_chunk),
            "paginas": paginas_cobertas,
            "texto": texto_chunk,
        })

        if fim == total_palavras:
            break

    return chunks


def processar_documentos(documentos, tamanho_chunk, overlap):
    """Lê documentos normalizados e gera a coleção de chunks contínuos com metadados."""
    todos_chunks = []
    estatisticas_docs = []
    indice_global = 1

    for doc in documentos:
        id_documento = doc["id_documento"]
        nome_arquivo = doc["nome_arquivo"]
        paginas = [p for p in doc.get("paginas", []) if p.get("texto_normalizado", "").strip()]
        texto_doc, offsets_pag = mapear_paginas_documento(paginas)
        chunks_gerados = gerar_chunks_documento(texto_doc, offsets_pag, tamanho_chunk, overlap)

        for ordem_doc, chunk in enumerate(chunks_gerados, start=1):
            registro_chunk = {
                "id_chunk": f"chunk_{indice_global:04d}",
                "id_documento": id_documento,
                "nome_arquivo": nome_arquivo,
                "paginas": chunk["paginas"],
                "ordem_chunk_documento": ordem_doc,
                "ordem_global": indice_global,
                "inicio_palavra": chunk["inicio_palavra"],
                "fim_palavra": chunk["fim_palavra"],
                "quantidade_palavras": chunk["quantidade_palavras"],
                "quantidade_caracteres": chunk["quantidade_caracteres"],
                "texto": chunk["texto"],
            }
            todos_chunks.append(registro_chunk)
            indice_global += 1

        estatisticas_docs.append({
            "id_documento": id_documento,
            "nome_arquivo": nome_arquivo,
            "paginas_com_conteudo": len(paginas),
            "quantidade_chunks": len(chunks_gerados),
            "chunks_com_overlap_entre_paginas": sum(1 for c in chunks_gerados if len(c["paginas"]) > 1),
        })

    return todos_chunks, estatisticas_docs


def salvar(caminho, dados):
    """Grava um artefato estruturado em JSON UTF-8 com o atributo 'paginas' em linha única."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto_json = json.dumps(dados, ensure_ascii=False, indent=2)
    # Compacta o array 'paginas' em linha única para legibilidade e economia de espaço (ex.: [1, 2])
    texto_json = re.sub(
        r'"paginas":\s*\[\s*([^\]]*?)\s*\]',
        lambda m: f'"paginas": [{", ".join(x.strip() for x in m.group(1).split(",") if x.strip())}]',
        texto_json,
    )
    caminho.write_text(texto_json + "\n", encoding="utf-8")


def main():
    """Executa a Etapa 2 — Geração de Chunks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entrada",
        type=Path,
        default=Path("3_dados/documentos_normalizados.json"),
        help="Caminho do arquivo de entrada com os documentos normalizados.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("4_chunks/chunks.json"),
        help="Caminho do arquivo JSON de saída para os chunks.",
    )
    parser.add_argument(
        "--relatorio",
        type=Path,
        default=Path("4_chunks/relatorio_chunking.json"),
        help="Caminho do arquivo JSON com relatório estatístico da geração de chunks.",
    )
    parser.add_argument(
        "--tamanho-chunk",
        type=int,
        default=200,
        help="Tamanho do chunk em número de palavras (padrão: 200).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=30,
        help="Número de palavras de sobreposição entre chunks consecutivos (padrão: 30).",
    )
    args = parser.parse_args()

    if args.tamanho_chunk <= 0:
        raise ValueError("O tamanho do chunk deve ser maior que zero.")
    if args.overlap < 0:
        raise ValueError("O overlap não pode ser negativo.")
    if args.overlap >= args.tamanho_chunk:
        raise ValueError("O overlap deve ser estritamente menor que o tamanho do chunk.")

    if not args.entrada.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {args.entrada}")

    inicio_tempo = time.perf_counter()
    dados_entrada = json.loads(args.entrada.read_text(encoding="utf-8"))
    documentos = dados_entrada.get("documentos", [])
    if not documentos:
        raise ValueError("Nenhum documento encontrado no arquivo de entrada.")

    chunks, estatisticas_docs = processar_documentos(
        documentos=documentos,
        tamanho_chunk=args.tamanho_chunk,
        overlap=args.overlap,
    )

    tempo_total = time.perf_counter() - inicio_tempo

    palavras_por_chunk = [c["quantidade_palavras"] for c in chunks]
    total_cruzou = sum(1 for c in chunks if len(c["paginas"]) > 1)
    relatorio = {
        "status_etapa": "concluido",
        "total_documentos": len(documentos),
        "total_chunks": len(chunks),
        "chunks_com_overlap_entre_paginas": total_cruzou,
        "percentual_chunks_cruzam_paginas": round((total_cruzou / len(chunks)) * 100, 2) if chunks else 0,
        "parametros": {
            "tamanho_chunk_palavras": args.tamanho_chunk,
            "overlap_palavras": args.overlap,
            "passo_palavras": args.tamanho_chunk - args.overlap,
        },
        "estatisticas_palavras": {
            "media": round(sum(palavras_por_chunk) / len(chunks), 2) if chunks else 0,
            "minimo": min(palavras_por_chunk) if chunks else 0,
            "maximo": max(palavras_por_chunk) if chunks else 0,
            "total_palavras_acumuladas": sum(palavras_por_chunk),
        },
        "tempo_execucao_segundos": round(tempo_total, 6),
        "documentos": estatisticas_docs,
    }

    saida_chunks = {
        "metadados": {
            "estrategia": "palavras_com_overlap_documento_continuo",
            "tamanho_chunk_palavras": args.tamanho_chunk,
            "overlap_palavras": args.overlap,
            "passo_palavras": args.tamanho_chunk - args.overlap,
            "total_chunks": len(chunks),
            "chunks_com_overlap_entre_paginas": total_cruzou,
            "total_documentos": len(documentos),
            "tempo_execucao_segundos": round(tempo_total, 6),
        },
        "chunks": chunks,
    }

    salvar(args.saida, saida_chunks)
    salvar(args.relatorio, relatorio)

    # Validações de integridade
    assert len(chunks) > 0, "Nenhum chunk foi gerado."
    assert all(
        "id_documento" in c and "paginas" in c and isinstance(c["paginas"], list) and len(c["paginas"]) > 0
        and "texto" in c and len(c["texto"].strip()) > 0
        for c in chunks
    ), "Todos os chunks devem preservar id_documento, paginas (lista) e texto não vazio."

    print(
        f"Etapa 2 concluída com sucesso: {len(chunks)} chunks gerados a partir de "
        f"{len(documentos)} documentos em {tempo_total:.4f}s."
    )
    print(
        f"Média de palavras por chunk: {relatorio['estatisticas_palavras']['media']} "
        f"(mín: {relatorio['estatisticas_palavras']['minimo']}, máx: {relatorio['estatisticas_palavras']['maximo']})."
    )
    print(
        f"Chunks com overlap entre páginas: {total_cruzou} ({relatorio['percentual_chunks_cruzam_paginas']}%)."
    )
    print(f"Artefatos salvos em: {args.saida} e {args.relatorio}")


if __name__ == "__main__":
    main()
