from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from mcstore.errors import ConflictError, InsufficientFundsError, NotFoundError
from mcstore.models import Card, Transaction, User
from mcstore.schemas import CardCreate, TransferCreate, UserCreate


def create_user(session: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("telegram or Minecraft account is already registered") from exc
    session.refresh(user)
    return user


def get_user(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise NotFoundError("user not found")
    return user


def get_user_by_telegram_id(session: Session, telegram_id: int) -> User:
    user = session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user is None:
        raise NotFoundError("user not found")
    return user


def create_card(session: Session, user_id: int, payload: CardCreate) -> Card:
    get_user(session, user_id)
    has_primary = session.scalar(
        select(Card.id).where(Card.owner_id == user_id, Card.is_primary.is_(True)).limit(1)
    )
    if payload.is_primary and has_primary is not None:
        raise ConflictError("user already has a primary card")
    card = Card(
        owner_id=user_id,
        name=payload.name,
        balance=payload.initial_balance,
        is_primary=payload.is_primary or has_primary is None,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


def list_cards(session: Session, user_id: int) -> list[Card]:
    get_user(session, user_id)
    query = select(Card).where(Card.owner_id == user_id).order_by(Card.created_at)
    return list(session.scalars(query))


def transfer(session: Session, payload: TransferCreate) -> Transaction:
    existing = session.scalar(
        select(Transaction).where(Transaction.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        return existing

    cards = list(
        session.scalars(
            select(Card)
            .where(Card.id.in_([payload.source_card_id, payload.target_card_id]))
            .order_by(Card.id)
            .with_for_update()
        )
    )
    by_id = {card.id: card for card in cards}
    source = by_id.get(payload.source_card_id)
    target = by_id.get(payload.target_card_id)
    if source is None or target is None:
        raise NotFoundError("source or target card not found")
    if source.balance < payload.amount:
        raise InsufficientFundsError("insufficient funds")

    source.balance -= payload.amount
    target.balance += payload.amount
    transaction = Transaction(**payload.model_dump())
    session.add(transaction)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        existing = session.scalar(
            select(Transaction).where(Transaction.idempotency_key == payload.idempotency_key)
        )
        if existing is not None:
            return existing
        raise ConflictError("transfer could not be committed") from exc
    session.refresh(transaction)
    return transaction


def list_transactions(session: Session, limit: int = 100) -> list[Transaction]:
    return list(
        session.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(limit))
    )
