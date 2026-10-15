# Registro da AV2 - Etapa 1

Data: 15/10/2026. Responsável previsto na divisão da equipe: Diego Bispo.
Implementação produzida com apoio do Codex, sujeita à revisão e validação do
responsável. Não se atribui autoria humana exclusiva ao código gerado.

## Contribuição e entregas

| Frente | Entrega preparada |
|---|---|
| Ingestão/tokenização | `preparar_instancias.py`, validação e contagem por chunk. |
| Dados | Corpus tokenizado e instâncias para W = 512, 1024, 2048, 4096 em `dados/`. |
| Orquestração | Notebook AV2 independente para Colab e seção no notebook existente. |
| Documentação | Continuidade da AV1, tokenizer, contrato, custos RAM/I/O e comandos em `README.md`. |
| Verificação | Testes automatizados da preparação e regressão da busca/ordenação AV1. |

A implementação de programação dinâmica é responsabilidade compartilhada com
Kaio nas próximas etapas. Este registro não declara essa implementação concluída
nem presume contribuições futuras de outros integrantes.

## Uso crítico de IA

- Ferramenta: Codex desktop, agente baseado em GPT-6; variante exata não
  disponibilizada no contexto desta sessão.
- Finalidade: leitura do enunciado e plano de divisão, inspeção da AV1,
  implementação da preparação, testes, documentação e integração ao notebook.
- Prompts relevantes desta entrega: “perfeito. vamos implementar a etapa 1.”;
  perguntas sobre branch/tag, definição de tokenizer e pendências de publicação;
  “então vamos avançar para conclusão da etapa 1”.
- Contexto fornecido pelo usuário: enunciado revisado da AV2, divisão de
  responsabilidades e repositório da AV1.
- Sugestões aproveitadas: reutilizar candidatos completos e corpus existentes;
  fixar encoding/versão; guardar hashes; isolar tokenização, associação e I/O;
  gravar resultados da AV2 em diretório próprio.
- Cuidados conceituais aplicados: não equiparar palavras a tokens; não confundir
  score BM25 com qualidade humana ou cobertura; não apresentar W como a janela
  total do modelo; não cortar os candidatos em Top-k antes da otimização.
- Erro identificado e corrigido na validação: inferir que a existência da pasta
  `/content` identifica o Colab. O notebook agora verifica a disponibilidade do
  módulo `google.colab`; fora dele, utiliza a cópia local explicitamente aberta.
- Limitações reconhecidas: nenhum modelo final foi escolhido; o encoding é uma
  convenção experimental explícita; overhead e tokenização do prompt montado
  serão verificados na integração. Não houve geração de resposta por LLM.
- Método de verificação: vetor conhecido de tokens; preservação dos textos e
  scores; testes de entrada inválida/casos de borda; execução no corpus real;
  regressão dos 14 testes da AV1; comparação de hashes das entradas;
  execução do notebook em kernel real em cópia limpa e automação Linux.

Os testes executados pelo agente são evidência técnica, mas não substituem a
revisão e a compreensão do código pela equipe antes da entrega acadêmica.
