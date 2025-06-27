# Pygent

Pygent é um assistente de código minimalista que executa tarefas dentro de um container Docker isolado sempre que disponível. Caso o Docker não esteja configurado, os comandos são executados localmente. Este manual resume os principais comandos e opções de configuração.

## Instalação

```bash
pip install -e .
```

É necessário possuir Python ≥ 3.9. As dependências principais não incluem Docker. Para habilitar a execução em containers instale `pygent[docker]`. Ajuste as variáveis `OPENAI_API_KEY`, `PYGENT_MODEL`, `PYGENT_IMAGE` e `PYGENT_USE_DOCKER` conforme necessidade.

## Uso básico

Para iniciar uma sessão interativa execute `pygent` no terminal. Utilize a opção `--docker` caso queira rodar os comandos em um container (requer `pygent[docker]`). Caso contrário a execução ocorre localmente. Use `/exit` para encerrar.

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

