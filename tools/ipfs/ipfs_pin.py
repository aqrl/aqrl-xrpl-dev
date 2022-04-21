import click
import sys
import json
import boto3
import time
import logging
from ipfs import IPFSRepo, IPFSFile
from ipfs_utils import load_config, get_s3_file, update_json_with_url, get_logger
from pathlib import Path
from typing import Dict

def pin_to_ipfs(config: Dict, repo: IPFSRepo, filepath: Path) -> IPFSFile:
    response = repo.pin(filepath)
    retries = 3
    while not response and retries != 0:
        response = repo.pin(filepath)
        retries -= 1
    if not response:
        return None
    return IPFSFile(
                pinhash=response["IpfsHash"],
                pinsize=response["PinSize"],
                pintime=response["Timestamp"],
                pinurl=config["pinata_gateway"]+response["IpfsHash"]
            )

def pin_s3_file_to_ipfs(
        ipfs_repo: IPFSRepo,
        config: Dict,
        s3_source_uri: str,
        local_dest_path: str,
        logger,
        do_fetch: bool = True,
        do_pin: bool = True,
    ):
    s3_fetch = None
    if do_fetch:
        logger.info(f"S3[{s3_source_uri}] => {local_dest_path}")
        retries = 3
        while not s3_fetch and retries != 0:
            s3_fetch = get_s3_file(
                            bucket=config["s3_bucket"],
                            file_key=s3_source_uri,
                            output_path=local_dest_path,
                        )
            retries -= 1
    else:
        s3_fetch = True
    if do_pin and s3_fetch:
        logger.info(f"PIN[{local_dest_path}] => IPFS")
        ipfs_file = pin_to_ipfs(config, ipfs_repo, Path(local_dest_path))
        logger.info(f"IPFS: {ipfs_file.pinurl}")
        return ipfs_file
    elif s3_fetch:
        return s3_fetch
    else:
        return None


def process_image_and_json(
        ipfs_repo: IPFSRepo,
        config: Dict,
        logger,
        image_num: int
    ) -> bool:
    logger.info(f"Processing Image and JSON for Index: {image_num}")
    collection = config["collection"]
    image = str(image_num) + ".png"
    json_meta = str(image_num) + ".json"
    image_output_dir = config["image_dir"]
    json_output_dir = config["json_dir"]
    s3_image = config["s3_image_dir"]+image
    s3_json = config["s3_json_dir"]+json_meta
    image_out_dir_path = Path(image_output_dir)
    json_out_dir_path = Path(json_output_dir)
    if not image_out_dir_path.exists():
        image_out_dir_path.mkdir(parents=True)
    if not json_out_dir_path.exists():
        json_out_dir_path.mkdir(parents=True)
    output_image = image_output_dir + collection + image
    output_json = json_output_dir + collection + json_meta
    ipfs_image = pin_s3_file_to_ipfs(
                    ipfs_repo,
                    config,
                    s3_image,
                    output_image,
                    logger
                )
    json_fetch = pin_s3_file_to_ipfs(
                    ipfs_repo,
                    config,
                    s3_json,
                    output_json,
                    logger,
                    do_pin=False
                )
    if ipfs_image and json_fetch:
        update_json_with_url(
            Path(output_json),
            "ipfs://"+ipfs_image.pinhash
        )
        ipfs_json = pin_s3_file_to_ipfs(
                        ipfs_repo,
                        config,
                        s3_json,
                        output_json,
                        logger,
                        do_fetch=False
                    )
        logger.info("Success")
        return True
    else:
        logger.error("Fetch or pin failed")
    return False

@click.command(help="PIN files to IPFS")
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
    default="ipfs_pin.log",
    type=click.STRING,
    help='Logfile to record runtime info'
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
def pin_files(config_file, log_file, start, end, dry_run) -> None:
    logger = get_logger(__name__, log_file)
    config = load_config(config_file)
    ipfs_repo = IPFSRepo(
                    api_key=config["pinata_api_key"],
                    api_secret=config["pinata_api_secret"],
                )
    if not start:
        start = config["start_idx"]
    if not end:
        end = config["end_idx"]
    if dry_run:
        logger.info(f"Would process {start} to {end}")
        return None
    for image_num in range(start, end+1):
        result = process_image_and_json(ipfs_repo, config, logger, image_num)
        if result:
            logger.info(f"Image {image_num} processed successfully")
        else:
            logger.error("Failed to process {image_num}")
            return None
