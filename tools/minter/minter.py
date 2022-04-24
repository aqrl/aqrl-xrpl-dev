#!/usr/bin/env python3
import click
from mint_nft import mint_nfts

@click.group()
def main():
    pass

main.add_command(mint_nfts)

if __name__ == "__main__":
    main()
