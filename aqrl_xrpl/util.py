from xrpl.clients import JsonRpcClient

JSON_RPC_URL_ALTNET = "https://s.altnet.rippletest.net:51234/"
JSON_RPC_URL_PROD = "https://s2.ripple.com:51234/"

def get_client(prod=False):
    """Get a prod or altnet network client"""
    if prod:
        return JsonRpcClient(JSON_RPC_URL_PROD)
    return JsonRpcClient(JSON_RPC_URL_ALTNET)


