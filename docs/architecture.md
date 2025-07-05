# Arquitetura

Entender a arquitetura do Pygent ajuda a customizar e estender o projeto de forma eficaz. O sistema é composto por alguns componentes principais que trabalham em conjunto.

## Componentes Principais

* **`Agent`**: O `Agent` é o orquestrador central. Ele mantém o histórico da conversa, interage com o modelo de linguagem para decidir o próximo passo e despacha as chamadas para as ferramentas. Cada agente possui seu próprio estado, incluindo a persona e as ferramentas habilitadas.

* **`Runtime`**: O `Runtime` representa o ambiente de execução isolado. Ele é responsável por executar comandos (`bash`), interagir com o sistema de arquivos (`write_file`, `read_file`) e gerenciar o ciclo de vida do ambiente (por exemplo, um contêiner Docker). Se o Docker não estiver disponível, o `runtime` executa os comandos localmente. Cada agente tem sua própria instância de `runtime`, garantindo o isolamento entre tarefas.

* **`Model`**: O `Model` é uma interface (protocolo) que abstrai a comunicação com um modelo de linguagem (LLM). A implementação padrão, `OpenAIModel`, interage com APIs compatíveis com a OpenAI. Você pode fornecer sua própria implementação para se conectar a diferentes back-ends de modelo.

* **`TaskManager`**: O `TaskManager` gerencia a execução de tarefas em segundo plano. Quando você usa a ferramenta `delegate_task`, o `TaskManager` cria um novo `Agent` com seu próprio `Runtime` para executar a tarefa de forma assíncrona, permitindo que o agente principal continue seu trabalho ou monitore o progresso da subtarefa.

## Fluxo de uma Requisição

1.  O usuário envia uma mensagem para o `Agent` através da CLI ou da API.
2.  O `Agent` adiciona a mensagem do usuário ao histórico da conversa.
3.  O `Agent` envia o histórico completo para o `Model`.
4.  O `Model` retorna uma resposta, que pode ser uma mensagem de texto ou uma solicitação para chamar uma ou mais ferramentas (`tool_calls`).
5.  Se for uma mensagem de texto, o `Agent` a exibe para o usuário.
6.  Se for uma chamada de ferramenta, o `Agent` invoca a função correspondente (ex: `tools._bash`), passando os argumentos necessários para o `Runtime`.
7.  O `Runtime` executa a ação (por exemplo, um comando `ls` no contêiner Docker).
8.  O resultado da execução é retornado ao `Agent`.
9.  O `Agent` adiciona o resultado da ferramenta ao histórico e, tipicamente, chama o `Model` novamente para que ele possa processar o resultado e decidir o próximo passo, continuando o ciclo até que a tarefa seja concluída (sinalizado pela ferramenta `stop`).