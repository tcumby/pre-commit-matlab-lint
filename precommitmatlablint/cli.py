"""
Command-line interface for pre-commit-matlab-lint.


"""

from __future__ import annotations

import logging
import time

import typer

from precommitmatlablint import __title__, __version__, __copyright__, metadata


logger = logging.getLogger(__package__)
cli = typer.Typer()


def info(n_seconds: float = 0.01, verbose: bool = False) -> None:
    """
    Get info about pre-commit-matlab-lint.

    Args:
        n_seconds: Number of seconds to wait between processing.
        verbose: Output more info
    
    Example:
        To call this, run: ::
        
            from testme import info
            info(0.02)
    """
    typer.echo(f"{__title__} version {__version__}, {__copyright__}")
    if verbose:
        typer.echo(str(metadata.__dict__))
    total = 0
    with typer.progressbar(range(100)) as progress:
        for value in progress:
            time.sleep(n_seconds)
            total += 1
    typer.echo(f"Processed {total} things.")


if __name__ == "__main__":
    cli()
