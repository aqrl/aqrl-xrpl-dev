import sys
import json
import logging
import boto3
from typing import Dict
from pathlib import Path

LOGGERS = {}

def load_config(config_path: Path) -> Dict:
    config_data = {}
    with config_path.open() as f:
        config_data = json.load(f)
    return config_data

def get_s3_file(bucket: str, file_key: str, output_path: str) -> bool:
    s3 = boto3.client("s3")
    s3.download_file(
        Bucket=bucket,
        Key=file_key,
        Filename=output_path,
    )
    output = Path(output_path)
    return output.exists()

def update_json_with_url(json_file: Path, pinurl: str) -> None:
    json_meta = {}
    with json_file.open() as f:
        json_meta = json.load(f)
    json_meta["image"] = pinurl
    with json_file.open("w", encoding="utf-8") as f:
        json.dump(json_meta, f, ensure_ascii=False, indent=4)

def get_logger(name: str, log_file: str, verbose: bool = True):
    if name in LOGGERS:
        return LOGGERS[name]
    log = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(filename=log_file)
    if verbose:
        log.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
        file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    log.addHandler(handler)
    log.addHandler(file_handler)
    LOGGERS[name] = log
    return log
