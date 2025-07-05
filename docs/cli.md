# Command Line Interface (CLI)

The Pygent CLI offers an interactive way to engage with the assistant, allowing for command execution, file management, and real-time environment configuration.

## Interactive Session

To start an interactive session, simply run `pygent` in your terminal. You can use various options to configure the session:

* `--docker`/`--no-docker`: Forces command execution inside a Docker container or locally.
* `--config <path>`: Loads configuration from a specific TOML file.
* `--workspace <name>`: Defines a working directory for the session.
* `--load <dir>`: Loads a snapshot of a previously saved environment, including the workspace, history, and environment variables.
* `--confirm-bash`: Prompts for confirmation before executing any command with the `bash` tool.
* `--ban-cmd <command>`: Disables the execution of a specific command.

## Internal Commands

Within the interactive session, you can use the following commands that start with `/`:

* `/help [command]`: Shows the list of available commands or help for a specific command.
* `/cmd <command>`: Executes a shell command directly in the `runtime` environment (local or Docker).
* `/cp <source> [destination]`: Copies a file from your local system to the agent's workspace.
* `/new`: Restarts the conversation, clearing the history but keeping the current `runtime` (and workspace, if persistent).
* `/save <dir>`: Saves the current state, including the workspace, conversation history, and environment variables, to a directory for later use.
* `/tools [list|enable|disable <name>]`: Lists available tools or enables/disables a specific tool during the session.
* `/banned [list|add|remove <name>]`: Lists, adds, or removes commands from the list of banned commands in the `runtime`.
* `/exit`: Ends the interactive session.