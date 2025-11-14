from sqlmodel import Field,SQLModel

class User(SQLModel, table=True):
    id: int|None = Field(primary_key=True,default=None) #Set to none for initialize use, db uses an auto generated primary key
    username: str = Field(unique=True)
    password: str