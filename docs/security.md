# Security model

## Assets and trust boundaries

- balances and transaction history are protected assets;
- Telegram input, HTTP requests and gRPC responses are untrusted;
- secrets must come from environment variables, never from Git;
- PostgreSQL is the supported backend for concurrent production-like tests.

## Implemented controls

- Pydantic validates sizes, roles, positive amounts and different cards;
- database constraints reject negative balances and non-positive transfers;
- one database transaction contains both balance changes and the ledger record;
- idempotency prevents duplicate withdrawal after client retries;
- parameterized SQLAlchemy expressions avoid string-built SQL;
- gRPC has explicit timeouts and can use TLS;
- examples contain no real tokens or personal data.

## Known gaps

- no user authentication or authorization on REST endpoints;
- the Telegram demo accepts card identifiers instead of binding them to the sender;
- no rate limiting, secret manager, immutable audit log or monitoring;
- default local gRPC mode is plaintext for compatibility with the old plugin;
- `initial_balance` is a bootstrap/demo feature and must become an admin-only mint
  operation in a deployed system.

These gaps are explicit so the repository does not pretend to be production-ready.
