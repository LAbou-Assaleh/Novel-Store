from __future__ import annotations

import re
from dataclasses import dataclass


def normalize_name(value: str) -> str:
    """Normalize an entity-like name for internal storage.

    Parameters:
        value (str): Raw user-provided name.

    Returns:
        str: Lowercase underscore-separated normalized name.
    """
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[\s\-]+", "_", cleaned)
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)
    return cleaned.strip("_")


def normalize_text(value: str) -> str:
    """Normalize free-form text while preserving spaces.

    Parameters:
        value (str): Raw user-provided text.

    Returns:
        str: Lowercase text with collapsed whitespace.
    """
    return re.sub(r"\s+", " ", value.strip().lower())


@dataclass(frozen=True)
class ParsedCommand:
    action: str
    payload: dict[str, str]


def parse_natural_command(raw_command: str) -> ParsedCommand:
    """Parse an MVP natural-language command into a structured command.

    Parameters:
        raw_command (str): Raw command text entered by the user.

    Returns:
        ParsedCommand: Structured action and payload for execution.

    Raises:
        ValueError: If the command is empty or unsupported.
    """
    command = raw_command.strip()
    if not command:
        raise ValueError("Command cannot be empty.")

    normalized = normalize_text(command)

    match = re.fullmatch(r"switch novel ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="novel_switch",
            payload={"name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(r"create novel ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="novel_create",
            payload={"name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(r'import extension "(.+)"', command.strip(), flags=re.IGNORECASE)
    if match:
        return ParsedCommand(
            action="extension_import",
            payload={"path": match.group(1).strip()},
        )

    match = re.fullmatch(r'export extension "(.+)"', command.strip(), flags=re.IGNORECASE)
    if match:
        return ParsedCommand(
            action="extension_export",
            payload={"path": match.group(1).strip()},
        )

    match = re.fullmatch(r"delete novel ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="novel_delete",
            payload={"name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(r"create character table ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="custom_character_table_create",
            payload={"aspect_name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(r"delete character table ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="custom_character_table_delete",
            payload={"aspect_name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(
        r'add character table value ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="custom_character_table_add_value",
            payload={
                "aspect_name": normalize_name(match.group(1)),
                "character_name": normalize_name(match.group(2)),
                "value": normalize_text(match.group(3)),
            },
        )

    match = re.fullmatch(
        r'delete character table value ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="custom_character_table_delete_value",
            payload={
                "aspect_name": normalize_name(match.group(1)),
                "character_name": normalize_name(match.group(2)),
                "value": normalize_text(match.group(3)),
            },
        )

    match = re.fullmatch(
        r'list character table values ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+)',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="custom_character_table_list_values",
            payload={
                "aspect_name": normalize_name(match.group(1)),
                "character_name": normalize_name(match.group(2)),
            },
        )

    match = re.fullmatch(
        r'query character table ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="custom_character_table_query_value",
            payload={
                "aspect_name": normalize_name(match.group(1)),
                "value": normalize_text(match.group(2)),
            },
        )

    match = re.fullmatch(
        r'update character ([a-z0-9_\-\s]+) aspect ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="character_aspect_set",
            payload={
                "name": normalize_name(match.group(1)),
                "aspect_name": normalize_name(match.group(2)),
                "aspect_value": normalize_text(match.group(3)),
            },
        )

    match = re.fullmatch(
        r'delete character ([a-z0-9_\-\s]+) aspect ([a-z0-9_\-\s]+)',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="character_aspect_delete",
            payload={
                "name": normalize_name(match.group(1)),
                "aspect_name": normalize_name(match.group(2)),
            },
        )

    match = re.fullmatch(
        r'update character ([a-z0-9_\-\s]+) (?:trait|traits|characteristic|characteristics) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="character_trait_add",
            payload={
                "name": normalize_name(match.group(1)),
                "trait": normalize_text(match.group(2)),
            },
        )

    match = re.fullmatch(
        r'delete character ([a-z0-9_\-\s]+) (?:trait|traits|characteristic|characteristics) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="character_trait_delete",
            payload={
                "name": normalize_name(match.group(1)),
                "trait": normalize_text(match.group(2)),
            },
        )

    match = re.fullmatch(
        r'update character ([a-z0-9_\-\s]+) relations "(.+)"',
        normalized,
    )
    if match:
        subject = normalize_name(match.group(1))
        relation_phrase = normalize_text(match.group(2))
        rel_match = re.fullmatch(r"([a-z0-9_\-\s]+) with ([a-z0-9_\-\s]+)", relation_phrase)
        if not rel_match:
            raise ValueError('Relation text must look like: "enemy with jessica".')
        return ParsedCommand(
            action="relation_create",
            payload={
                "source": subject,
                "target": normalize_name(rel_match.group(2)),
                "relation_type": normalize_name(rel_match.group(1)),
            },
        )

    match = re.fullmatch(
        r'delete character ([a-z0-9_\-\s]+) relations "(.+)"',
        normalized,
    )
    if match:
        subject = normalize_name(match.group(1))
        relation_phrase = normalize_text(match.group(2))
        rel_match = re.fullmatch(r"([a-z0-9_\-\s]+) with ([a-z0-9_\-\s]+)", relation_phrase)
        if not rel_match:
            raise ValueError('Relation text must look like: "enemy with jessica".')
        return ParsedCommand(
            action="relation_delete",
            payload={
                "source": subject,
                "target": normalize_name(rel_match.group(2)),
                "relation_type": normalize_name(rel_match.group(1)),
            },
        )

    match = re.fullmatch(
        r"create connection ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+)",
        normalized,
    )
    if match:
        return ParsedCommand(
            action="relation_create",
            payload={
                "source": normalize_name(match.group(1)),
                "target": normalize_name(match.group(2)),
                "relation_type": "connected_to",
            },
        )

    match = re.fullmatch(
        r"delete connection ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+)",
        normalized,
    )
    if match:
        return ParsedCommand(
            action="relation_delete",
            payload={
                "source": normalize_name(match.group(1)),
                "target": normalize_name(match.group(2)),
                "relation_type": "connected_to",
            },
        )

    match = re.fullmatch(
        r'create plan ([a-z0-9_\-\s]+)(?: description "(.+)")?',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="plan_create",
            payload={
                "name": normalize_name(match.group(1)),
                "description": normalize_text(match.group(2) or ""),
            },
        )

    match = re.fullmatch(r'delete plan ([a-z0-9_\-\s]+)', normalized)
    if match:
        return ParsedCommand(
            action="plan_delete",
            payload={"name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(
        r'connect plan ([a-z0-9_\-\s]+) with character ([a-z0-9_\-\s]+) as ([a-z0-9_\-\s]+)',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="relation_create",
            payload={
                "source": normalize_name(match.group(1)),
                "target": normalize_name(match.group(2)),
                "relation_type": normalize_name(match.group(3)),
            },
        )

    match = re.fullmatch(
        r'create named connection ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="relation_create",
            payload={
                "source": normalize_name(match.group(1)),
                "target": normalize_name(match.group(2)),
                "relation_type": normalize_name(match.group(3)),
                "relationship_name": normalize_text(match.group(4)),
            },
        )

    match = re.fullmatch(
        r'delete named connection ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) ([a-z0-9_\-\s]+) "(.+)"',
        normalized,
    )
    if match:
        return ParsedCommand(
            action="relation_delete",
            payload={
                "source": normalize_name(match.group(1)),
                "target": normalize_name(match.group(2)),
                "relation_type": normalize_name(match.group(3)),
                "relationship_name": normalize_text(match.group(4)),
            },
        )

    match = re.fullmatch(r'delete character ([a-z0-9_\-\s]+)', normalized)
    if match:
        return ParsedCommand(
            action="character_delete",
            payload={"name": normalize_name(match.group(1))},
        )

    match = re.fullmatch(r"list enemies of ([a-z0-9_\-\s]+)", normalized)
    if match:
        return ParsedCommand(
            action="list_enemies",
            payload={"name": normalize_name(match.group(1))},
        )

    raise ValueError(f"Unsupported command: {raw_command}")
