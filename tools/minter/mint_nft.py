#!/usr/bin/env python3
from context import (
    XRPLAccount,
    XRPLNFT,
    get_network_url,
)
import click
import time
import asyncio
import json
import bitstring
from ipfs import IPFSRepo, IPFSFile
from pathlib import Path
from xrpl.models.response import ResponseStatus
from xrpl.models.transactions import NFTokenMintFlag
from typing import List, Dict
from utils import load_config, update_json_with_url, get_logger

def encode_taxon(index: int, coll_id: int) -> int:
    """[24 bits] = INDEX + [8 bits] = COLLECTION ID"""
    packed = bitstring.pack(f"int:24={index}, int:8={coll_id}")
    return packed.int

def decode_taxon(packed: int) -> List:
    """unpacked[0] = INDEX, unpacked[1] = COLLECTION ID"""
    unpacked = packed.readlist("int:24, int:8")
    return unpacked

def get_ipfs_file_info(repo: IPFSRepo, file_name: str) -> Dict:
    response = None
    retries = 3
    while not response and retries != 0:
        response = repo.get(file_name)
        time.sleep(2)
        if "rows" in response:
            break
        retries -= 1
    if not response or "rows" not in response:
        return None
    return response

def get_ipfs_uri_list(
    config: Dict,
    repo: IPFSRepo,
    start: int,
    end: int,
    uri_record_file: Path,
    logger
) -> Dict[str, str]:
    uris = {}
    collection = config["collection"]
    try:
        for image_num in range(start, end+1):
            image_json_name = collection + str(image_num) + ".json"
            logger.info(f"GET [{image_json_name}]")
            info = get_ipfs_file_info(repo, image_json_name)
            fileuri = "ipfs://" + info["rows"][0]["ipfs_pin_hash"]
            logger.info(f"URI [{image_json_name}] = {fileuri}")
            uris[image_json_name] = fileuri
    except:
        with uri_record_file.open("w", encoding="utf-8") as f:
            logger.info(f"DUMP URIS => {uri_record_file}")
            json.dump(uris, f, ensure_ascii=False, indent=4)
    return uris

async def mint_nft_collection(
    config: Dict,
    account: XRPLAccount,
    issuer: str,
    network_url: str,
    flags: List[int],
    start: int,
    end: int,
    nft_uris: Dict[str, str],
    minted_record_file: Path,
    logger,
) -> None:
    minted = {}
    wallet = account.get_wallet()
    collection = config["collection"]
    collection_id = config["collection_id"]
    transfer_fee = config["transfer_fee"]
    for image_num in range(start, end+1):
        image_json_name = collection + str(image_num) + ".json"
        taxon = encode_taxon(image_num, collection_id)
        logger.info(f"MINT[{image_json_name}, {nft_uris[image_json_name]}, {taxon}]")
        nft = XRPLNFT(
            issuer=issuer,
            uri=nft_uris[image_json_name],
            network_url=network_url,
        )
        nft.prepare_mint_tx(
            taxon=taxon,
            flags=flags,
            transfer_fee=transfer_fee,
        )
        mint_response = await nft.mint(wallet)
        token_id = nft.get_token_id()
        details = {
            "name" : image_json_name,
            "tokenID": token_id,
            "uri": nft_uris[image_json_name]
        }
        minted[image_num] = details
        logger.info(f"MINTED[{image_json_name}, {nft_uris[image_json_name]}] => {token_id}")
    with minted_record_file.open("w", encoding="utf-8") as f:
        logger.info(f"DUMP MINTED DETAILS => {minted_record_file}")
        json.dump(minted, f, ensure_ascii=False, indent=4)

@click.command(help="Mint NFT collections on XRPL")
@click.option(
    '-c',
    '--config_file',
    required=True,
    type=Path,
    help='Config file with secrets and details about collection to mint'
)
@click.option(
    '-l',
    '--log_file',
    default="minter.log",
    type=click.STRING,
    help='Logfile to record runtime info'
)
@click.option(
    '-u',
    '--create_uris',
    is_flag=True,
)
@click.option(
    '-s',
    '--start',
    type=click.INT,
    help='Start index of file in collection to pin'
)
@click.option(
    '-e',
    '--end',
    type=click.INT,
    help='End index of file in collection to pin'
)
@click.option(
    '-d',
    '--dry_run',
    is_flag=True,
)
def mint_nfts(config_file, log_file, create_uris, start, end, dry_run) -> None:
    logger = get_logger(__name__, log_file)
    config = load_config(config_file)
    ipfs_repo = IPFSRepo(
                    api_key=config["pinata_api_key"],
                    api_secret=config["pinata_api_secret"],
                )
    xrpl_account = config["xrpl_account"]
    xrpl_secret = config["xrpl_secret"]
    transfer_fee = config["transfer_fee"]
    network_url = get_network_url(mode="devnet")
    acc = XRPLAccount(xrpl_secret, network_url)
    uri_records_file = Path("uris.json")
    minted_records_file = Path("minted.json")
    if not start:
        start = config["start_idx"]
    if not end:
        end = config["end_idx"]
    if dry_run:
        logger.info(f"Would process {start} to {end}")
        return None
    if (create_uris):
        uris = get_ipfs_uri_list(
                    config,
                    ipfs_repo,
                    start,
                    end,
                    uri_records_file,
                    logger
                )
        return None
    else:
        with uri_records_file.open("r") as f:
            uris = json.load(f)
    asyncio.run(
        mint_nft_collection(
            config=config,
            account=acc,
            issuer=xrpl_account,
            network_url=network_url,
            flags=[NFTokenMintFlag.TF_TRANSFERABLE, NFTokenMintFlag.TF_ONLY_XRP],
            start=start,
            end=end,
            nft_uris=uris,
            minted_record_file=minted_records_file,
            logger=logger
        )
    )

