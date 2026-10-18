# MC Store / TTB

Backend-проект на Python: экономика Minecraft-сервера с Telegram-интерфейсом и
интеграцией с игровым плагином по gRPC.

Это переработка моего проекта 2025 года. В исходной версии бот, сеть и бизнес-логика
находились в одном файле, данные хранились в JSON, а переводы не были атомарными.
Версия 2.0 сохраняет идею и протокол интеграции, но имеет нормальную архитектуру,
тесты и воспроизводимый запуск.

## Что реализовано

- REST API на FastAPI и Pydantic;
- модели и транзакции SQLAlchemy (SQLite локально, PostgreSQL в Docker);
- атомарный перевод между картами и ключ идемпотентности;
- Telegram-бот на aiogram как тонкий клиент API;
- gRPC-клиент и генерация Python-кода из исходных `.proto`;
- Docker Compose, линтер, тесты и CI.

## Архитектура

```text
Telegram bot ──HTTP──> FastAPI ──SQLAlchemy──> PostgreSQL / SQLite
                           │
Minecraft plugin <──gRPC───┘
```

API является единственной точкой изменения баланса. Telegram и gRPC не обращаются
к БД напрямую. Денежные величины хранятся целыми числами, поэтому ошибки округления
`float` исключены.

## Быстрый запуск

Нужен Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,bot]'
cp .env.example .env
python scripts/generate_proto.py
pytest --cov
mcstore-api
```

Документация API будет доступна по адресу <http://127.0.0.1:8000/docs>.

Полный стек:

```bash
docker compose up --build
```

Telegram-бот запускается отдельно после заполнения `MCSTORE_BOT_TOKEN`:

```bash
mcstore-bot
```

## Пример перевода

```bash
curl -X POST http://127.0.0.1:8000/transfers \
  -H 'Content-Type: application/json' \
  -d '{
    "source_card_id": "SOURCE",
    "target_card_id": "TARGET",
    "amount": 25,
    "idempotency_key": "client-request-0001",
    "message": "shop purchase"
  }'
```

Повтор запроса с тем же `idempotency_key` возвращает уже созданную транзакцию и не
списывает средства второй раз.

## Документация

- [Архитектура](docs/architecture.md)
- [Модель безопасности](docs/security.md)
