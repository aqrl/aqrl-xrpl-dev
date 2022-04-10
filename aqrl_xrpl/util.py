from xrpl.clients import JsonRpcClient
from xrpl.clients import WebsocketClient
from xrpl.wallet import Wallet


JSON_RPC_URL_ALTNET = "https://s.altnet.rippletest.net:51234/"
JSON_RPC_URL_PROD = "https://s2.ripple.com:51234/"
WSS_RPC_URL_DEVNET = "wss://xls20-sandbox.rippletest.net:51233"

DEVNET_WALLET_ADDRESS = "r99H6n1yzYp4m996CPSxLx6pazfguPtScf"
DEVNET_WALLET_SECRET = "snZK5LZiTzdDDaJZqZwtwwDB98Un9"
DEVNET_WALLET_SEQUENCE = 1099624

def get_devnet_wallet():
    return Wallet(seed=DEVNET_WALLET_SECRET, sequence=DEVNET_WALLET_SEQUENCE)

def get_network_url(mode: str) -> str:
    """Get a prod, altnet or devnet network url"""
    if mode == 'prod':
        return JSON_RPC_URL_PROD
    elif mode == 'altnet':
        return JSON_RPC_URL_ALTNET
    else:
        return WSS_RPC_URL_DEVNET

def get_client(mode: str):
    """Get a prod, altnet or devnet network client"""
    if mode == 'prod':
        return JsonRpcClient(JSON_RPC_URL_PROD)
    elif mode == 'altnet':
        return JsonRpcClient(JSON_RPC_URL_ALTNET)
    else:
        return WebsocketClient(WSS_RPC_URL_DEVNET)



