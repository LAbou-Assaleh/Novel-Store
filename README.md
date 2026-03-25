# Novel Knowledge System

Novel Knowledge System (NKS) is a CLI for storing and organizing novel-writing data in PostgreSQL. It supports novels, sections, notes, characters, relationships, plot points, chapters, worldbuilding locations, timeline events, quick captures, search, backups, and compact review reports.

Running the app with no arguments starts an iterative shell powered by `prompt_toolkit`, with tab completion for commands and common stored names. The shell stays open until you enter `exit`.

The shell accepts either bare commands like `create "My Novel"` or the explicit prefixed form `novel create "My Novel"`.

## Database

NKS uses PostgreSQL for persistence.

For committed code and docs, credentials are not stored in the repository. You must provide a database URL using one of these options:

- Set `NKS_DATABASE_URL` in your shell.
- Run `python3 project/main.py init --db "<database_url>"`.
- Keep local connection details in the gitignored `project/.nks_config.json`.

Resolution order is:

1. Explicit `--db` value
2. `NKS_DATABASE_URL`
3. Saved gitignored config
## Requirements

- Python 3
- PostgreSQL running locally
- A local Postgres user/credential setup provided through environment variables or gitignored config

Install Python dependencies:

```bash
pip install -r project/requirements.txt
```

## Quick Start

Initialize the schema:

```bash
export NKS_DATABASE_URL="<database_url>"
python3 project/main.py init
```

Start the interactive shell:

```bash
python3 project/main.py
```

Inside the shell:

```text
novel> help
novel> create "The Great Swordman"
novel> character add "The Great Swordman" "John Ashen" --role protagonist
novel> exit
```

Create and inspect a novel:

```bash
python3 project/main.py create "The Great Swordman" --genre fantasy --status planning
python3 project/main.py show "The Great Swordman"
```

Build out the project:

```bash
python3 project/main.py section add "The Great Swordman" plot
python3 project/main.py note add "The Great Swordman" --section plot --title "Opening" --body "John is expelled from the academy."
python3 project/main.py character add "The Great Swordman" "John Ashen" --role protagonist
python3 project/main.py character add "The Great Swordman" "Jessica Vale" --role rival
python3 project/main.py character trait add "The Great Swordman" "John Ashen" determined
python3 project/main.py relation add "The Great Swordman" "John Ashen" "Jessica Vale" rival
python3 project/main.py plot add "The Great Swordman" "John begins training in exile."
python3 project/main.py chapter add "The Great Swordman" "Chapter 1" --number 1
python3 project/main.py world place add "The Great Swordman" "Ashen Academy"
python3 project/main.py timeline add "The Great Swordman" "John is expelled" --day 1
python3 project/main.py quick "The Great Swordman" "Hidden bloodline idea"
python3 project/main.py review report "The Great Swordman"
```

## Command Overview

Top-level commands:

- `python3 project/main.py init`
- `python3 project/main.py migrate`
- `python3 project/main.py create`
- `python3 project/main.py list`
- `python3 project/main.py show`
- `python3 project/main.py update`
- `python3 project/main.py search`
- `python3 project/main.py quick`
- `python3 project/main.py backup create`
- `python3 project/main.py section add`
- `python3 project/main.py note add`
- `python3 project/main.py note append`
- `python3 project/main.py note tag`
- `python3 project/main.py character add`
- `python3 project/main.py character trait add`
- `python3 project/main.py relation add`
- `python3 project/main.py plot add`
- `python3 project/main.py chapter add`
- `python3 project/main.py world place add`
- `python3 project/main.py timeline add`
- `python3 project/main.py review report`

## Common Examples

Search all stored content:

```bash
python3 project/main.py search bloodline
python3 project/main.py search duel --type note
```

Update metadata:

```bash
python3 project/main.py update "The Great Swordman" --status drafting --summary "A disgraced swordsman rises again."
```

Append to a note and tag it:

```bash
python3 project/main.py note append 1 "Martial roots system."
python3 project/main.py note tag 1 magic
```

Create a JSON backup snapshot:

```bash
python3 project/main.py backup create
```

## Project Layout

- `project/main.py` is the CLI entrypoint and interactive shell.
- `project/cli.py` contains the command implementations.
- `project/models.py` defines the SQLAlchemy schema.
- `project/db.py` manages the database connection and saved config.
- `project/NKS_CLI_Documentation.tex` contains the LaTeX command reference.

## Notes

- The current implementation is PostgreSQL-first.
- Backups are written as JSON files under `project/backups/`.
- The CLI checks `NKS_DATABASE_URL` before falling back to the gitignored `project/.nks_config.json`.
- Sensitive local connection details should live only in environment variables or gitignored files.
