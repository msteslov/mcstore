from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from mcstore.errors import ConflictError, InsufficientFundsError
from mcstore.schemas import CardCreate, TransferCreate, UserCreate
from mcstore.services import create_card, create_user, transfer


def make_user(session: Session, suffix: str):
    return create_user(
        session,
        UserCreate(
            telegram_id=int(suffix),
            minecraft_uuid=str(uuid4()),
            minecraft_name=f"player_{suffix}",
        ),
    )


def test_transfer_is_atomic_and_first_transaction_succeeds(session: Session) -> None:
    sender = make_user(session, "1001")
    recipient = make_user(session, "1002")
    source = create_card(session, sender.id, CardCreate(initial_balance=100))
    target = create_card(session, recipient.id, CardCreate())

    transaction = transfer(
        session,
        TransferCreate(
            source_card_id=source.id,
            target_card_id=target.id,
            amount=35,
            idempotency_key="transfer-0001",
        ),
    )

    session.refresh(source)
    session.refresh(target)
    assert transaction.id
    assert source.balance == 65
    assert target.balance == 35
    assert source.balance + target.balance == 100


def test_transfer_is_idempotent(session: Session) -> None:
    sender = make_user(session, "2001")
    recipient = make_user(session, "2002")
    source = create_card(session, sender.id, CardCreate(initial_balance=100))
    target = create_card(session, recipient.id, CardCreate())
    payload = TransferCreate(
        source_card_id=source.id,
        target_card_id=target.id,
        amount=20,
        idempotency_key="same-request-key",
    )

    first = transfer(session, payload)
    second = transfer(session, payload)

    session.refresh(source)
    session.refresh(target)
    assert first.id == second.id
    assert (source.balance, target.balance) == (80, 20)


def test_insufficient_funds_do_not_change_balances(session: Session) -> None:
    sender = make_user(session, "3001")
    recipient = make_user(session, "3002")
    source = create_card(session, sender.id, CardCreate(initial_balance=10))
    target = create_card(session, recipient.id, CardCreate())

    with pytest.raises(InsufficientFundsError):
        transfer(
            session,
            TransferCreate(
                source_card_id=source.id,
                target_card_id=target.id,
                amount=11,
                idempotency_key="too-expensive",
            ),
        )
    assert (source.balance, target.balance) == (10, 0)


def test_primary_card_is_unique_per_user(session: Session) -> None:
    user = make_user(session, "4001")
    create_card(session, user.id, CardCreate())
    with pytest.raises(ConflictError):
        create_card(session, user.id, CardCreate(is_primary=True))


def test_same_card_transfer_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TransferCreate(
            source_card_id="card-a",
            target_card_id="card-a",
            amount=1,
            idempotency_key="invalid-key",
        )
