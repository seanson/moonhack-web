# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "segno",
#     "structlog",
#     "typer",
# ]
# ///
"""Render the QR code used on the printable poster.

Defaults to the site's baseURL from config/_default/hugo.toml and writes an SVG
into assets/img/ for the poster layout to embed.

Usage: uv run scripts/make_qr.py [--url URL] [--out PATH]
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Annotated

import segno
import structlog
import typer

app = typer.Typer(add_completion=False)
log = structlog.get_logger()

REPO = Path(__file__).resolve().parent.parent
HUGO_CONFIG = REPO / "config/_default/hugo.toml"
DEFAULT_OUT = REPO / "assets/img/qr.svg"

# Moonhack 2026 palette: 'not black' on white, for print contrast.
DARK = "#131A35"
LIGHT = "#FFFFFF"


class QrError(Exception):
    """Raised when the QR code cannot be built."""


def site_base_url(config: Path = HUGO_CONFIG) -> str:
    """Return baseURL from the Hugo config."""
    try:
        with config.open("rb") as handle:
            settings = tomllib.load(handle)
    except FileNotFoundError as exc:
        raise QrError(f"No Hugo config at {config.relative_to(REPO)}") from exc

    base_url = settings.get("baseURL")
    if not base_url:
        raise QrError(f"No baseURL set in {config.relative_to(REPO)}")
    return str(base_url)


def write_qr(url: str, out: Path, scale: int = 8) -> None:
    """Write a QR code for url as an SVG at out."""
    out.parent.mkdir(parents=True, exist_ok=True)
    qr = segno.make(url, error="q")
    qr.save(out, kind="svg", scale=scale, dark=DARK, light=LIGHT)
    log.info("wrote qr", url=url, out=str(out.relative_to(REPO)), version=qr.version)


@app.command()
def main(
    url: Annotated[str | None, typer.Option(help="URL to encode (default: site baseURL)")] = None,
    out: Annotated[Path, typer.Option(help="SVG output path")] = DEFAULT_OUT,
    scale: Annotated[int, typer.Option(help="Module size in SVG units")] = 8,
) -> None:
    """Render the poster QR code."""
    try:
        write_qr(url or site_base_url(), out, scale)
    except QrError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
