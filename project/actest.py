import shlex
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from typing import List

app = typer.Typer()

# -------------------------
# Mock data (replace with DB)
# -------------------------
CHARACTERS = ["john", "jessica", "mike", "mary", "jonathan"]
REL_TYPES = ["ally", "enemy", "parent", "child"]

COMMANDS = ["view", "connect", "help", "exit"]

# -------------------------
# Typer commands
# -------------------------
@app.command()
def view(name: str):
    typer.echo(f"Viewing character: {name}")


@app.command()
def connect(source: str, target: str, rel_type: str):
    typer.echo(f"{source} -> ({rel_type}) -> {target}")


# -------------------------
# Autocomplete engine
# -------------------------
class CLICompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        parts = text.split()

        # No input → suggest commands
        if not parts:
            for cmd in COMMANDS:
                yield Completion(cmd, start_position=0)
            return

        # First token → command
        if len(parts) == 1 and not text.endswith(" "):
            for cmd in COMMANDS:
                if cmd.startswith(parts[0]):
                    yield Completion(cmd, start_position=-len(parts[0]))
            return

        cmd = parts[0]

        # -------------------------
        # Command-specific completion
        # -------------------------
        if cmd == "view":
            incomplete = parts[-1] if not text.endswith(" ") else ""
            for c in CHARACTERS:
                if c.startswith(incomplete):
                    yield Completion(c, start_position=-len(incomplete))

        elif cmd == "connect":
            arg_index = len(parts) - 1 if not text.endswith(" ") else len(parts)

            # source
            if arg_index == 1:
                incomplete = parts[-1] if not text.endswith(" ") else ""
                for c in CHARACTERS:
                    if c.startswith(incomplete):
                        yield Completion(c, start_position=-len(incomplete))

            # target
            elif arg_index == 2:
                incomplete = parts[-1] if not text.endswith(" ") else ""
                for c in CHARACTERS:
                    if c.startswith(incomplete):
                        yield Completion(c, start_position=-len(incomplete))

            # relationship type
            elif arg_index == 3:
                incomplete = parts[-1] if not text.endswith(" ") else ""
                for r in REL_TYPES:
                    if r.startswith(incomplete):
                        yield Completion(r, start_position=-len(incomplete))

        else:
            # fallback → suggest commands again
            for cmd in COMMANDS:
                if cmd.startswith(parts[0]):
                    yield Completion(cmd, start_position=-len(parts[0]))


# -------------------------
# REPL loop
# -------------------------
def repl():
    session = PromptSession(completer=CLICompleter())

    print("Interactive CLI (Tab for autocomplete, 'exit' to quit)")

    while True:
        try:
            text = session.prompt(">>> ")

            if text.strip() in {"exit", "quit"}:
                break

            args = shlex.split(text)

            if not args:
                continue

            try:
                app(args)
            except SystemExit:
                # prevents Typer from exiting loop
                pass

        except KeyboardInterrupt:
            print("\nInterrupted")
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")


# -------------------------
# Entry
# -------------------------
if __name__ == "__main__":
    repl()