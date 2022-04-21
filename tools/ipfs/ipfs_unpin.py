import click
import time
import sys
import json
import logging
from ipfs import IPFSRepo, IPFSFile
from ipfs_utils import load_config, get_logger
from pathlib import Path
from typing import Dict

def unpin_from_ipfs(config: Dict, repo: IPFSRepo, filehash: str) -> bool:
    response = None
    retries = 3
    while not response and retries != 0:
        response = repo.unpin(filehash)
        time.sleep(2)
        retries -= 1
    if not response:
        return False
    return response == "OK"

def unpin_file(
        ipfs_repo: IPFSRepo,
        config: Dict,
        logger,
        file_name: str,
    ) -> bool:
    retries = 3
    data = None
    while retries != 0:
        data = ipfs_repo.get(file_name)
        time.sleep(2)
        retries -= 1
        if "rows" in data:
            break
    if not data or "rows" not in data:
        return False
    filehash = data["rows"][0]["ipfs_pin_hash"]
    logger.info(f"UNPIN[{file_name}]")
    return unpin_from_ipfs(config, ipfs_repo, filehash)

def process_image_and_json(
        ipfs_repo: IPFSRepo,
        config: Dict,
        logger,
        image_num: int
    ) -> bool:
    logger.info(f"Processing Image and JSON for Index: {image_num}")
    collection = config["collection"]
    image = collection + str(image_num) + ".png"
    json_meta = collection + str(image_num) + ".json"
    response_image = unpin_file(ipfs_repo, config, logger, image)
    response_json = unpin_file(ipfs_repo, config, logger, json_meta)
    if response_image and response_json:
        logger.info("Success")
        return True
    else:
        logger.error("Failed")
    return False

@click.command(help="UNPIN files from IPFS")
@click.option(
    '-c',
    '--config_file',
    required=True,
    type=Path,
    help='Config file with secrets and details about collection to pin'
)
@click.option(
    '-l',
    '--log_file',
    default="ipfs_unpin.log",
    type=click.STRING,
    help='Logfile to record runtime info'
)
@click.option(
    '-f',
    '--file_name',
    type=click.STRING,
    help='File to unpin from IPFS'
)
@click.option(
    '-s',
    '--start',
    type=click.INT,
    help='Start index of file in collection to unpin'
)
@click.option(
    '-e',
    '--end',
    type=click.INT,
    help='End index of file in collection to unpin'
)
@click.option(
    '-d',
    '--dry_run',
    is_flag=True,
)
def unpin_files(config_file, log_file, file_name, start, end, dry_run) -> None:
    logger = get_logger(__name__, log_file)
    config = load_config(config_file)
    ipfs_repo = IPFSRepo(
                    api_key=config["pinata_api_key"],
                    api_secret=config["pinata_api_secret"],
                )
    if file_name:
        unpin_file(ipfs_repo, config, logger, file_name)
        return None
    if not start:
        start = config["start_idx"]
    if not end:
        end = config["end_idx"]
    if dry_run:
        logger.info(f"Would process {start} to {end}")
        return None
    for image_num in range(start, end+1):
        result = process_image_and_json(ipfs_repo, config, logger, image_num)
        time.sleep(2)
        if result:
            logger.info(f"Image {image_num} processed successfully")
        else:
            logger.error(f"Failed to process {image_num}")
            return None
