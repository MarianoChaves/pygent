# Pygent

Pygent é um assistente de código minimalista que executa tarefas dentro de um container Docker isolado. Este manual resume os principais comandos e opções de configuração.

## Instalação

```bash
pip install -e .
```

É necessário possuir Python ≥ 3.9 e Docker configurado. Ajuste as variáveis `OPENAI_API_KEY`, `PYGENT_MODEL` e `PYGENT_IMAGE` conforme necessidade.

## Uso básico

Para iniciar uma sessão interativa execute `pygent` no terminal. Cada comando informado é executado no container e o resultado é impresso em seguida. Utilize `/exit` para encerrar.

Também é possível utilizar a API Python:

```python
from pygent import Agent
ag = Agent()
ag.step("echo teste")
ag.runtime.cleanup()
```

## Desenvolvimento

Instale as dependências opcionais com `pip install -e .[test,docs]` e rode `pytest` para executar os testes. Para gerar esta documentação localmente utilize `mkdocs serve`.

Consulte o arquivo README para informações mais detalhadas.

