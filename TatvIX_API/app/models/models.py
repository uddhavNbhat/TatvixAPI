from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
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
    files: list["Files"] = Relationship(back_populates="user", cascade_delete=True)


class Chat(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default=None
    )  # Chat id, each user chat has a subsequent chat id
    owner_id: str | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    header: str = Field(default="New Chat Created")  # Chat header

    user: User = Relationship(
        back_populates="chats"
    )  # When i call user.chats, i will get the full chat instance for that particular user.
    messages: list["Message"] = Relationship(back_populates="chat", cascade_delete=True)


class Message(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # Message id, each user chat has a subsequent chat id
    chat_id: str = Field(foreign_key="chat.id")
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    chat: Chat = Relationship(back_populates="messages")


class Files(SQLModel, table=True):
    id: str = Field(
        primary_key=True, default_factory=lambda: str(uuid4())
    )  # File id, each user chat has a subsequent chat id
    user_id: str = Field(foreign_key="user.id")
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
    file_id: str = Field(foreign_key="files.id")
    page_no: int
    text: str = Field(default="")

    file: Files = Relationship(back_populates="images")
