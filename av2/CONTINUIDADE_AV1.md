# Continuidade da AV1 e preparação do contexto - texto para o relatório

## Elementos mantidos e acrescentados

O projeto mantém o tema de recuperação de regulamentos acadêmicos do PROCC/UFS,
os mesmos sete PDFs institucionais e a procedência documentada no catálogo da
AV1. São reutilizados extração, normalização, fragmentação com sobreposição,
índice invertido e pontuação BM25. A configuração versionada da AV1 contém 182
chunks e 75 candidatos positivos para a consulta “critérios para atribuição de
bolsas e requisitos de matrícula”. Os resultados anteriores são preservados.

A nova preparação acrescenta a cada chunk o custo inteiro `w_i`, calculado em
tokens, e o benefício `v_i`, igual ao score já produzido pela busca. A etapa
não refaz a ingestão dos PDFs nem altera o texto dos chunks. Os campos
`id_chunk`, `id_documento`, `nome_arquivo` e `paginas` preservam o vínculo da
evidência com sua fonte. O novo diretório `av2/` reúne código, dados e
documentação sem substituir os artefatos da primeira atividade.

## Representação e parâmetros

Para cada chunk i, definimos `w_i = len(encode_ordinary(texto_i))`, utilizando
tiktoken 0.14.0 e encoding cl100k_base. É uma contagem exata para esse encoding,
escolhido como unidade experimental fixa para ambos os seletores. Não se presume
equivalência entre tokens e palavras. Não há chamada à API ou modelo gerador
necessário para calcular esses custos.

O benefício é `v_i = score_BM25(i, consulta)`, com o arredondamento já adotado na
AV1. Esse score representa relevância lexical estimada, não uma medida direta
de cobertura nem uma garantia de qualidade da resposta. Chunks sem score
positivo permanecem no corpus tokenizado com benefício zero, mas não entram no
conjunto de candidatos da mochila. Textos iguais com IDs distintos continuam
identificáveis para posterior análise de redundância.

As capacidades W = 512, 1024, 2048 e 4096 limitam a soma dos custos dos chunks
selecionados. A lista de candidatos é idêntica nos quatro cenários. Não há corte
prévio em Top-k; itens maiores que a capacidade permanecem na instância para
que os seletores tratem a restrição. Na integração com uma LLM, devem-se reservar
tokens para instruções, consulta, citações e resposta, além de recontar o prompt
montado com o tokenizer efetivamente escolhido. Essa verificação pertence à
etapa de integração e não pode ser inferida da soma dos custos individuais.

## Procedimento e propriedades da preparação

1. Ler corpus e candidatos completos, identificando seus hashes SHA-256.
2. Validar unicidade dos IDs, origem, correspondência dos textos e scores finitos
   não negativos; associar o score pelo ID.
3. Carregar o tokenizer e contar os tokens de cada texto preservado.
4. Construir uma lista comum de itens positivos e quatro cenários de capacidade.
5. Gravar as instâncias e registrar ambiente, parâmetros, commit e tempos.

Após a associação de cada chunk, seu benefício é o score do candidato com o
mesmo ID, ou zero se não existir candidato. A rejeição de IDs repetidos e de
textos/fontes divergentes impede associações ambíguas. A tokenização opera no
texto preservado e não modifica as entradas. Cada cenário referencia uma vez
cada ID de candidato válido. Essas propriedades justificam o contrato de saída
da preparação; não constituem prova de corretude dos futuros seletores.

## Custos no modelo RAM e entrada/saída

Sejam N a quantidade de chunks, M a quantidade de candidatos, L o volume de
texto e B a quantidade de capacidades. A associação por dicionário custa
O(N + M) operações esperadas, acrescida da comparação dos textos dos candidatos.
A montagem dos cenários custa O(BM). A memória mantém os textos e registros,
as referências dos cenários, o tokenizer e a lista temporária de tokens do
maior chunk. O custo da implementação BPE não é equiparado a uma operação RAM
por palavra.

O relatório de preparação mede separadamente leitura/decodificação/hash,
validação/associação, carregamento do tokenizer, contagem/registro de tokens,
montagem dos cenários e serialização/gravação. O carregamento inicial pode
incluir download do vocabulário. O tempo de tokenização não inclui o I/O dos
JSONs nem os algoritmos de seleção. Essas medições descrevem a preparação;
a comparação guloso versus PD será conduzida no benchmark das próximas etapas.

## Versionamento, evidências e limitações

O trabalho utiliza o mesmo repositório, com desenvolvimento na branch `av2` e
preservação da tag `av1-entrega`. O registro de execução identifica o commit
exato, o hash do preparador, os hashes das entradas e o estado da cópia antes
da geração dos dados. As evidências incluem notebook executado, testes
automatizados e matriz com resultados esperados e observados.

O caso padrão usa uma consulta e uma escala de corpus. Variações de W não
substituem as duas escalas e repetições exigidas para o experimento final.
Também permanecem para as etapas seguintes a análise de qualidade/redundância,
a implementação e prova dos seletores e a avaliação do contexto na geração.
