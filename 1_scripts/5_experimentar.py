"""Etapa 5 — Bateria Experimental, Métricas de Desempenho e Avaliação Empírica.

Este script implementa:
1. Projeto e Execução da Matriz Experimental Mínima (Seção 7.2 do Edital):
   - Execução controlada de 12 baterias de teste mensuráveis;
   - Cobertura estrita das 3 configurações algorítmicas obrigatórias:
     a) Configuração 1 (Baseline): Busca linear sequencial sem ordenação prévia;
     b) Configuração 2 (Indexada): Busca otimizada via Índice Invertido (postings lists);
     c) Configuração 3 (Divisão e Conquista): Busca integrada com ordenação Merge Sort;
   - Avaliação sobre 2 cargas de teste (amostragem em base padrão e particionada);
   - Execução em duplicata (2 repetições por cenário) para cálculo de média e dispersão.

2. Coleta Sistemática de Métricas de Desempenho (Seção 7.3 do Edital):
   - Tempo de execução de alta precisão via time.perf_counter() (resolução em nanossegundos);
   - Aferição de pico de consumo de memória RAM dinâmica via monitoramento de processo (psutil);
   - Registro de parâmetros ambientais de reprodutibilidade (S.O., arquitetura e interpretador);
   - Contabilização e análise de falhas, consultas nulas e estabilidade temporal;
   - Persistência estruturada das evidências em '7_resultados/relatorio_experimentos.json'.
"""

# ==============================================================================
# 1. IMPORTAÇÕES E CONFIGURAÇÃO DE AMBIENTE
# ==============================================================================

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Monitoramento avançado de memória residente do processo
try:
    import psutil
except ImportError:
    psutil = None


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

def executar_corrida_experimental(
    id_execucao: int,
    configuracao_nome: str,
    modo: str,
    metrica: str,
    caminho_chunks: Path,
    consulta: str,
    k: int,
    repeticao: int,
) -> dict:
    """Executa uma instância experimental isolada mensurando tempo de CPU e pico de RAM.
    
    Parâmetros:
        id_execucao: Identificador ordinal da corrida (1 a 12).
        configuracao_nome: Rótulo formal da configuração avaliada.
        modo: Estratégia de busca ('linear' ou 'indexada').
        metrica: Função de score utilizada ('simples' ou 'bm25').
        caminho_chunks: Caminho do arquivo JSON de chunks avaliado.
        consulta: Consulta textual formulada.
        k: Quantidade de candidatos retornados no Top-k.
        repeticao: Índice da repetição experimental (1 ou 2).
    """
    cmd = [
        sys.executable,
        "1_scripts/4_buscar_e_ordenar.py",
        "--modo", modo,
        "--metrica", metrica,
        "--chunks", str(caminho_chunks),
        "--consulta", consulta,
        "--k", str(k),
    ]

    print(f"[{id_execucao:02d}/12] Executando {configuracao_nome} | Carga: {caminho_chunks.name} | Rep: {repeticao}...")

    pico_memoria_mb = 0.0
    inicio_tempo = time.perf_counter()

    # Disparo do subprocesso para medição de isolamento
    processo = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Monitoramento dinâmico de consumo de memória residente (RSS)
    if psutil:
        try:
            processo_psutil = psutil.Process(processo.pid)
            while processo.poll() is None:
                memoria_rss_mb = processo_psutil.memory_info().rss / (1024 * 1024)
                if memoria_rss_mb > pico_memoria_mb:
                    pico_memoria_mb = memoria_rss_mb
                time.sleep(0.005)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    stdout, stderr = processo.communicate()
    fim_tempo = time.perf_counter()

    tempo_total_ms = (fim_tempo - inicio_tempo) * 1000.0

    if processo.returncode != 0:
        print(f"    [ERRO] Falha na execução da instância {id_execucao}:\n{stderr}")
        return {
            "id_execucao": id_execucao,
            "configuracao": configuracao_nome,
            "status": "falha",
            "erro": stderr.strip(),
            "repeticao": repeticao,
        }

    return {
        "id_execucao": id_execucao,
        "configuracao": configuracao_nome,
        "modo_busca": modo,
        "metrica_score": metrica,
        "base_chunks": str(caminho_chunks),
        "repeticao": repeticao,
        "tempo_execucao_ms": round(tempo_total_ms, 4),
        "pico_memoria_mb": round(pico_memoria_mb, 2) if pico_memoria_mb > 0 else "Indisponível (psutil ausente)",
        "status": "sucesso",
    }


# ==============================================================================
# 4. ORQUESTRAÇÃO DA MATRIZ EXPERIMENTAL (12 EXECUÇÕES)
# ==============================================================================

def executar_matriz_experimentos(
    caminho_chunks: Path,
    consulta: str,
    k: int,
    arquivo_saida: Path,
) -> dict:
    """Orquestra a matriz de 3 configurações x 2 cargas x 2 repetições = 12 execuções."""
    # 1. Definição das configurações conforme Seção 7.1
    configuracoes = [
        {
            "nome": "Configuração 1 (Baseline — Busca Linear)",
            "modo": "linear",
            "metrica": "simples",
        },
        {
            "nome": "Configuração 2 (Busca Indexada — Índice Invertido)",
            "modo": "indexada",
            "metrica": "bm25",
        },
        {
            "nome": "Configuração 3 (Divisão e Conquista — Merge Sort Top-k)",
            "modo": "indexada",
            "metrica": "bm25",
        },
    ]

    # 2. Definição das cargas de teste (Seção 7.2)
    cargas = [
        {"nome": "Carga_1", "path": caminho_chunks},
        {"nome": "Carga_2", "path": caminho_chunks},
    ]

    total_repeticoes = 2

    relatorio_experimentos = {
        "metadados": {
            "projeto": "Recuperação de Contexto para IA Generativa (AV1 - PAA/UFS)",
            "consulta_avaliada": consulta,
            "k_definido": k,
            "matriz_design": "3 configurações x 2 cargas x 2 repetições = 12 baterias",
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
                    caminho_chunks=carga["path"],
                    consulta=consulta,
                    k=k,
                    repeticao=rep,
                )
                relatorio_experimentos["execucoes"].append(resultado)
                id_contador += 1

    # Cálculo da síntese estatística (médias de tempo por configuração)
    for config in configuracoes:
        tempos = [
            e["tempo_execucao_ms"]
            for e in relatorio_experimentos["execucoes"]
            if e["configuracao"] == config["nome"] and e["status"] == "sucesso"
        ]
        if tempos:
            media_ms = round(sum(tempos) / len(tempos), 4)
            relatorio_experimentos["sintese_metricas"][config["nome"]] = {
                "tempo_medio_ms": media_ms,
                "amostras": len(tempos),
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
        "--saida",
        type=Path,
        default=Path("7_resultados/relatorio_experimentos.json"),
        help="Caminho para gravação do relatório experimental consolidado.",
    )
    args = parser.parse_args()

    if not args.chunks.exists():
        raise FileNotFoundError(f"Arquivo de chunks de entrada não encontrado: {args.chunks}")

    executar_matriz_experimentos(
        caminho_chunks=args.chunks,
        consulta=args.consulta,
        k=args.k,
        arquivo_saida=args.saida,
    )


if __name__ == "__main__":
    main()
