# Ferramentas (Tools)

As ferramentas são o coração da funcionalidade do Pygent, permitindo que o agente interaja com o sistema de arquivos, execute comandos e realize outras ações.

## Ferramentas Nativas

O Pygent vem com um conjunto de ferramentas essenciais prontas para uso:

* **`bash`**: Executa um comando shell no ambiente de execução (local ou Docker).
    * **Parâmetros**: `cmd` (string) - O comando a ser executado.
* **`write_file`**: Cria ou sobrescreve um arquivo no workspace do agente.
    * **Parâmetros**: `path` (string), `content` (string).
* **`stop`**: Para o loop de execução autônoma do agente. Útil para sinalizar o fim de uma tarefa.
* **`continue`**: Usado para solicitar uma resposta ou entrada do usuário, continuando a conversa.

## Ferramentas de Tarefas

Para gerenciar subtarefas e agentes em segundo plano, o Pygent oferece ferramentas específicas que são ativadas ao registrar com `register_task_tools()`:

* **`delegate_task`**: Cria uma nova tarefa em segundo plano com um novo agente.
    * **Parâmetros**: `prompt` (string), `files` (lista de strings, opcional), `persona` (string, opcional), `timeout` (float, opcional).
* **`task_status`**: Verifica o status de uma tarefa delegada.
    * **Parâmetros**: `task_id` (string).
* **`collect_file`**: Recupera um arquivo ou diretório de uma tarefa delegada para o workspace do agente principal.
    * **Parâmetros**: `task_id` (string), `path` (string), `dest` (string, opcional).
* **`list_personas`**: Retorna as personas disponíveis para tarefas delegadas.

## Criando Ferramentas Customizadas

Você pode estender facilmente o Pygent com suas próprias ferramentas.

### Usando `register_tool`

A maneira mais direta de registrar uma nova ferramenta é usando a função `register_tool`.

```python
from pygent import Agent, register_tool

# A função da ferramenta sempre recebe o runtime como primeiro argumento
def hello(rt, name: str) -> str:
    return f"Hello {name}!"

# Registre a ferramenta
register_tool(
    "hello", # Nome da ferramenta
    "Greet by name", # Descrição
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, # Schema de parâmetros
    hello # A função a ser chamada
)

ag = Agent()
# Agora o agente pode usar a ferramenta 'hello'
ag.step("hello name='world'")
ag.runtime.cleanup()
```

Com certeza! Para garantir que não haja problemas de formatação, aqui está o conteúdo completo do arquivo tools.md. Você pode copiar todo o texto abaixo e colar em um novo arquivo chamado tools.md no seu diretório docs/.

Markdown

# Ferramentas (Tools)

As ferramentas são o coração da funcionalidade do Pygent, permitindo que o agente interaja com o sistema de arquivos, execute comandos e realize outras ações.

## Ferramentas Nativas

O Pygent vem com um conjunto de ferramentas essenciais prontas para uso:

* **`bash`**: Executa um comando shell no ambiente de execução (local ou Docker).
    * **Parâmetros**: `cmd` (string) - O comando a ser executado.
* **`write_file`**: Cria ou sobrescreve um arquivo no workspace do agente.
    * **Parâmetros**: `path` (string), `content` (string).
* **`stop`**: Para o loop de execução autônoma do agente. Útil para sinalizar o fim de uma tarefa.
* **`continue`**: Usado para solicitar uma resposta ou entrada do usuário, continuando a conversa.

## Ferramentas de Tarefas

Para gerenciar subtarefas e agentes em segundo plano, o Pygent oferece ferramentas específicas que são ativadas ao registrar com `register_task_tools()`:

* **`delegate_task`**: Cria uma nova tarefa em segundo plano com um novo agente.
    * **Parâmetros**: `prompt` (string), `files` (lista de strings, opcional), `persona` (string, opcional), `timeout` (float, opcional).
* **`task_status`**: Verifica o status de uma tarefa delegada.
    * **Parâmetros**: `task_id` (string).
* **`collect_file`**: Recupera um arquivo ou diretório de uma tarefa delegada para o workspace do agente principal.
    * **Parâmetros**: `task_id` (string), `path` (string), `dest` (string, opcional).
* **`list_personas`**: Retorna as personas disponíveis para tarefas delegadas.

## Criando Ferramentas Customizadas

Você pode estender facilmente o Pygent com suas próprias ferramentas.

### Usando `register_tool`

A maneira mais direta de registrar uma nova ferramenta é usando a função `register_tool`.

```python
from pygent import Agent, register_tool

# A função da ferramenta sempre recebe o runtime como primeiro argumento
def hello(rt, name: str) -> str:
    return f"Hello {name}!"

# Registre a ferramenta
register_tool(
    "hello", # Nome da ferramenta
    "Greet by name", # Descrição
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, # Schema de parâmetros
    hello # A função a ser chamada
)

ag = Agent()
# Agora o agente pode usar a ferramenta 'hello'
ag.step("hello name='world'")
ag.runtime.cleanup()
```

## Usando o decorador @tool
Como alternativa, você pode usar o decorador @tool para um registro mais conciso:

```python
from pygent import tool, Agent

@tool(
    name="goodbye",
    description="Say goodbye",
    parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
)
def goodbye(rt, name: str) -> str:
    return f"Goodbye {name}!"

ag = Agent()
ag.step("goodbye name='world'")
ag.runtime.cleanup()
```