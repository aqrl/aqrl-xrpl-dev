from . import util
import json
from xrpl.wallet import generate_faucet_wallet
from xrpl.core import addresscodec
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.response import ResponseStatus
from xrpl.utils import str_to_hex
from xrpl.wallet import Wallet
from xrpl.models.requests import NFTBuyOffers
from xrpl.models.requests import NFTSellOffers
from xrpl.models.transactions import NFTokenCreateOffer, NFTokenCreateOfferFlag
from xrpl.models.transactions import NFTokenMint
from xrpl.models.transactions import NFTokenAcceptOffer
from xrpl.asyncio.transaction import safe_sign_and_autofill_transaction
from xrpl.asyncio.transaction import send_reliable_submission
from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.utils import drops_to_xrp
from typing import Optional, Union, List, Dict

class XRPLNFT:
    """Represtation of an NFT Token on XRPL"""

    def __init__(self, issuer: str, uri: str, network_url: str) -> None:
        self.issuer = issuer
        self.uri_str = uri
        self.uri = str_to_hex(uri)
        self.network_url = network_url
        self.mint_ready = False
        self.buy_tx_ready = False
        self.sell_tx_ready = False
        self.offer_tx_ready = False
        self.minted = False
        self.sell_offer_created = False
        self.buy_offer_created = False
        self.offer_accepted = False
        self.has_tokenID = False

    def __str__(self):
        return (f"XRPLNFT[Issuer: {self.issuer}, "
                f"\n\tURI: {self.uri_str}, "
                f"\n\tNetwork: {self.network_url}, "
                f"\n\tMint ready: {self.mint_ready}"
                f"\n\tMinted: {self.minted}]")

    def set_tokenID(self, token_id: str) -> None:
        self.tokenID = token_id
        self.has_tokenID = True

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

    def prepare_sell_offer_tx(
        self,
        sender_account: str,
        price: str = "0",
        flags: Union[int, List[int]] = [NFTokenCreateOfferFlag.TF_SELL_NFTOKEN],
        destination_account: Optional[str] = None,
        expiration: Optional[int] = None,
    ) -> None:
        if not self.has_tokenID:
            return None
        self.sell_tx = NFTokenCreateOffer(
                account=sender_account,
                amount=price,
                nftoken_id=self.tokenID,
                flags=flags
            )
        self.sell_tx_ready = True

    def prepare_buy_offer_tx(
        self,
        sender_account: str,
        owner_account: str,
        price: str = "0"
    ) -> None:
        if not self.has_tokenID:
            return None
        self.buy_tx = NFTokenCreateOffer(
            account=sender_account,
            amount=price,
            nftoken_id=self.tokenID,
            owner=owner_account
        )
        self.buy_tx_ready = True

    def prepare_accept_offer_tx(
        self,
        sender_account: str,
        buy_offer: str = None,
        sell_offer: str = None,
        flags: Union[int, List[int]] = 0,
        broker_fee: str = None
    ) -> None:
        self.offer_tx = NFTokenAcceptOffer(
            account=sender_account,
            flags=flags,
            nftoken_buy_offer=buy_offer,
            nftoken_sell_offer=sell_offer,
            nftoken_broker_fee=broker_fee
        )
        self.offer_tx_ready = True

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

    async def create_sell_offer(self, wallet: Wallet) -> ResponseStatus:
        async with AsyncWebsocketClient(self.network_url) as client:
            if self.sell_tx_ready:
                signed_tx = await safe_sign_and_autofill_transaction(self.sell_tx, wallet, client)
                self.sell_offer_response = await send_reliable_submission(signed_tx, client)
                if self.sell_offer_response.status == ResponseStatus.SUCCESS:
                    self.sell_offer_created = True
                return self.sell_offer_response.status

    async def create_buy_offer(self, wallet: Wallet) -> ResponseStatus:
        async with AsyncWebsocketClient(self.network_url) as client:
            if self.buy_tx_ready:
                signed_tx = await safe_sign_and_autofill_transaction(self.buy_tx, wallet, client)
                self.buy_offer_response = await send_reliable_submission(signed_tx, client)
                if self.buy_offer_response.status == ResponseStatus.SUCCESS:
                    self.buy_offer_created = True
                return self.buy_offer_response.status

    async def accept_offer(self, wallet: Wallet) -> ResponseStatus:
        async with AsyncWebsocketClient(self.network_url) as client:
            if self.offer_tx_ready:
                signed_tx = await safe_sign_and_autofill_transaction(self.offer_tx, wallet, client)
                self.offer_accept_response = await send_reliable_submission(signed_tx, client)
                if self.offer_accept_response.status == ResponseStatus.SUCCESS:
                    self.offer_accepted = True
                return self.offer_accept_response.status

    async def get_buy_offers(self, debug: bool = False):
        async with AsyncWebsocketClient(self.network_url) as client:
            self.get_offers_response = await client.request(
                NFTBuyOffers(
                    nft_id=self.tokenID
                )
            )
            if debug:
                print(self.get_offers_response.status)
                print(json.dumps(self.get_offers_response.result, indent=4, sort_keys=True))
            return self.get_offers_response

    async def get_sell_offers(self, debug: bool = False):
        async with AsyncWebsocketClient(self.network_url) as client:
            self.get_offers_response = await client.request(
                NFTSellOffers(
                    nft_id=self.tokenID
                )
            )
            if debug:
                print(self.get_offers_response.status)
                print(json.dumps(self.get_offers_response.result, indent=4, sort_keys=True))
            return self.get_offers_response

    def show_mint_result(self) -> None:
        print(f"Mint Outcome: {self.mint_response.status}\nResult Data:")
        print(json.dumps(self.mint_response.result, indent=4, sort_keys=True))

    def get_mint_result(self) -> str:
        return json.dumps(self.mint_response.result, indent=4, sort_keys=True)

    def get_buy_offer_result(self) -> str:
        return json.dumps(self.buy_offer_response.result, indent=4, sort_keys=True)

    def get_sell_offer_result(self) -> str:
        return json.dumps(self.sell_offer_response.result, indent=4, sort_keys=True)

    def get_offer_accept_result(self) -> str:
        return json.dumps(self.offer_accept_response.result, indent=4, sort_keys=True)

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
