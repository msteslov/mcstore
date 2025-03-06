import grpc
import stats_pb2
import stats_pb2_grpc
import auth_pb2
import auth_pb2_grpc

def auth(auth_code, IP_PORT):

    channel = grpc.insecure_channel(IP_PORT)
    stub = auth_pb2_grpc.AuthStub(channel)

    request = auth_pb2.AuthCode(code = auth_code)

    try:
        response = stub.acceptCode(request)
    except grpc.RpcError as e:
        print('RPC Error:')
        print(' Code:', e.code())
        print(' Details:', e.details())
        return False
    
    if response.type == auth_pb2.AuthResponse.success:
        return response.player
    else:
        return False
    
def getstat(UUID, IP_PORT):

    if UUID == 'qweqweqe':
        return 6 * 20 * 3600
    
    channel = grpc.insecure_channel(IP_PORT)
    stub = stats_pb2_grpc.StatsStub(channel)

    request = auth_pb2.PlayerId(uuid = UUID)

    try:
        response = stub.getInfo(request)
    except grpc.RpcError as e:
        print('RPC Error:')
        print(' Code:', e.code())
        print(' Details:', e.details())
        return False
    
    if response.HasField('stats'):
        player_info = response.stats

        total_world_time = None
        for entry in player_info.base_stats:

            if entry.type == stats_pb2.BaseStat.total_world_time:
                total_world_time = entry.count
                break

        if total_world_time is not None:
            return str(total_world_time)
        else:
            return False
    # elif response.HasField('Error'):
    #     if response.error == stats_pb2.PlayerStatsResponse.unknown_player:
    #         print("Ошибка: игрок не найден")
    #     else:
    #         print("Ошибка: неизвестная ошибка")
    else:
        print("Получен пустой ответ")
        return False


