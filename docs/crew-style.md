# Multi-Agent Collaboration

Pygent pode coordenar diversos agentes em paralelo por meio da classe `TaskManager`. Essa abordagem lembra sistemas como o Crew AI, em que tarefas são distribuídas para agentes especializados.

## Definindo personas

Crie uma lista de `Persona` para representar os papéis dos agentes que irão compor a "equipe":

```python
from pygent import Agent, TaskManager
from pygent.persona import Persona

personas = [
    Persona("escritor", "produz arquivos"),
    Persona("revisor", "analisa o resultado"),
]

manager = TaskManager(personas=personas)
```

## Delegando tarefas

Use `start_task` para lançar subtarefas em background. Defina a persona desejada e, opcionalmente, envie arquivos de apoio:

```python
main = Agent()

# Envie um agente escritor para gerar um arquivo
escrita = manager.start_task(
    "write_file path='nota.txt' content='ola'\nstop",
    main.runtime,
    persona="escritor",
)

# Outro agente lê o arquivo e imprime no console
leitura = manager.start_task(
    "bash cmd='cat nota.txt'\nstop",
    main.runtime,
    files=["nota.txt"],
    persona="revisor",
)
```

## Acompanhar e coletar resultados

O `TaskManager` permite verificar o status e copiar arquivos de volta para o agente principal:

```python
import time
for tid in [escrita, leitura]:
    while manager.status(tid) == "running":
        time.sleep(1)
    print("Status da tarefa", tid + ":", manager.status(tid))

print(manager.collect_file(main.runtime, escrita, "nota.txt"))
main.runtime.cleanup()
```

Com essas chamadas é possível montar fluxos de trabalho em cadeia ou paralelos, obtendo um comportamento semelhante ao de frameworks de múltiplos agentes como o Crew AI.
