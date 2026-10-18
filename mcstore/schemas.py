from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserCreate(BaseModel):
    telegram_id: int | None = None
    telegram_username: str | None = Field(default=None, max_length=64)
    minecraft_uuid: str = Field(min_length=1, max_length=36)
    minecraft_name: str = Field(min_length=1, max_length=32)
    role: str = Field(default="user", pattern="^(user|banker|admin)$")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int | None
    telegram_username: str | None
    minecraft_uuid: str
    minecraft_name: str
    role: str
    created_at: datetime


class CardCreate(BaseModel):
    name: str = Field(default="Main card", min_length=1, max_length=64)
    initial_balance: int = Field(default=0, ge=0)
    is_primary: bool = False


class CardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: int
    name: str
    balance: int
    is_primary: bool
    created_at: datetime


class TransferCreate(BaseModel):
    source_card_id: str = Field(min_length=1, max_length=32)
    target_card_id: str = Field(min_length=1, max_length=32)
    amount: int = Field(gt=0)
    idempotency_key: str = Field(min_length=8, max_length=128)
    message: str = Field(default="", max_length=255)

    @model_validator(mode="after")
    def cards_must_differ(self):
        if self.source_card_id == self.target_card_id:
            raise ValueError("source and target cards must differ")
        return self


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    idempotency_key: str
    source_card_id: str
    target_card_id: str
    amount: int
    message: str
    created_at: datetime
