"""Console script for pygrowcube."""
import asyncio
import sys
import click
from pygrowcube.pygrowcube import get_status
import logging


@click.command()
@click.argument("ip_address")
@click.option(
    "--timeout",
    "-t",
    default=15,
    show_default=True,
    help="Maximum time to wait for readings in seconds. GrowCube typically sends readings within 10s.",
)
@click.option(
    "--connect",
    "-c",
    is_flag=True,
    default=False,
    help="Validate connection to GrowCube without waiting for sensor readings",
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Send log output to stdout"
)
@click.option("--debug", "-d", is_flag=True, default=False, help="Enable debug logging")
@click.option(
    "--log", "-l", is_flag=True, default=False, help="Send log output to a file"
)
@click.option(
    "--logfilename",
    "-f",
    default="pygrowcube.log",
    help="Specify a filename to use for log output",
)
def main(timeout, ip_address, connect, verbose, debug, log, logfilename):
    """Get the status and sensor readings of the GrowCube device at IP_ADDRESS"""
    loglevel = logging.INFO if verbose else logging.ERROR
    loglevel = logging.DEBUG if debug else loglevel
    if log:
        logging.basicConfig(
            filename=logfilename,
            level=loglevel,
            format="%(asctime)s %(levelname)s:%(message)s",
        )
    else:
        logging.basicConfig(
            stream=sys.stdout,
            level=loglevel,
            format="%(asctime)s %(levelname)s:%(message)s",
        )

    status = asyncio.run(get_status(ip_address, timeout, not connect))

    click.echo(str(status))
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
