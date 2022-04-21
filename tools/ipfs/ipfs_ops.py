#!/usr/bin/env python3
import click
from ipfs_pin import pin_files
from ipfs_unpin import unpin_files
from ipfs_list import list_files

@click.group()
def main():
    pass

main.add_command(pin_files)
main.add_command(unpin_files)
main.add_command(list_files)

if __name__ == "__main__":
    main()
