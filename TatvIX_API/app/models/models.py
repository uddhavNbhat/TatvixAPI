from sqlmodel import Field, SQLModel, Relationship, Index
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


class User(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # Usert id, each user chat has a subsequent chat id
    username: str = Field(unique=True)
    password: str

    chats: list["Chat"] = Relationship(
        back_populates="user", cascade_delete=True
    )  # Defines one to many relationship with chat table.
    folders: list["Folder"] = Relationship(back_populates="user", cascade_delete=True)
    files: list["Files"] = Relationship(back_populates="user", cascade_delete=True)


class Folder(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    name: str
    owner_id: str | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    chats: list["Chat"] = Relationship(back_populates="folder", cascade_delete=True)
    user: User = Relationship(back_populates="folders")

    # Unique Index on owner id and folder name (cannot have repeating folder names per user)
    __table_args__ = (Index("idx_user_folder_name", "name", "owner_id", unique=True),)


class Chat(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default=None
    )  # Chat id, each user chat has a subsequent chat id
    owner_id: str | None = Field(
        default=None, foreign_key="user.id", ondelete="CASCADE"
    )
    folder_id: str | None = Field(
        default=None, foreign_key="folder.id", ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    header: str = Field(default="New Chat Created")  # Chat header

    user: User = Relationship(
        back_populates="chats"
    )  # When i call user.chats, i will get the full chat instance for that particular user.
    folder: Folder = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(back_populates="chat", cascade_delete=True)


class Message(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # Message id, each user chat has a subsequent chat id
    chat_id: str = Field(foreign_key="chat.id", ondelete="CASCADE")
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    chat: Chat = Relationship(back_populates="messages")
    files: list["MessageFiles"] = Relationship(
        back_populates="message", cascade_delete=True
    )


class MessageFiles(SQLModel, table=True):
    id: str = Field(primary_key=True, default_factory=lambda: str(uuid4()))
    message_id: str | None = Field(
        foreign_key="message.id", default=None, ondelete="CASCADE"
    )
    file_id: str

    message: Optional[Message] = Relationship(back_populates="files")


class Files(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # File id, each user chat has a subsequent chat id
    user_id: str = Field(foreign_key="user.id", ondelete="CASCADE")
    file_path: str = Field(default="")
    file_name: str = Field(nullable=False)
    mime_type: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: User = Relationship(back_populates="files")
    images: list["Images"] = Relationship(back_populates="file", cascade_delete=True)


class Images(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # Image id, each user chat has a subsequent chat id
    file_id: str = Field(foreign_key="files.id", ondelete="CASCADE")
    page_no: int
    text: str = Field(default="")

    file: Files = Relationship(back_populates="images")
