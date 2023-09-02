"""Console script for pygrowcube."""
import sys
import click
from pygrowcube.pygrowcube import get_status


@click.command(options_metavar='')
@click.argument('ip_address')
def main(ip_address):
    """Get the status and sensor readings of the GrowCube device at IP_ADDRESS"""
    click.echo(str(get_status(ip_address)))
    return 0

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
