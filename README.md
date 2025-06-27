# Pygent

Pygent é um assistente de código minimalista que executa cada tarefa em um
container Docker isolado. O objetivo é facilitar execução de comandos de forma
segura e reprodutível, mantendo o histórico de mensagens da conversa.

## Instalação

Recomendação mais simples é usar `pip`:

```bash
pip install -e .
```

O projeto requer Python ≥ 3.9 e depende de `docker`, `openai` e `rich`.

## Uso via CLI

Após instalado, inicie a interface interativa com:

```bash
pygent
```

Digita mensagens normalmente e utilize `/exit` para sair.

## Uso via API

Também é possível integrar diretamente com o código Python:

```python
from pygent import Agent

ag = Agent()
ag.step("echo hello")  # roda dentro do container
ag.runtime.cleanup()
```

Veja a pasta `examples/` para scripts mais completos.

