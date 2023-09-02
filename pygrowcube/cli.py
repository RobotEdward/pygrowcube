"""Console script for pygrowcube."""
import sys
import click
from pygrowcube.pygrowcube import GetStatus 

@click.command()
def main(args=None):
    """Console script for pygrowcube."""
    click.echo(GetStatus());
    click.echo("message")
    click.echo("Replace this message by putting your code into " "pygrowcube.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
