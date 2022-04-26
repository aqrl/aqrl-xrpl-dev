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
from xrpl.utils import hex_to_str
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
    pint = bitstring.pack(f"int:32={packed}")
    unpacked = pint.readlist("int:24, int:8")
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
    except Exception as e:
        logger.error(f"EXCEPTION ENCOUNTERED: {e}")
    finally:
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
    logger,
) -> None:
    minted = {}
    wallet = account.get_wallet()
    collection = config["collection"]
    collection_id = config["collection_id"]
    transfer_fee = config["transfer_fee"]
    try:
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
            logger.info(f"RESULT {mint_response}")
    except Exception as e:
        logger.error(f"EXCEPTION ENCOUNTERED: {e}")


async def get_mint_records(
    config: Dict,
    account: XRPLAccount,
    nft_uris: Dict[str, str],
    minted_record_file: Path,
    meta_json_dir: Path,
    logger,
) -> None:
    collection = config["collection"]
    minted = {}
    try:
        get_nfts = await account.get_nfts(limit=12000)
        nft_list = get_nfts.result["account_nfts"]
        for nft in nft_list:
            taxon = nft["NFTokenTaxon"]
            tokenID = nft["NFTokenID"]
            uri = nft["URI"]
            decoded = decode_taxon(taxon)
            image_num = decoded[0]
            logger.info(f"PROCESSING {image_num}")
            image_json_name = collection + str(image_num) + ".json"
            if nft_uris[image_json_name] == hex_to_str(uri):
                logger.info(f"VALIDATED URI {nft_uris[image_json_name]}")
            else:
                logger.error("MISMATCH URI {nft_uris[image_json_name]} != {hex_to_str(uri)}")
            metadata_file = meta_json_dir / image_json_name
            metadata = {}
            with metadata_file.open("r") as f:
                metadata = json.load(f)
            metadata["name"] = image_json_name
            metadata["tokenID"] = tokenID
            metadata["uri"] = nft_uris[image_json_name]
            minted[image_num] = metadata
    except Exception as e:
        logger.error(f"EXCEPTION ENCOUNTERED: {e}")
    finally:
        if not minted_record_file.exists():
            minted_record_file.touch()
        with minted_record_file.open("r+", encoding="utf-8") as f:
            logger.info(f"DUMP MINTED DETAILS => {minted_record_file}")
            json.dump(minted, f, ensure_ascii=False, indent=4, sort_keys=True)


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
    '-g',
    '--get_mints',
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
def mint_nfts(config_file, log_file, create_uris, get_mints, start, end, dry_run) -> None:
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
    meta_json_dir = Path(config["json_dir"])
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
    if (get_mints):
        asyncio.run(
            get_mint_records(
                config=config,
                account=acc,
                nft_uris=uris,
                minted_record_file=minted_records_file,
                meta_json_dir=meta_json_dir,
                logger=logger
            )
        )
        return None
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
            logger=logger
        )
    )

