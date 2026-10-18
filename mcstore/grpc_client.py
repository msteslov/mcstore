from dataclasses import dataclass

import grpc

from mcstore.config import get_settings


@dataclass(frozen=True)
class MinecraftAccount:
    uuid: str
    username: str


class MinecraftGrpcClient:
    """Thin adapter over generated protobuf code kept separate from business logic."""

    def __init__(self, endpoint: str | None = None, *, tls: bool | None = None, timeout: float = 5):
        settings = get_settings()
        self.endpoint = endpoint or settings.grpc_endpoint
        self.tls = settings.grpc_tls if tls is None else tls
        self.timeout = timeout

    def _channel(self):
        if self.tls:
            return grpc.secure_channel(self.endpoint, grpc.ssl_channel_credentials())
        return grpc.insecure_channel(self.endpoint)

    def authenticate(self, code: str) -> MinecraftAccount:
        from mcstore.grpc_generated import auth_pb2, auth_pb2_grpc

        with self._channel() as channel:
            stub = auth_pb2_grpc.AuthStub(channel)
            response = stub.acceptCode(auth_pb2.AuthCode(code=code), timeout=self.timeout)
        if response.type != auth_pb2.AuthResponse.success or not response.HasField("player"):
            raise PermissionError("Minecraft authorization code is invalid or expired")
        return MinecraftAccount(uuid=response.player.uuid, username=response.player.name)

    def unlink(self, minecraft_uuid: str) -> bool:
        from mcstore.grpc_generated import auth_pb2, auth_pb2_grpc

        with self._channel() as channel:
            stub = auth_pb2_grpc.AuthStub(channel)
            response = stub.unlink(
                auth_pb2.PlayerId(uuid=minecraft_uuid),
                timeout=self.timeout,
            )
        return response.type == auth_pb2.UnlinkResponse.success
