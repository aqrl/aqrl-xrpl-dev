#!/usr/bin/env python3
from context import (
    XRPLAccount,
    XRPLNFT,
    get_network_url,
)
import asyncio
import json
from time import time
from xrpl.models.response import ResponseStatus
from xrpl.models.transactions import NFTokenMintFlag
from typing import List, Dict

_ACCOUNT = "rG2ueQWPDfRy6KaR2YLpj2sjaDBbtrCrDW"
_SECRET = "sspSBf4LjEwpXyRffSdgQRuChwezh"
_URI = "https://aqrl.mypinata.cloud/ipfs/QmQMdhAX7zz7zP7eC9jzXy7dBFppXQFgYQFhaa7SfjJXwn"
_NUM_MINT = 10
_TRANSFER_FEE = 1000 # 1%

async def get_nfts_in_account(account: XRPLAccount, debug: bool = False) -> None:
    get_nfts_response = await account.get_nfts(debug=debug)
    account.parse_get_nfts_response()
    account.list_nfts()

def create_nft_uris(num: int) -> Dict[int, str]:
    uris = {}
    for taxon in range(num):
        uris[taxon] = str(taxon)
    return uris

async def mint_nft_collection(
    num: int,
    account: XRPLAccount,
    issuer: str,
    network_url: str,
    flags: List[int],
    nft_uris: Dict[int, str],
    debug: bool = False,
) -> None:
    wallet = account.get_wallet()
    time_sum = 0
    for i in range(num):
        if debug:
            print(f"Creating NFT[{i}]..")
        start = time()
        nft = XRPLNFT(
            issuer=issuer,
            uri=nft_uris[i],
            network_url=network_url,
        )
        nft.prepare_mint_tx(
            taxon=i,
            flags=flags,
            transfer_fee=_TRANSFER_FEE,
        )
        mint_response = await nft.mint(wallet)
        duration = time() - start
        time_sum += duration
        if debug:
            nft.show_mint_response()
            print(f"Time taken: {duration}s")
    print(f"Total time taken to mint {num} NFTs: {time_sum}s "
            f"i.e. {time_sum/60:.2f}min {time_sum % 60:.2f}s "
            f"i.e. {time_sum // num:.2f}s per NFT")

async def main() -> None:
    network_url = get_network_url(mode="devnet")
    acc = XRPLAccount(_SECRET, network_url)
    uris = create_nft_uris(_NUM_MINT)
    await mint_nft_collection(
        num=_NUM_MINT,
        account=acc,
        issuer=_ACCOUNT,
        network_url=network_url,
        flags=[NFTokenMintFlag.TF_TRANSFERABLE, NFTokenMintFlag.TF_ONLY_XRP],
        nft_uris=uris,
        debug=True,
    )
    await get_nfts_in_account(acc, debug=True)

if __name__ == "__main__":
    asyncio.run(main())

