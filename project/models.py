from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    genre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    sections: Mapped[list["Section"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    characters: Mapped[list["Character"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    plot_points: Mapped[list["PlotPoint"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    chapters: Mapped[list["Chapter"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    places: Mapped[list["WorldPlace"]] = relationship(back_populates="novel", cascade="all, delete-orphan")
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="novel", cascade="all, delete-orphan"
    )
    quick_captures: Mapped[list["QuickCapture"]] = relationship(
        back_populates="novel", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="novel", cascade="all, delete-orphan"
    )


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("novel_id", "name", name="uq_section_novel_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="sections")
    notes: Mapped[list["Note"]] = relationship(back_populates="section")


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    section_id: Mapped[int | None] = mapped_column(ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")

    novel: Mapped[Novel] = relationship(back_populates="notes")
    section: Mapped[Section | None] = relationship(back_populates="notes")
    tags: Mapped[list["NoteTag"]] = relationship(back_populates="note", cascade="all, delete-orphan")


class NoteTag(Base):
    __tablename__ = "note_tags"
    __table_args__ = (UniqueConstraint("note_id", "tag", name="uq_note_tag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    tag: Mapped[str] = mapped_column(String(120), nullable=False)

    note: Mapped[Note] = relationship(back_populates="tags")


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("novel_id", "name", name="uq_character_novel_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    novel: Mapped[Novel] = relationship(back_populates="characters")
    traits: Mapped[list["CharacterTrait"]] = relationship(back_populates="character", cascade="all, delete-orphan")
    outgoing_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="source_character",
        foreign_keys="Relationship.source_character_id",
    )
    incoming_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="target_character",
        foreign_keys="Relationship.target_character_id",
    )


class CharacterTrait(Base):
    __tablename__ = "character_traits"
    __table_args__ = (UniqueConstraint("character_id", "trait", name="uq_character_trait"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trait: Mapped[str] = mapped_column(String(120), nullable=False)

    character: Mapped[Character] = relationship(back_populates="traits")


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint(
            "novel_id",
            "source_character_id",
            "target_character_id",
            "relation_type",
            name="uq_character_relationship",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    source_character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[str] = mapped_column(String(120), nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="relationships")
    source_character: Mapped[Character] = relationship(
        back_populates="outgoing_relationships",
        foreign_keys=[source_character_id],
    )
    target_character: Mapped[Character] = relationship(
        back_populates="incoming_relationships",
        foreign_keys=[target_character_id],
    )


class PlotPoint(Base):
    __tablename__ = "plot_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="plot_points")


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (UniqueConstraint("novel_id", "number", name="uq_chapter_novel_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    novel: Mapped[Novel] = relationship(back_populates="chapters")


class WorldPlace(Base):
    __tablename__ = "world_places"
    __table_args__ = (UniqueConstraint("novel_id", "name", name="uq_world_place_novel_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="places")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)

    novel: Mapped[Novel] = relationship(back_populates="timeline_events")


class QuickCapture(Base):
    __tablename__ = "quick_captures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    novel: Mapped[Novel] = relationship(back_populates="quick_captures")
