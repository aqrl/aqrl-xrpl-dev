from xrpl.clients import JsonRpcClient

def get_client(json_rpc_url):
    """Define the network client"""
    return JsonRpcClient(json_rpc_url)


