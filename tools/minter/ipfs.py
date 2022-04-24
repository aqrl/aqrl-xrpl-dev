import requests
import json
from pathlib import Path
from typing import Dict
from dataclasses import dataclass

DEFAULT_PROVIDER = "Pinata"
PINATA_AUTH_ENDPOINT = "https://api.pinata.cloud/data/testAuthentication"
PINATA_PIN_ENDPOINT = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_UNPIN_ENDPOINT = "https://api.pinata.cloud/pinning/unpin"
PINATA_LIST_ENDPOINT = "https://api.pinata.cloud/data/pinList"
PINATA_AUTH_RESPONSE = "Congratulations! You are communicating with the Pinata API!"

@dataclass
class IPFSFile:
    """ Storage for IPFS Pinned File Details """
    pinhash: str
    pinsize: int
    pintime: str
    pinurl: str

class IPFSRepo:
    """ Connector for IPFS Account, defaults to Pinata """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        provider: str = DEFAULT_PROVIDER,
        auth_endpoint: str = PINATA_AUTH_ENDPOINT,
        pin_endpoint: str = PINATA_PIN_ENDPOINT,
        unpin_endpoint: str = PINATA_UNPIN_ENDPOINT,
        list_endpoint: str = PINATA_LIST_ENDPOINT,
    ) -> None:
        self.provider = provider
        self.auth_url = auth_endpoint
        self.pin_url = pin_endpoint
        self.unpin_url = unpin_endpoint
        self.list_url = list_endpoint
        self.headers = {
            "pinata_api_key": api_key,
            "pinata_secret_api_key": api_secret,
        }
        self.auth = self.do_auth()

    def do_auth(self) -> bool:
        self.auth_response = requests.get(self.auth_url, headers=self.headers)
        resp = json.loads(self.auth_response.text)
        if self.provider == "Pinata":
            return resp["message"] == PINATA_AUTH_RESPONSE
        return False

    def pin(self, filepath: Path) -> Dict:
        if not self.auth:
            return None
        with filepath.open(mode="rb") as f:
            files = {"file": f}
            try:
                response = requests.post(
                                self.pin_url,
                                headers=self.headers,
                                files=files
                           )
                return json.loads(response.text)
            except requests.exceptions.RequestException as e:
                return None

    def unpin(self, filehash: str) -> str:
        if not self.auth:
            return None
        unpin_url = self.unpin_url + "/" + filehash
        try:
            response = requests.delete(
                            unpin_url,
                            headers=self.headers,
                        )
            return response.text
        except requests.exceptions.RequestException as e:
            return None

    def get(self, filename: str) -> Dict:
        if not self.auth:
            return None
        payload = {"status": "pinned", "metadata[name]": filename}
        try:
            response = requests.get(
                            self.list_url,
                            headers=self.headers,
                            params=payload,
                        )
            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            return None






