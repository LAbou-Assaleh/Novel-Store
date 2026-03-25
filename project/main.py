from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from typing import Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

try:
    from sqlalchemy import func, select

    from .cli import app
    from .db import get_session
    from .models import Character, Novel, Section
except ImportError:
    from sqlalchemy import func, select

    from cli import app
    from db import get_session
    from models import Character, Novel, Section


@dataclass(frozen=True)
class CompletionContext:
    tokens: list[str]
    raw_prefix: str
    inside_quotes: bool


HELP_LINES = [
    "help",
    "exit",
    "init [--db <database_url>]",
    "migrate",
    'create "<novel>" [--genre <genre>] [--status <status>]',
    "list",
    'show "<novel>"',
    'update "<novel>" [--status <status>] [--summary "<text>"] [--genre <genre>]',
    'search "<query>" [--type <entity>]',
    'quick "<novel>" "<text>"',
    "backup create",
    'section add "<novel>" <section>',
    'note add "<novel>" [--section <section>] [--title "<title>"] [--body "<text>"]',
    'note append <id> "<text>"',
    "note tag <id> <tag>",
    'character add "<novel>" "<name>" [--role <role>]',
    'character trait add "<novel>" "<name>" <trait>',
    'relation add "<novel>" "<char1>" "<char2>" <type>',
    'plot add "<novel>" "<description>"',
    'chapter add "<novel>" "<title>" [--number <num>]',
    'world place add "<novel>" "<place>"',
    'timeline add "<novel>" "<event>" [--day <num>]',
    'review report "<novel>"',
]
HELP_TEXT = "Commands:\n- " + "\n- ".join(HELP_LINES)
COMMAND_PHRASES = ["help", "exit", *[line.split(" [", 1)[0] for line in HELP_LINES[2:]]]


def quote_completion(value: str) -> str:
    return f'"{value.replace("\"", "\\\"")}"'


def parse_shell_tokens(raw_text: str) -> list[str]:
    try:
        tokens = shlex.split(raw_text)
    except ValueError:
        tokens = raw_text.strip().split()
    if tokens and tokens[0] == "novel":
        return tokens[1:]
    return tokens


def get_existing_novels() -> list[str]:
    try:
        with get_session() as session:
            stmt = select(Novel.title).order_by(Novel.title)
            return [row[0] for row in session.execute(stmt)]
    except Exception:
        return []


def get_existing_sections(novel_title: str) -> list[str]:
    try:
        with get_session() as session:
            stmt = (
                select(Section.name)
                .join(Novel, Section.novel_id == Novel.id)
                .where(func.lower(Novel.title) == novel_title.strip().lower())
                .order_by(Section.name)
            )
            return [row[0] for row in session.execute(stmt)]
    except Exception:
        return []


def get_existing_characters(novel_title: str | None = None) -> list[str]:
    try:
        with get_session() as session:
            stmt = select(Character.name).join(Novel, Character.novel_id == Novel.id)
            if novel_title:
                stmt = stmt.where(func.lower(Novel.title) == novel_title.strip().lower())
            stmt = stmt.order_by(Character.name)
            return [row[0] for row in session.execute(stmt)]
    except Exception:
        return []


def get_command_phrase_completions(prefix: str) -> list[str]:
    return [phrase for phrase in COMMAND_PHRASES if phrase.startswith(prefix)]


def get_value_provider(tokens: list[str]) -> Callable[[], list[str]] | None:
    provider_map: dict[tuple[str, ...], Callable[[], list[str]]] = {
        ("show",): get_existing_novels,
        ("update",): get_existing_novels,
        ("quick",): get_existing_novels,
        ("plot", "add"): get_existing_novels,
        ("chapter", "add"): get_existing_novels,
        ("section", "add"): get_existing_novels,
        ("character", "add"): get_existing_novels,
        ("review", "report"): get_existing_novels,
        ("world", "place", "add"): get_existing_novels,
        ("timeline", "add"): get_existing_novels,
        ("relation", "add"): get_existing_novels,
    }
    return provider_map.get(tuple(tokens))


def get_position_aware_provider(tokens: list[str]) -> Callable[[], list[str]] | None:
    if tokens[:2] == ["note", "add"]:
        if len(tokens) == 2:
            return get_existing_novels
        if len(tokens) >= 4 and tokens[-1] == "--section":
            return lambda: get_existing_sections(tokens[2])

    if tokens[:3] == ["character", "trait", "add"]:
        if len(tokens) == 3:
            return get_existing_novels
        if len(tokens) == 4:
            return lambda: get_existing_characters(tokens[3])

    if tokens[:2] == ["relation", "add"]:
        if len(tokens) == 2:
            return get_existing_novels
        if len(tokens) in {3, 4}:
            return lambda: get_existing_characters(tokens[2])

    return None


def build_completion_context(text_before_cursor: str) -> CompletionContext:
    raw_prefix = text_before_cursor.removeprefix("novel ")
    quote_count = text_before_cursor.count('"')
    inside_quotes = quote_count % 2 == 1
    prefix_text = text_before_cursor[: text_before_cursor.rfind('"')] if inside_quotes else text_before_cursor
    return CompletionContext(
        tokens=parse_shell_tokens(prefix_text),
        raw_prefix=raw_prefix,
        inside_quotes=inside_quotes,
    )


class NovelCompleter(Completer):
    def get_completions(self, document: Document, complete_event: object):
        text_before_cursor = document.text_before_cursor
        if not text_before_cursor:
            for candidate in sorted(COMMAND_PHRASES):
                yield Completion(candidate, start_position=0)
            return

        context = build_completion_context(text_before_cursor)

        if context.inside_quotes:
            quote_index = text_before_cursor.rfind('"')
            fragment = text_before_cursor[quote_index + 1 :]
            provider = get_position_aware_provider(context.tokens) or get_value_provider(context.tokens)
            if provider:
                for value in provider():
                    if value.startswith(fragment):
                        yield Completion(value[len(fragment) :] + '"', start_position=0, display=value)
                return

        if text_before_cursor.endswith(" "):
            provider = get_position_aware_provider(context.tokens) or get_value_provider(context.tokens)
            if provider:
                for value in provider():
                    yield Completion(quote_completion(value), start_position=0, display=value)
                return

        for candidate in get_command_phrase_completions(context.raw_prefix):
            yield Completion(candidate, start_position=-len(context.raw_prefix))


def execute_command(raw_command: str) -> None:
    tokens = parse_shell_tokens(raw_command)
    if not tokens:
        return
    app(args=tokens, prog_name="novel", standalone_mode=False)


def run_interactive_loop() -> None:
    session = PromptSession(completer=NovelCompleter(), complete_while_typing=True)
    while True:
        try:
            raw_command = session.prompt("novel> ").strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        if not raw_command:
            continue

        lowered = raw_command.lower()
        if lowered == "exit":
            break
        if lowered == "help":
            print(HELP_TEXT)
            continue

        try:
            execute_command(raw_command)
        except SystemExit:
            continue
        except Exception as exc:
            print(f"Error: {exc}")


def main() -> None:
    if len(sys.argv) > 1:
        app()
        return
    run_interactive_loop()


if __name__ == "__main__":
    main()
