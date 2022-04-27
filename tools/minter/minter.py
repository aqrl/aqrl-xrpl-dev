#!/usr/bin/env python3
import click
from mint_nft import mint_nfts
from db import upload_to_db

@click.group()
def main():
    pass

main.add_command(mint_nfts)
main.add_command(upload_to_db)

if __name__ == "__main__":
    main()
