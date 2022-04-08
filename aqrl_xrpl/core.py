from . import util
import json
from xrpl.wallet import generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo

def create_altnet_faucet():
    """Create faucet using altnet client"""
    client = util.get_client(prod=False)
    return create_faucet(client)

def create_faucet(client):
    """Create a wallet using the testnet faucet"""
    test_wallet = generate_faucet_wallet(client, debug=True)
    return test_wallet

def create_account(wallet):
    """Create an account str from the wallet"""
    return wallet.classic_address

def create_xaddress(account):
    """Derive an x-address from the classic address"""
    xaddress = addresscodec.classic_address_to_xaddress(account, tag=12345, is_test_network=True)
    print("\nClassic address:\n\n", account)
    print("X-address:\n\n", xaddress)
    return xaddress

def lookup_account_info(test_account):
    """Look up info about your account"""
    acct_info = AccountInfo(
        account=test_account,
        ledger_index="validated",
        strict=True,
    )
    response = client.request(acct_info)
    result = response.result
    print("response.status: ", response.status)
    print(json.dumps(response.result, indent=4, sort_keys=True))
