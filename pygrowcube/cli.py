"""Console script for pygrowcube."""
import sys
import click
from pygrowcube.pygrowcube import get_status


@click.command()
def main(args=None):
    """Console script for pygrowcube."""
    click.echo(get_status())
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
