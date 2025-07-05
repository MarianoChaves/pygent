# Interface de Linha de Comando (CLI)

A CLI do Pygent oferece uma maneira interativa de interagir com o assistente, permitindo a execução de comandos, o gerenciamento de arquivos e a configuração do ambiente em tempo de real.

## Sessão Interativa

Para iniciar uma sessão interativa, simplesmente execute `pygent` no seu terminal. Você pode usar várias opções para configurar a sessão:

* `--docker`/`--no-docker`: Força a execução de comandos dentro de um contêiner Docker ou localmente.
* `--config <caminho>`: Carrega a configuração de um arquivo TOML específico.
* `--workspace <nome>`: Define um diretório de trabalho para a sessão.
* `--load <dir>`: Carrega um snapshot de um ambiente salvo anteriormente, incluindo o workspace, histórico e variáveis de ambiente.
* `--confirm-bash`: Pede confirmação antes de executar qualquer comando com a ferramenta `bash`.
* `--ban-cmd <comando>`: Desabilita a execução de um comando específico.

## Comandos Internos

Dentro da sessão interativa, você pode usar os seguintes comandos que começam com `/`:

* `/help [comando]`: Mostra a lista de comandos disponíveis ou a ajuda para um comando específico.
* `/cmd <comando>`: Executa um comando shell diretamente no ambiente de `runtime` (local ou Docker).
* `/cp <origem> [destino]`: Copia um arquivo do seu sistema local para o workspace do agente.
* `/new`: Reinicia a conversa, limpando o histórico, mas mantendo o `runtime` atual (e o workspace, se for persistente).
* `/save <dir>`: Salva o estado atual, incluindo o workspace, o histórico da conversa e as variáveis de ambiente, em um diretório para uso posterior.
* `/tools [list|enable|disable <nome>]`: Lista as ferramentas disponíveis ou ativa/desativa uma ferramenta específica durante a sessão.
* `/banned [list|add|remove <nome>]`: Lista, adiciona ou remove comandos da lista de comandos proibidos no `runtime`.
* `/exit`: Encerra a sessão interativa.