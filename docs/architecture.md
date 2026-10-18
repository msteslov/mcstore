# Architecture

## Components

`mcstore.api` exposes HTTP endpoints and converts domain errors into stable HTTP
responses. `mcstore.services` owns registration, card issuance and transfers.
Only this layer changes balances. `mcstore.models` contains SQLAlchemy models and
database constraints.

`mcstore.bot` is a stateless Telegram adapter. `mcstore.grpc_client` isolates the
Minecraft plugin contract. Generated files are deliberately not committed: the
canonical contracts are `proto/auth.proto` and `proto/stats.proto`, and
`scripts/generate_proto.py` produces the Python bindings.

## Transfer invariant

For every successful transfer:

```text
source_after = source_before - amount
target_after = target_before + amount
total_after = total_before
```

The source and target rows are selected in deterministic order and locked by the
database. The balance changes and transaction record are committed together. A unique
idempotency key protects clients from duplicated network requests.

## Why the upstream gRPC repository is absent

The project uses gRPC as a dependency; it does not modify gRPC itself. Vendoring the
entire upstream source tree makes authorship unclear, inflates the repository and
duplicates the package manager. Only our protocol contracts and generated client code
belong to this project.
