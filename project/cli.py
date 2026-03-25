from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import typer
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

try:
    from .db import (
        init_db,
        get_session,
        read_config,
        redact_database_url,
        resolve_database_url,
        write_config,
    )
    from .models import (
        Chapter,
        Character,
        CharacterTrait,
        Note,
        NoteTag,
        Novel,
        PlotPoint,
        QuickCapture,
        Relationship,
        Section,
        TimelineEvent,
        WorldPlace,
    )
except ImportError:
    from db import (
        init_db,
        get_session,
        read_config,
        redact_database_url,
        resolve_database_url,
        write_config,
    )
    from models import (
        Chapter,
        Character,
        CharacterTrait,
        Note,
        NoteTag,
        Novel,
        PlotPoint,
        QuickCapture,
        Relationship,
        Section,
        TimelineEvent,
        WorldPlace,
    )


app = typer.Typer(
    help="Novel Knowledge System (NKS) CLI",
    no_args_is_help=True,
    add_completion=False,
)
backup_app = typer.Typer(help="Database backup commands", no_args_is_help=True)
section_app = typer.Typer(help="Section commands", no_args_is_help=True)
note_app = typer.Typer(help="Note commands", no_args_is_help=True)
character_app = typer.Typer(help="Character commands", no_args_is_help=True)
trait_app = typer.Typer(help="Character trait commands", no_args_is_help=True)
relation_app = typer.Typer(help="Relationship commands", no_args_is_help=True)
plot_app = typer.Typer(help="Plot commands", no_args_is_help=True)
chapter_app = typer.Typer(help="Chapter commands", no_args_is_help=True)
world_app = typer.Typer(help="Worldbuilding commands", no_args_is_help=True)
place_app = typer.Typer(help="World place commands", no_args_is_help=True)
timeline_app = typer.Typer(help="Timeline commands", no_args_is_help=True)
review_app = typer.Typer(help="Reporting commands", no_args_is_help=True)

app.add_typer(backup_app, name="backup")
app.add_typer(section_app, name="section")
app.add_typer(note_app, name="note")
app.add_typer(character_app, name="character")
character_app.add_typer(trait_app, name="trait")
app.add_typer(relation_app, name="relation")
app.add_typer(plot_app, name="plot")
app.add_typer(chapter_app, name="chapter")
app.add_typer(world_app, name="world")
world_app.add_typer(place_app, name="place")
app.add_typer(timeline_app, name="timeline")
app.add_typer(review_app, name="review")


def normalize_space(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "backup"


def require_database_url() -> str:
    return resolve_database_url()


def get_novel(session: Session, title: str) -> Novel | None:
    stmt = select(Novel).where(func.lower(Novel.title) == title.strip().lower())
    return session.execute(stmt).scalar_one_or_none()


def require_novel(session: Session, title: str) -> Novel:
    novel = get_novel(session, title)
    if not novel:
        raise typer.BadParameter(f'Novel "{title}" does not exist.')
    return novel


def get_section(session: Session, novel_id: int, name: str) -> Section | None:
    stmt = select(Section).where(
        Section.novel_id == novel_id,
        func.lower(Section.name) == name.strip().lower(),
    )
    return session.execute(stmt).scalar_one_or_none()


def get_or_create_section(session: Session, novel: Novel, name: str) -> Section:
    cleaned_name = normalize_space(name)
    if not cleaned_name:
        raise typer.BadParameter("Section name cannot be empty.")

    section = get_section(session, novel.id, cleaned_name)
    if section:
        return section

    section = Section(novel_id=novel.id, name=cleaned_name)
    session.add(section)
    session.flush()
    return section


def get_character(session: Session, novel_id: int, name: str) -> Character | None:
    stmt = select(Character).where(
        Character.novel_id == novel_id,
        func.lower(Character.name) == name.strip().lower(),
    )
    return session.execute(stmt).scalar_one_or_none()


def require_character(session: Session, novel: Novel, name: str) -> Character:
    character = get_character(session, novel.id, name)
    if not character:
        raise typer.BadParameter(f'Character "{name}" does not exist in "{novel.title}".')
    return character


def build_backup_snapshot(session: Session) -> dict:
    novels = session.execute(select(Novel).order_by(Novel.title)).scalars().all()
    payload: list[dict] = []
    for novel in novels:
        payload.append(
            {
                "title": novel.title,
                "genre": novel.genre,
                "status": novel.status,
                "summary": novel.summary,
                "sections": [section.name for section in novel.sections],
                "notes": [
                    {
                        "id": note.id,
                        "section": note.section.name if note.section else None,
                        "title": note.title,
                        "body": note.body,
                        "tags": [tag.tag for tag in note.tags],
                    }
                    for note in novel.notes
                ],
                "characters": [
                    {
                        "name": character.name,
                        "role": character.role,
                        "description": character.description,
                        "traits": [trait.trait for trait in character.traits],
                    }
                    for character in novel.characters
                ],
                "relationships": [
                    {
                        "source": relation.source_character.name,
                        "target": relation.target_character.name,
                        "type": relation.relation_type,
                    }
                    for relation in novel.relationships
                ],
                "plot_points": [item.description for item in novel.plot_points],
                "chapters": [{"title": item.title, "number": item.number} for item in novel.chapters],
                "places": [item.name for item in novel.places],
                "timeline": [{"event": item.event, "day": item.day} for item in novel.timeline_events],
                "quick_captures": [item.text for item in novel.quick_captures],
            }
        )
    return {"created_at": datetime.now().isoformat(timespec="seconds"), "novels": payload}


def count_label(label: str, value: int) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value} {label}{suffix}"


def emit_search_results(results: Iterable[str]) -> None:
    rows = list(results)
    if not rows:
        typer.echo("No matches found.")
        return
    for row in rows:
        typer.echo(row)


@app.command("init")
def init_command(
    db: str = typer.Option(
        "",
        "--db",
        help="Database URL. Required unless NKS_DATABASE_URL or local gitignored config is set.",
    ),
) -> None:
    """Initialize the database schema and saved configuration."""
    resolved_url = resolve_database_url(db.strip() or None)
    write_config(resolved_url)
    resolved_url = init_db(resolved_url)
    typer.echo(f"Initialized NKS with database `{redact_database_url(resolved_url)}`.")


@app.command("migrate")
def migrate_command() -> None:
    """Apply schema updates to the configured database."""
    resolved_url = require_database_url()
    init_db(resolved_url)
    typer.echo(f"Schema is up to date for `{redact_database_url(resolved_url)}`.")


@backup_app.command("create")
def backup_create() -> None:
    """Create a JSON snapshot backup of the configured database."""
    require_database_url()
    backup_dir = Path(__file__).resolve().parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    with get_session() as session:
        snapshot = build_backup_snapshot(session)
        label = safe_slug(snapshot["novels"][0]["title"]) if snapshot["novels"] else "nks"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{label}_{stamp}.json"
        backup_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    typer.echo(f"Backup created at {backup_path}.")


@app.command("create")
def create_novel(
    title: str,
    genre: str = typer.Option("", "--genre", help="Novel genre"),
    status: str = typer.Option("", "--status", help="Novel status"),
) -> None:
    """Create a novel entry."""
    require_database_url()
    cleaned_title = normalize_space(title)
    if not cleaned_title:
        raise typer.BadParameter("Novel title cannot be empty.")

    with get_session() as session:
        existing = get_novel(session, cleaned_title)
        if existing:
            raise typer.BadParameter(f'Novel "{cleaned_title}" already exists.')

        novel = Novel(
            title=cleaned_title,
            genre=normalize_space(genre),
            status=normalize_space(status),
        )
        session.add(novel)
        session.flush()

    typer.echo(f'Created novel "{cleaned_title}".')


@app.command("list")
def list_novels() -> None:
    """Display all novels."""
    require_database_url()
    with get_session() as session:
        novels = session.execute(select(Novel).order_by(Novel.title)).scalars().all()

    if not novels:
        typer.echo("No novels found.")
        return

    for novel in novels:
        genre = novel.genre or "unspecified"
        status = novel.status or "unspecified"
        typer.echo(f"{novel.title} | genre={genre} | status={status}")


@app.command("show")
def show_novel(title: str) -> None:
    """Display a detailed overview of a novel."""
    require_database_url()
    with get_session() as session:
        stmt = (
            select(Novel)
            .options(
                joinedload(Novel.sections),
                joinedload(Novel.notes).joinedload(Note.tags),
                joinedload(Novel.characters).joinedload(Character.traits),
                joinedload(Novel.relationships).joinedload(Relationship.source_character),
                joinedload(Novel.relationships).joinedload(Relationship.target_character),
                joinedload(Novel.plot_points),
                joinedload(Novel.chapters),
                joinedload(Novel.places),
                joinedload(Novel.timeline_events),
                joinedload(Novel.quick_captures),
            )
            .where(func.lower(Novel.title) == title.strip().lower())
        )
        novel = session.execute(stmt).unique().scalar_one_or_none()

        if not novel:
            raise typer.BadParameter(f'Novel "{title}" does not exist.')

        typer.echo(f"Title: {novel.title}")
        typer.echo(f"Genre: {novel.genre or 'unspecified'}")
        typer.echo(f"Status: {novel.status or 'unspecified'}")
        typer.echo(f"Summary: {novel.summary or 'No summary yet.'}")
        typer.echo(
            "Counts: "
            + ", ".join(
                [
                    count_label("section", len(novel.sections)),
                    count_label("note", len(novel.notes)),
                    count_label("character", len(novel.characters)),
                    count_label("relationship", len(novel.relationships)),
                    count_label("plot point", len(novel.plot_points)),
                    count_label("chapter", len(novel.chapters)),
                    count_label("place", len(novel.places)),
                    count_label("timeline event", len(novel.timeline_events)),
                    count_label("quick capture", len(novel.quick_captures)),
                ]
            )
        )


@app.command("update")
def update_novel(
    title: str,
    status: str = typer.Option("", "--status", help="Updated novel status"),
    summary: str = typer.Option("", "--summary", help="Updated novel summary"),
    genre: str = typer.Option("", "--genre", help="Updated novel genre"),
) -> None:
    """Update metadata for a novel."""
    require_database_url()
    with get_session() as session:
        novel = require_novel(session, title)
        if status.strip():
            novel.status = normalize_space(status)
        if summary.strip():
            novel.summary = normalize_space(summary)
        if genre.strip():
            novel.genre = normalize_space(genre)
        session.add(novel)

    typer.echo(f'Updated novel "{title}".')


@section_app.command("add")
def section_add(title: str, section: str) -> None:
    """Create a section within a novel."""
    require_database_url()
    with get_session() as session:
        novel = require_novel(session, title)
        record = get_or_create_section(session, novel, section)
    typer.echo(f'Added section "{record.name}" to "{title}".')


@note_app.command("add")
def note_add(
    title: str,
    section: str = typer.Option("", "--section", help="Section name"),
    note_title: str = typer.Option("", "--title", help="Note title"),
    body: str = typer.Option("", "--body", help="Note body"),
) -> None:
    """Create a note."""
    require_database_url()
    with get_session() as session:
        novel = require_novel(session, title)
        section_record = get_or_create_section(session, novel, section) if section.strip() else None
        note = Note(
            novel_id=novel.id,
            section_id=section_record.id if section_record else None,
            title=normalize_space(note_title),
            body=body.strip(),
        )
        session.add(note)
        session.flush()
    typer.echo(f"Created note #{note.id} in \"{title}\".")


@note_app.command("append")
def note_append(note_id: int, text: str) -> None:
    """Append text to an existing note."""
    require_database_url()
    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise typer.BadParameter(f"Note #{note_id} does not exist.")
        note.body = f"{note.body}\n{text.strip()}".strip()
        session.add(note)
    typer.echo(f"Appended text to note #{note_id}.")


@note_app.command("tag")
def note_tag(note_id: int, tag: str) -> None:
    """Add a tag to a note."""
    require_database_url()
    cleaned_tag = normalize_space(tag)
    if not cleaned_tag:
        raise typer.BadParameter("Tag cannot be empty.")

    with get_session() as session:
        note = session.get(Note, note_id)
        if not note:
            raise typer.BadParameter(f"Note #{note_id} does not exist.")

        existing_stmt = select(NoteTag).where(
            NoteTag.note_id == note_id,
            func.lower(NoteTag.tag) == cleaned_tag.lower(),
        )
        existing = session.execute(existing_stmt).scalar_one_or_none()
        if not existing:
            session.add(NoteTag(note_id=note_id, tag=cleaned_tag))
    typer.echo(f'Added tag "{cleaned_tag}" to note #{note_id}.')


@character_app.command("add")
def character_add(
    title: str,
    name: str,
    role: str = typer.Option("", "--role", help="Character role"),
) -> None:
    """Create a character."""
    require_database_url()
    cleaned_name = normalize_space(name)
    if not cleaned_name:
        raise typer.BadParameter("Character name cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        if get_character(session, novel.id, cleaned_name):
            raise typer.BadParameter(f'Character "{cleaned_name}" already exists in "{title}".')
        session.add(
            Character(
                novel_id=novel.id,
                name=cleaned_name,
                role=normalize_space(role),
            )
        )
    typer.echo(f'Added character "{cleaned_name}" to "{title}".')


@trait_app.command("add")
def character_trait_add(title: str, name: str, trait: str) -> None:
    """Add a trait to a character."""
    require_database_url()
    cleaned_trait = normalize_space(trait)
    if not cleaned_trait:
        raise typer.BadParameter("Trait cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        character = require_character(session, novel, name)
        existing_stmt = select(CharacterTrait).where(
            CharacterTrait.character_id == character.id,
            func.lower(CharacterTrait.trait) == cleaned_trait.lower(),
        )
        existing = session.execute(existing_stmt).scalar_one_or_none()
        if not existing:
            session.add(CharacterTrait(character_id=character.id, trait=cleaned_trait))
    typer.echo(f'Added trait "{cleaned_trait}" to "{name}".')


@relation_app.command("add")
def relation_add(title: str, char1: str, char2: str, type: str) -> None:
    """Create a relationship between characters."""
    require_database_url()
    relation_type = normalize_space(type)
    if not relation_type:
        raise typer.BadParameter("Relationship type cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        source = require_character(session, novel, char1)
        target = require_character(session, novel, char2)

        existing_stmt = select(Relationship).where(
            Relationship.novel_id == novel.id,
            Relationship.source_character_id == source.id,
            Relationship.target_character_id == target.id,
            func.lower(Relationship.relation_type) == relation_type.lower(),
        )
        existing = session.execute(existing_stmt).scalar_one_or_none()
        if existing:
            raise typer.BadParameter("That relationship already exists.")

        session.add(
            Relationship(
                novel_id=novel.id,
                source_character_id=source.id,
                target_character_id=target.id,
                relation_type=relation_type,
            )
        )
    typer.echo(f'Created {relation_type} relationship: {char1} -> {char2}.')


@plot_app.command("add")
def plot_add(title: str, description: str) -> None:
    """Add a plot point."""
    require_database_url()
    cleaned_description = description.strip()
    if not cleaned_description:
        raise typer.BadParameter("Plot description cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        session.add(PlotPoint(novel_id=novel.id, description=cleaned_description))
    typer.echo(f'Added plot point to "{title}".')


@chapter_app.command("add")
def chapter_add(
    title: str,
    chapter_title: str,
    number: int | None = typer.Option(None, "--number", help="Chapter number"),
) -> None:
    """Create a chapter."""
    require_database_url()
    cleaned_title = normalize_space(chapter_title)
    if not cleaned_title:
        raise typer.BadParameter("Chapter title cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        session.add(Chapter(novel_id=novel.id, title=cleaned_title, number=number))
    typer.echo(f'Added chapter "{cleaned_title}" to "{title}".')


@place_app.command("add")
def world_place_add(title: str, place: str) -> None:
    """Add a world location."""
    require_database_url()
    cleaned_place = normalize_space(place)
    if not cleaned_place:
        raise typer.BadParameter("Place name cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        existing_stmt = select(WorldPlace).where(
            WorldPlace.novel_id == novel.id,
            func.lower(WorldPlace.name) == cleaned_place.lower(),
        )
        existing = session.execute(existing_stmt).scalar_one_or_none()
        if existing:
            raise typer.BadParameter(f'Place "{cleaned_place}" already exists in "{title}".')
        session.add(WorldPlace(novel_id=novel.id, name=cleaned_place))
    typer.echo(f'Added place "{cleaned_place}" to "{title}".')


@timeline_app.command("add")
def timeline_add(
    title: str,
    event: str,
    day: int | None = typer.Option(None, "--day", help="Timeline day number"),
) -> None:
    """Add a timeline event."""
    require_database_url()
    cleaned_event = event.strip()
    if not cleaned_event:
        raise typer.BadParameter("Timeline event cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        session.add(TimelineEvent(novel_id=novel.id, event=cleaned_event, day=day))
    typer.echo(f'Added timeline event to "{title}".')


@app.command("search")
def search(
    query: str,
    type: str = typer.Option("", "--type", help="Optional entity type filter"),
) -> None:
    """Search across stored data."""
    require_database_url()
    needle = query.strip().lower()
    if not needle:
        raise typer.BadParameter("Query cannot be empty.")

    filter_type = type.strip().lower()
    results: list[str] = []

    def include(kind: str) -> bool:
        return not filter_type or filter_type == kind

    with get_session() as session:
        if include("novel"):
            stmt = select(Novel).where(
                or_(
                    func.lower(Novel.title).contains(needle),
                    func.lower(func.coalesce(Novel.summary, "")).contains(needle),
                    func.lower(func.coalesce(Novel.genre, "")).contains(needle),
                    func.lower(func.coalesce(Novel.status, "")).contains(needle),
                )
            )
            results.extend([f'novel | {item.title}' for item in session.execute(stmt).scalars()])

        if include("section"):
            stmt = select(Section, Novel.title).join(Novel).where(func.lower(Section.name).contains(needle))
            results.extend([f'section | {name} | {novel_title}' for name, novel_title in [(item.name, title) for item, title in session.execute(stmt)]])

        if include("note"):
            stmt = (
                select(Note, Novel.title)
                .join(Novel)
                .where(
                    or_(
                        func.lower(func.coalesce(Note.title, "")).contains(needle),
                        func.lower(Note.body).contains(needle),
                    )
                )
            )
            results.extend(
                [
                    f'note | #{item.id} | {title} | {item.title or "untitled"}'
                    for item, title in session.execute(stmt)
                ]
            )

        if include("character"):
            stmt = select(Character, Novel.title).join(Novel).where(
                or_(
                    func.lower(Character.name).contains(needle),
                    func.lower(func.coalesce(Character.role, "")).contains(needle),
                    func.lower(func.coalesce(Character.description, "")).contains(needle),
                )
            )
            results.extend(
                [f'character | {item.name} | {title}' for item, title in session.execute(stmt)]
            )

        if include("relation"):
            stmt = (
                select(Relationship)
                .options(
                    joinedload(Relationship.source_character),
                    joinedload(Relationship.target_character),
                    joinedload(Relationship.novel),
                )
                .where(func.lower(Relationship.relation_type).contains(needle))
            )
            for item in session.execute(stmt).scalars():
                results.append(
                    f"relation | {item.novel.title} | {item.source_character.name} -> {item.target_character.name} ({item.relation_type})"
                )

        if include("plot"):
            stmt = select(PlotPoint, Novel.title).join(Novel).where(
                func.lower(PlotPoint.description).contains(needle)
            )
            results.extend([f'plot | {title} | {item.description}' for item, title in session.execute(stmt)])

        if include("chapter"):
            stmt = select(Chapter, Novel.title).join(Novel).where(func.lower(Chapter.title).contains(needle))
            results.extend(
                [
                    f'chapter | {title} | {item.number if item.number is not None else "?"} | {item.title}'
                    for item, title in session.execute(stmt)
                ]
            )

        if include("place"):
            stmt = select(WorldPlace, Novel.title).join(Novel).where(func.lower(WorldPlace.name).contains(needle))
            results.extend([f'place | {title} | {item.name}' for item, title in session.execute(stmt)])

        if include("timeline"):
            stmt = select(TimelineEvent, Novel.title).join(Novel).where(
                func.lower(TimelineEvent.event).contains(needle)
            )
            results.extend(
                [
                    f'timeline | {title} | day={item.day if item.day is not None else "?"} | {item.event}'
                    for item, title in session.execute(stmt)
                ]
            )

        if include("quick"):
            stmt = select(QuickCapture, Novel.title).join(Novel).where(func.lower(QuickCapture.text).contains(needle))
            results.extend([f'quick | {title} | {item.text}' for item, title in session.execute(stmt)])

    emit_search_results(results)


@app.command("quick")
def quick(title: str, text: str) -> None:
    """Add a fast, unstructured note."""
    require_database_url()
    cleaned_text = text.strip()
    if not cleaned_text:
        raise typer.BadParameter("Quick capture text cannot be empty.")

    with get_session() as session:
        novel = require_novel(session, title)
        capture = QuickCapture(novel_id=novel.id, text=cleaned_text)
        session.add(capture)
        session.flush()
    typer.echo(f'Captured quick note #{capture.id} for "{title}".')


@review_app.command("report")
def review_report(title: str) -> None:
    """Generate a compact report for a novel."""
    require_database_url()
    with get_session() as session:
        stmt = (
            select(Novel)
            .options(
                joinedload(Novel.sections),
                joinedload(Novel.notes).joinedload(Note.tags),
                joinedload(Novel.characters).joinedload(Character.traits),
                joinedload(Novel.relationships).joinedload(Relationship.source_character),
                joinedload(Novel.relationships).joinedload(Relationship.target_character),
                joinedload(Novel.plot_points),
                joinedload(Novel.chapters),
                joinedload(Novel.places),
                joinedload(Novel.timeline_events),
                joinedload(Novel.quick_captures),
            )
            .where(func.lower(Novel.title) == title.strip().lower())
        )
        novel = session.execute(stmt).unique().scalar_one_or_none()
        if not novel:
            raise typer.BadParameter(f'Novel "{title}" does not exist.')

        typer.echo(f"Report for {novel.title}")
        typer.echo(f"Genre: {novel.genre or 'unspecified'}")
        typer.echo(f"Status: {novel.status or 'unspecified'}")
        typer.echo(f"Summary: {novel.summary or 'No summary yet.'}")
        typer.echo(
            "Inventory: "
            + ", ".join(
                [
                    count_label("section", len(novel.sections)),
                    count_label("note", len(novel.notes)),
                    count_label("character", len(novel.characters)),
                    count_label("relationship", len(novel.relationships)),
                    count_label("plot point", len(novel.plot_points)),
                    count_label("chapter", len(novel.chapters)),
                    count_label("place", len(novel.places)),
                    count_label("timeline event", len(novel.timeline_events)),
                    count_label("quick capture", len(novel.quick_captures)),
                ]
            )
        )
        if novel.characters:
            typer.echo("Characters: " + ", ".join(character.name for character in novel.characters[:10]))
        if novel.relationships:
            typer.echo(
                "Relationships: "
                + "; ".join(
                    f"{item.source_character.name}->{item.target_character.name} ({item.relation_type})"
                    for item in novel.relationships[:10]
                )
            )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
