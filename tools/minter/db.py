import json
import psycopg2
import click
from pathlib import Path
from typing import List, Dict
from utils import load_config, get_logger

@click.command(help="Upload minted NFT data to Postgres DB")
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
    '-m',
    '--minted_nft_record_file',
    required=True,
    type=Path,
    help='File containing minted nft records'
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
def upload_to_db(config_file, log_file, minted_nft_record_file, start, end, dry_run) -> None:
    logger = get_logger(__name__, log_file)
    config = load_config(config_file)
    db_name = config["heroku_db_name"]
    db_url = config["heroku_db_url"]
    if not start:
        start = config["start_idx"]
    if not end:
        end = config["end_idx"]
    if dry_run:
        logger.info(f"Would process {start} to {end}")
        return None
    minted = {}
    with minted_nft_record_file.open("r") as f:
        minted = json.load(f)
    entries = []
    logger.info(f"Preparing DB Entry Inputs")
    for num in range(start, end+1):
        nft = minted[str(num)]
        entry = (
            nft["id"],
            nft["tokenID"],
            nft["uri"],
            nft["background"],
            nft["pet"],
            nft["pot"],
            nft["eyes"],
            nft["neck"],
            nft["head"],
            nft["mask"],
            nft["clothes"]
        )
        logger.info(f"INPUT {entry}")
        entries.append(entry)
    try:
        logger.info("CONNECTING TO DB")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        args = ','.join(
                 cursor.mogrify(
                     "(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                     entry
                 ).decode('utf-8')
                 for entry in entries
                )
        logger.info("PUSHING TO DB")
        cursor.execute(f"INSERT INTO {db_name} VALUES " + (args))
        conn.commit()
    except Exception as e:
        logger.error(f"EXCEPTION ENCOUNTERED: {e}")
    finally:
        conn.close()
