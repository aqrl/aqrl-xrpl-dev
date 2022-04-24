from . import util
import json
from xrpl.wallet import generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.response import ResponseStatus
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint
from xrpl.asyncio.transaction import safe_sign_and_autofill_transaction
from xrpl.asyncio.transaction import send_reliable_submission
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.utils import drops_to_xrp
from typing import Union, List, Dict

class XRPLNFT:
    """Represtation of an NFT Token on XRPL"""

    def __init__(self, issuer: str, uri: str, network_url: str) -> None:
        self.issuer = issuer
        self.uri_str = uri
        self.uri = str_to_hex(uri)
        self.network_url = network_url
        self.mint_ready = False
        self.minted = False

    def __str__(self):
        return (f"XRPLNFT[Issuer: {self.issuer}, "
                f"\n\tURI: {self.uri_str}, "
                f"\n\tNetwork: {self.network_url}, "
                f"\n\tMint ready: {self.mint_ready}"
                f"\n\tMinted: {self.minted}]")

    def prepare_mint_tx(
        self,
        taxon: int = 0,
        flags: Union[int, List[int]] = 0,
        transfer_fee: int = 0,
    ) -> None:
        self.mint_tx = NFTokenMint(
                account=self.issuer,
                token_taxon=taxon,
                uri=self.uri,
                flags=flags,
                transfer_fee=transfer_fee,
            )
        self.mint_ready = True

    async def mint(self, wallet: Wallet) -> ResponseStatus:
        async with AsyncWebsocketClient(self.network_url) as client:
            if self.mint_ready:
                signed_tx = await safe_sign_and_autofill_transaction(self.mint_tx, wallet, client)
                self.max_ledger = signed_tx.last_ledger_sequence
                self.tx_id = signed_tx.get_hash()
                self.fee_in_xrp = drops_to_xrp(signed_tx.fee)
                self.mint_response = await send_reliable_submission(signed_tx, client)
                if self.mint_response.status == ResponseStatus.SUCCESS:
                    self.minted = True
                return self.mint_response.status

    def show_mint_response(self) -> None:
        print(f"Mint Outcome: {self.mint_response.status}\nResult Data:")
        print(json.dumps(self.mint_response.result, indent=4, sort_keys=True))

    def get_token_id(self) -> str:
        if self.minted == False:
            return ""
        tx_data = self.mint_response.result
        if "meta" not in tx_data:
            return ""
        self.tokenID = ""
        nft_node = None
        for node in tx_data["meta"]["AffectedNodes"]:
            if "CreatedNode" in node:
                if "NFTokens" in node["CreatedNode"]["NewFields"]:
                    nft_node = node
                    break
            elif "ModifiedNode" in node:
                if "NFTokens" in node["ModifiedNode"]["FinalFields"]:
                    nft_node = node
                    break
        if "CreatedNode" in node:
            self.tokenID = node["CreatedNode"]["NewFields"]["NFTokens"][0]["NFToken"]["NFTokenID"]
        elif "ModifiedNode" in node:
            new_tokens = set()
            old_tokens = set()
            for entry in node["ModifiedNode"]["FinalFields"]["NFTokens"]:
                new_tokens.add(entry["NFToken"]["NFTokenID"])
            for entry in node["ModifiedNode"]["PreviousFields"]["NFTokens"]:
                old_tokens.add(entry["NFToken"]["NFTokenID"])
            new_tokenID = new_tokens - old_tokens
            self.tokenID = new_tokenID.pop()
        return self.tokenID
