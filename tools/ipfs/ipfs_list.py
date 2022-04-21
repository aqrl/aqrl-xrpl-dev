import click
import sys
import json
import logging
from ipfs import IPFSRepo, IPFSFile
from ipfs_utils import load_config, get_logger
from pathlib import Path
from typing import Dict
from pprint import PrettyPrinter

def list_file(config: Dict, repo: IPFSRepo, file_name: str) -> Dict:
    response = None
    retries = 3
    while not response and retries != 0:
        response = repo.get(file_name)
        retries -= 1
    if not response:
        return None
    return response

@click.command(help="LIST files from IPFS")
@click.option(
    '-c',
    '--config_file',
    required=True,
    type=Path,
    help='Config file with secrets and details about collection to pin'
)
@click.option(
    '-f',
    '--file_name',
    required=True,
    type=click.STRING,
    help='File to list from IPFS'
)
@click.option(
    '-l',
    '--log_file',
    default="ipfs_list.log",
    type=click.STRING,
    help='Logfile to record runtime info'
)
def list_files(config_file, file_name, log_file) -> None:
    logger = get_logger(__name__, log_file)
    config = load_config(config_file)
    pp = PrettyPrinter(width=41, compact=True)
    ipfs_repo = IPFSRepo(
                    api_key=config["pinata_api_key"],
                    api_secret=config["pinata_api_secret"],
                )
    logger.info(f"Getting info for {file_name}")
    result = list_file(config, ipfs_repo, file_name)
    logger.info(f"Result: {result}")
    pp.pprint(result)
    return None
