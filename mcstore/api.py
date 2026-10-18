from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Query, status
from sqlalchemy.orm import Session

from mcstore.database import create_schema, get_session
from mcstore.errors import ConflictError, InsufficientFundsError, NotFoundError
from mcstore.schemas import (
    CardCreate,
    CardRead,
    TransactionRead,
    TransferCreate,
    UserCreate,
    UserRead,
)
from mcstore.services import (
    create_card,
    create_user,
    get_user,
    list_cards,
    list_transactions,
    transfer,
)

DbSession = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_schema()
    yield


app = FastAPI(
    title="MC Store API",
    version="2.0.0",
    description="Transactional economy service for a Minecraft server.",
    lifespan=lifespan,
)


@app.exception_handler(NotFoundError)
async def handle_not_found(_request, exc: NotFoundError):
    return _error_response(status.HTTP_404_NOT_FOUND, str(exc))


@app.exception_handler(ConflictError)
async def handle_conflict(_request, exc: ConflictError):
    return _error_response(status.HTTP_409_CONFLICT, str(exc))


@app.exception_handler(InsufficientFundsError)
async def handle_insufficient_funds(_request, exc: InsufficientFundsError):
    return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))


def _error_response(status_code: int, detail: str):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content={"detail": detail})


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, session: DbSession):
    return create_user(session, payload)


@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, session: DbSession):
    return get_user(session, user_id)


@app.post(
    "/users/{user_id}/cards",
    response_model=CardRead,
    status_code=status.HTTP_201_CREATED,
)
def issue_card(user_id: int, payload: CardCreate, session: DbSession):
    return create_card(session, user_id, payload)


@app.get("/users/{user_id}/cards", response_model=list[CardRead])
def read_cards(user_id: int, session: DbSession):
    return list_cards(session, user_id)


@app.post("/transfers", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def make_transfer(payload: TransferCreate, session: DbSession):
    return transfer(session, payload)


@app.get("/transactions", response_model=list[TransactionRead])
def read_transactions(
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    return list_transactions(session, limit)


def run() -> None:
    uvicorn.run("mcstore.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
