# Pygent

Pygent é um assistente de código que executa cada solicitação em um container Docker isolado sempre que possível. Caso Docker não esteja disponível (por exemplo em algumas instalações do Windows), o Pygent ainda funciona executando os comandos localmente.

## Recursos

* Execução de comandos em containers efêmeros (imagem padrão `python:3.12-slim`).
* Integração com modelos da OpenAI para orquestração das etapas.
* Histórico persistente das interações durante a sessão.
* API Python simples para integração em outros projetos.

## Instalação

Recomenda-se instalar a partir do código fonte:

```bash
pip install -e .
```

É necessário possuir Python ≥ 3.9. As dependências de runtime são `openai` e `rich`. Para executar dentro de containers Docker instale também `pygent[docker]`.

## Configuração

O comportamento pode ser ajustado via variáveis de ambiente:

* `OPENAI_API_KEY` &ndash; chave para acesso à API da OpenAI.
* `PYGENT_MODEL` &ndash; modelo utilizado nas chamadas (padrão `gpt-4o-mini-preview`).
* `PYGENT_IMAGE` &ndash; imagem Docker para criar o container (padrão `python:3.12-slim`).
* `PYGENT_USE_DOCKER` &ndash; defina `0` para desabilitar Docker e executar localmente.

## Uso via CLI

Após instalar, execute:

```bash
pygent
```

Use `--docker` para executar os comandos dentro de um container (requere
`pygent[docker]`). Utilize `--no-docker` ou defina `PYGENT_USE_DOCKER=0`
para forçar a execução local.

Digite mensagens normalmente; utilize `/exit` para encerrar a sessão. Todo comando é executado dentro do container e o resultado é exibido no terminal.

## Uso via API

Também é possível interagir diretamente com o código Python:

```python
from pygent import Agent

ag = Agent()
ag.step("echo 'Ola Mundo'")
# ... demias passos
ag.runtime.cleanup()
```

Confira a pasta `examples/` para scripts mais completos.

## Desenvolvimento

1. Instale as dependências de teste:

```bash
pip install -e .[test]
```

2. Rode o conjunto de testes:

```bash
pytest
```

Para gerar a documentação localmente utilize `mkdocs serve`.

## Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.

