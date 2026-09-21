"""Etapa 5 — Bateria Experimental, Métricas de Desempenho e Avaliação Empírica.

Este script implementa:
1. Projeto e Execução da Matriz Experimental Mínima (Seção 7.2 do Edital):
   - Execução controlada de 12 baterias de teste mensuráveis;
   - Cobertura das 3 configurações algorítmicas obrigatórias:
     a) Configuração 1 (Baseline): Busca linear sequencial, sem índice;
     b) Configuração 2 (Indexada): Recuperação por postings lists do índice invertido;
     c) Configuração 3 (Divisão e Conquista): busca indexada seguida de Merge Sort
        com seleção de Top-k, isolando o custo da ordenação;
   - Avaliação sobre 2 cargas de teste (corpus integral e corpus reduzido);
   - Execução em duplicata (2 repetições por cenário) para cálculo de média e dispersão.

2. Coleta Sistemática de Métricas de Desempenho (Seção 7.3 do Edital):
   - Cronometragem in-process do trecho algoritmicamente relevante via
     time.perf_counter(), imediatamente ao redor da(s) função(ões) em avaliação;
   - Aferição de pico de consumo de memória RAM dinâmica via tracemalloc;
   - Registro de parâmetros ambientais de reprodutibilidade (S.O., arquitetura e interpretador);
   - Contabilização de falhas por execução (exceções capturadas e registradas no campo
     'status' de cada bateria); a taxa de falhas, a taxa de resultados vazios e o
     comportamento em consultas nulas ou fora do vocabulário são medidos na Etapa 8
     ('8_avaliar_robustez.py');
   - Persistência estruturada das evidências em '7_resultados/relatorio_experimentos.json'.

Nota de metodologia: a cronometragem é feita in-process, e não por subprocesso. Medir o
processo inteiro incluiria o custo fixo de inicialização do interpretador e de `import nltk`
(~1 s nesta máquina), que domina as dezenas de milissegundos dos algoritmos avaliados e
inverteria artificialmente o ranking entre as configurações.
"""

# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DE AMBIENTE
# ==============================================================================

import argparse
import importlib.util
import json
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path


# ==============================================================================
# 2. CARACTERIZAÇÃO DO AMBIENTE COMPUTACIONAL (REPRODUTIBILIDADE)
# ==============================================================================

def registrar_ambiente_execucao() -> dict:
    """Coleta e formaliza os metadados do ambiente de execução conforme Seção 7.2."""
    return {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "plataforma": platform.platform(),
        "arquitetura": platform.machine(),
        "processador": platform.processor() or "Não identificado",
        "versao_python": platform.python_version(),
        "interpretador": sys.executable,
    }


# ==============================================================================
# 3. PROTOCOLO DE MEDIÇÃO E INSTRUMENTAÇÃO TEMPORAL
# ==============================================================================

def carregar_modulo_busca(caminho: Path):
    """Importa dinamicamente o módulo da Etapa 4 para instrumentação in-process."""
    especificacao = importlib.util.spec_from_file_location("busca_e_ordenar", caminho)
    if especificacao is None or especificacao.loader is None:
        raise ImportError(f"Não foi possível carregar o módulo de busca: {caminho}")
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo


def medir_operacao(operacao, repeticoes_internas: int = 5) -> tuple[object, float, float]:
    """Executa `operacao` e devolve (resultado, mediana_ms, pico_memoria_bytes).

    A mediana de `repeticoes_internas` execuções amortiza o ruído do escalonador.
    O pico de memória é aferido com tracemalloc apenas na primeira execução, para
    não incorrer no custo de instrumentação a cada amostra.
    """
    tracemalloc.start()
    try:
        inicio = time.perf_counter()
        resultado = operacao()
        primeira_amostra_ms = (time.perf_counter() - inicio) * 1000.0
        _, pico_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    amostras = [primeira_amostra_ms]
    for _ in range(max(repeticoes_internas - 1, 0)):
        inicio = time.perf_counter()
        operacao()
        amostras.append((time.perf_counter() - inicio) * 1000.0)

    return resultado, statistics.median(amostras), float(pico_bytes)


def executar_corrida_experimental(
    id_execucao: int,
    configuracao_nome: str,
    modo: str,
    metrica: str,
    caminho_chunks: Path,
    nome_carga: str,
    total_chunks_carga: int,
    consulta: str,
    k: int,
    repeticao: int,
    chunks: list[dict],
    chunks_map: dict[str, dict],
    indice_invertido: dict,
    estatisticas_corpus: tuple[int, float, dict[str, int]],
    modulo_busca,
) -> dict:
    """Executa uma instância experimental isolada mensurando tempo de CPU e pico de RAM.

    Parâmetros:
        id_execucao: Identificador ordinal da corrida (1 a 12).
        configuracao_nome: Rótulo formal da configuração avaliada.
        modo: Estratégia de busca ('linear' ou 'indexada').
        metrica: Função de score utilizada ('simples' ou 'bm25').
        caminho_chunks: Caminho do arquivo JSON de chunks avaliado.
        nome_carga: Rótulo da carga de teste (Carga 1 ou Carga 2).
        total_chunks_carga: Quantidade de chunks da carga avaliada.
        consulta: Consulta textual formulada.
        k: Quantidade de candidatos retornados no Top-k.
        repeticao: Índice da repetição experimental (1 ou 2).
        chunks: Lista de chunks da carga avaliada, já carregada em memória.
        chunks_map: Mapa id_chunk -> chunk, usado pela busca indexada.
        indice_invertido: Índice invertido restrito à carga, carregado uma única vez.
        estatisticas_corpus: Tupla (N, avgdl, doc_lengths) pré-calculada da carga.
        modulo_busca: Módulo da Etapa 4 com as funções de busca e ordenação.
    """
    print(f"[{id_execucao:02d}/12] Executando {configuracao_nome} | Carga: {nome_carga} | Rep: {repeticao}...")

    try:
        if modo == "linear":
            resultado, tempo_ms, pico_bytes = medir_operacao(
                lambda: modulo_busca.buscar_linear(
                    chunks,
                    consulta,
                    metrica=metrica,
                    estatisticas_corpus=estatisticas_corpus,
                )
            )
            candidatos, metricas_busca = resultado
            tempo_ordenacao_ms = 0.0
            pico_ordenacao_bytes = 0.0
            comparacoes_ordenacao = 0
        else:
            resultado, tempo_ms, pico_bytes = medir_operacao(
                lambda: modulo_busca.buscar_indexada(
                    indice_invertido,
                    chunks_map,
                    consulta,
                    metrica=metrica,
                    estatisticas_corpus=estatisticas_corpus,
                )
            )
            candidatos, metricas_busca = resultado

            # A Configuração 3 isola a ordenação: as comparações do Merge Sort são
            # executadas sobre os mesmos candidatos, de modo que a diferença entre
            # as Configurações 2 e 3 seja atribuível exclusivamente ao custo O(n log n).
            if "Merge Sort" in configuracao_nome:
                def _ordenar():
                    metricas_merge = {
                        "movimentacoes": 0,
                        "chamadas_recursivas": 0,
                        "profundidade_maxima": 0,
                        "empates_score": 0,
                        "comparacoes_score": 0,
                        "comparacoes_id_chunk": 0,
                        "comparacoes_totais": 0,
                    }
                    ordenados = modulo_busca.merge_sort(list(candidatos), metricas_merge)
                    return modulo_busca.selecionar_topk(ordenados, k), metricas_merge

                (_, metricas_merge), tempo_ordenacao_ms, pico_ordenacao_bytes = medir_operacao(_ordenar)
                comparacoes_ordenacao = metricas_merge["comparacoes_totais"]
            else:
                tempo_ordenacao_ms = 0.0
                pico_ordenacao_bytes = 0.0
                comparacoes_ordenacao = 0

    except Exception as erro:  # noqa: BLE001 - falha da corrida é dado experimental
        print(f"    [ERRO] Falha na execução da instância {id_execucao}: {erro}")
        return {
            "id_execucao": id_execucao,
            "configuracao": configuracao_nome,
            "status": "falha",
            "erro": f"{type(erro).__name__}: {erro}",
            "repeticao": repeticao,
        }

    pico_memoria_mb = (pico_bytes + pico_ordenacao_bytes) / (1024 * 1024)

    return {
        "id_execucao": id_execucao,
        "configuracao": configuracao_nome,
        "modo_busca": modo,
        "metrica_score": metrica,
        "base_chunks": str(caminho_chunks),
        "carga": nome_carga,
        "total_chunks_carga": total_chunks_carga,
        "repeticao": repeticao,
        "tempo_execucao_ms": round(tempo_ms, 4),
        "tempo_ordenacao_ms": round(tempo_ordenacao_ms, 4),
        "pico_memoria_mb": round(pico_memoria_mb, 4),
        "candidatos_avaliados": len(candidatos),
        "comparacoes_ordenacao": comparacoes_ordenacao,
        "distintos_consulta": metricas_busca.get("termos_distintos_consulta", []),
        "status": "sucesso",
    }


# ==============================================================================
# 4. ORQUESTRAÇÃO DA MATRIZ EXPERIMENTAL (12 EXECUÇÕES)
# ==============================================================================

def carregar_chunks(caminho_chunks: Path) -> list[dict]:
    """Carrega a lista de chunks do artefato JSON da Etapa 2."""
    with open(caminho_chunks, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados["chunks"] if isinstance(dados, dict) else dados


def carregar_indice_invertido(caminho_indice: Path, chunks: list[dict]) -> dict:
    """Carrega o índice invertido da Etapa 3 restringindo-o aos chunks da carga.

    A restrição é necessária porque as cargas têm tamanhos diferentes: usar o
    índice integral com uma carga parcial inflaria artificialmente as postings
    de uma das cargas e quebraria a comparabilidade entre elas.
    """
    with open(caminho_indice, "r", encoding="utf-8") as f:
        dados = json.load(f)
    indice_bruto = dados["indice_invertido"] if isinstance(dados, dict) else dados

    ids_validos = {chunk["id_chunk"] for chunk in chunks}

    indice_restrito: dict[str, dict] = {}
    for termo, postings in indice_bruto.items():
        postings_filtrados = [
            {"id_chunk": p["id_chunk"], "frequencia": p["frequencia"]}
            for p in postings["chunks"]
            if p["id_chunk"] in ids_validos
        ]
        if postings_filtrados:
            indice_restrito[termo] = {"chunks": postings_filtrados}

    return indice_restrito


def definir_cargas(caminho_chunks: Path) -> list[dict]:
    """Materializa as duas cargas de teste da Seção 7.2.

    Carga 1 — corpus integral: os 182 chunks resultantes da Etapa 2.
    Carga 2 — corpus reduzido: os 91 chunks de ordem ímpar, amostragem
    determinística que preserva a ordem relativa dos documentos e reduz o
    volume em ~50%, permitindo observar o crescimento assintótico do custo
    das três configurações quando n varia.
    """
    chunks_integrais = carregar_chunks(caminho_chunks)
    chunks_reduzidos = [
        chunk for chunk in chunks_integrais if chunk["ordem_global"] % 2 == 1
    ]

    return [
        {
            "nome": "Carga 1 (Corpus Integral)",
            "descricao": f"{len(chunks_integrais)} chunks — corpus completo da Etapa 2",
            "chunks": chunks_integrais,
        },
        {
            "nome": "Carga 2 (Corpus Reduzido)",
            "descricao": f"{len(chunks_reduzidos)} chunks — amostragem determinística (~50%)",
            "chunks": chunks_reduzidos,
        },
    ]


def executar_matriz_experimentos(
    caminho_chunks: Path,
    consulta: str,
    k: int,
    arquivo_saida: Path,
    caminho_indice: Path,
) -> dict:
    """Orquestra a matriz de 3 configurações x 2 cargas x 2 repetições = 12 execuções."""
    # 1. Definição das configurações conforme Seção 7.1
    configuracoes = [
        {
            "nome": "Configuração 1 (Baseline — Busca Linear)",
            "modo": "linear",
            "metrica": "simples",
            "descricao": "Varredura sequencial de todos os chunks, sem índice invertido.",
        },
        {
            "nome": "Configuração 2 (Busca Indexada — Índice Invertido)",
            "modo": "indexada",
            "metrica": "bm25",
            "descricao": "Recuperação por postings lists do índice invertido (Etapa 3).",
        },
        {
            "nome": "Configuração 3 (Divisão e Conquista — Merge Sort Top-k)",
            "modo": "indexada",
            "metrica": "bm25",
            "descricao": (
                "Busca indexada acrescida da ordenação dos candidatos por Merge Sort "
                "antes da seleção do Top-k, isolando o custo O(n log n)."
            ),
        },
    ]

    # 2. Materialização das cargas de teste (Seção 7.2)
    cargas = definir_cargas(caminho_chunks)

    total_repeticoes = 2

    # 3. Preparação única dos insumos: o carregamento e a preparação do índice
    #    ficam fora da região cronometrada, pois são custo de setup e não da
    #    instância algoritmicamente avaliada.
    modulo_busca = carregar_modulo_busca(Path(__file__).with_name("4_buscar_e_ordenar.py"))
    for carga in cargas:
        carga["chunks_map"] = {chunk["id_chunk"]: chunk for chunk in carga["chunks"]}
        carga["indice"] = carregar_indice_invertido(caminho_indice, carga["chunks"])
        carga["estatisticas"] = modulo_busca.calcular_estatisticas_corpus(carga["chunks"])

    relatorio_experimentos = {
        "metadados": {
            "projeto": "Recuperação de Contexto para IA Generativa (AV1 - PAA/UFS)",
            "consulta_avaliada": consulta,
            "k_definido": k,
            "matriz_design": "3 configurações x 2 cargas x 2 repetições = 12 baterias",
            "metodo_medicao": (
                "Cronometragem in-process (time.perf_counter) da mediana de 5 execuções "
                "da região algoritmicamente relevante; memória via tracemalloc."
            ),
            "cargas": {
                carga["nome"]: carga["descricao"] for carga in cargas
            },
            "configuracoes": {
                config["nome"]: config["descricao"] for config in configuracoes
            },
            "ambiente_computacional": registrar_ambiente_execucao(),
        },
        "execucoes": [],
        "sintese_metricas": {},
    }

    id_contador = 1

    print("=" * 75)
    print("ETAPA 5 — EXECUÇÃO DA BATERIA DE BENCHMARK ALGORÍTMICO (PAA / UFS)")
    print("=" * 75)
    print(f"Consulta: '{consulta}'")
    print(f"Top-k: {k} resultados")
    print(f"Total planejado de execuções: 12 baterias formais")
    print("-" * 75)

    for config in configuracoes:
        for carga in cargas:
            for rep in range(1, total_repeticoes + 1):
                resultado = executar_corrida_experimental(
                    id_execucao=id_contador,
                    configuracao_nome=config["nome"],
                    modo=config["modo"],
                    metrica=config["metrica"],
                    caminho_chunks=caminho_chunks,
                    nome_carga=carga["nome"],
                    total_chunks_carga=len(carga["chunks"]),
                    consulta=consulta,
                    k=k,
                    repeticao=rep,
                    chunks=carga["chunks"],
                    chunks_map=carga["chunks_map"],
                    indice_invertido=carga["indice"],
                    estatisticas_corpus=carga["estatisticas"],
                    modulo_busca=modulo_busca,
                )
                relatorio_experimentos["execucoes"].append(resultado)
                id_contador += 1

    # Cálculo da síntese estatística (médias de tempo por configuração e por carga)
    for config in configuracoes:
        for carga in cargas:
            tempos = [
                e["tempo_execucao_ms"]
                for e in relatorio_experimentos["execucoes"]
                if e["configuracao"] == config["nome"]
                and e.get("carga") == carga["nome"]
                and e["status"] == "sucesso"
            ]
            if tempos:
                relatorio_experimentos["sintese_metricas"].setdefault(config["nome"], {})[
                    carga["nome"]
                ] = {
                    "tempo_medio_ms": round(statistics.mean(tempos), 4),
                    "desvio_padrao_ms": round(
                        statistics.pstdev(tempos) if len(tempos) > 1 else 0.0, 4
                    ),
                    "amostras": len(tempos),
                }

    relatorio_experimentos["tempo_medio_global_ms"] = {
        config["nome"]: round(
            statistics.mean(
                e["tempo_execucao_ms"]
                for e in relatorio_experimentos["execucoes"]
                if e["configuracao"] == config["nome"] and e["status"] == "sucesso"
            ),
            4,
        )
        for config in configuracoes
        if any(
            e["configuracao"] == config["nome"] and e["status"] == "sucesso"
            for e in relatorio_experimentos["execucoes"]
        )
    }

    # Persistência formal do artefato JSON (Seção 7.3)
    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(relatorio_experimentos, f, indent=4, ensure_ascii=False)

    print("-" * 75)
    print(f"Bateria experimental finalizada com sucesso!")
    print(f"Relatório consolidado salvo em: {arquivo_saida}")
    print("=" * 75)

    return relatorio_experimentos


# ==============================================================================
# 5. EXECUÇÃO PRINCIPAL (CLI)
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Etapa 5 — Protocolo Experimental, Coleta de Métricas e Análise de Escalabilidade."
    )
    parser.add_argument(
        "--consulta",
        type=str,
        default="critérios para atribuição de bolsas e requisitos de matrícula",
        help="Consulta padrão utilizada nas baterias de teste experimentais.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Número de candidatos retornados no Top-k (padrão: 5).",
    )
    parser.add_argument(
        "--chunks",
        type=Path,
        default=Path("4_chunks/chunks.json"),
        help="Caminho do arquivo com os chunks gerados na Etapa 2.",
    )
    parser.add_argument(
        "--indice",
        type=Path,
        default=Path("5_indexacao/indice_invertido.json"),
        help="Caminho do índice invertido gerado na Etapa 3.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path("7_resultados/relatorio_experimentos.json"),
        help="Caminho para gravação do relatório experimental consolidado.",
    )
    args = parser.parse_args()

    if not args.chunks.exists():
        raise FileNotFoundError(f"Arquivo de chunks de entrada não encontrado: {args.chunks}")
    if not args.indice.exists():
        raise FileNotFoundError(f"Índice invertido não encontrado: {args.indice}")

    executar_matriz_experimentos(
        caminho_chunks=args.chunks,
        consulta=args.consulta,
        k=args.k,
        arquivo_saida=args.saida,
        caminho_indice=args.indice,
    )


if __name__ == "__main__":
    main()
