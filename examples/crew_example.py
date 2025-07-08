"""Coordenar dois subagentes em paralelo."""
import time
from pygent import Agent, TaskManager
from pygent.persona import Persona

personas = [
    Persona("escritor", "produz arquivos"),
    Persona("revisor", "analisa o resultado"),
]

manager = TaskManager(personas=personas)
main = Agent()

# Agente 1 escreve um arquivo
escrita = manager.start_task(
    "write_file path='nota.txt' content='ola'\nstop",
    main.runtime,
    persona="escritor",
)

# Agente 2 lê o arquivo
leitura = manager.start_task(
    "bash cmd='cat nota.txt'\nstop",
    main.runtime,
    files=["nota.txt"],
    persona="revisor",
)

for tid in [escrita, leitura]:
    while manager.status(tid) == "running":
        time.sleep(1)
    print(tid, manager.status(tid))

print(manager.collect_file(main.runtime, escrita, "nota.txt"))
main.runtime.cleanup()
