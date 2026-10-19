# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "structlog",
#     "typer",
# ]
# ///
"""Generate Moonhack name card PDFs from a text file of names.

Reads one name per line (blank lines and lines starting with # are skipped) and
lays them out 8 per A4 page, 2 columns by 4 rows. Each card is 90 x 60mm with
rounded corners and an 8mm gap between cards, so there is room to cut round the
corners and a home printer can reach every edge. Rendered with headless
Chrome from the art in assets/img/, so Hugo does not need to be running.

Usage: uv run scripts/make_badges.py [NAMES.txt] [--out PATH] [--blank N]
       NAMES.txt defaults to .work/names.txt
Env:   CHROME overrides the Chrome binary path.

Keep the names file under .work/ (gitignored). It lists children by name.
"""

from __future__ import annotations

import base64
import html
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import structlog
import typer

app = typer.Typer(add_completion=False)
log = structlog.get_logger()

REPO = Path(__file__).resolve().parent.parent
IMG = REPO / "assets/img"
DEFAULT_NAMES = REPO / ".work/names.txt"
DEFAULT_OUT = REPO / ".work/data/moonhack-2026-badges-a4.pdf"
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

PER_PAGE = 8
EYEBROW = "1st Kings Langley Scouts"
TITLE = "Moonhack 2026"

# Light card, so the white star is left out. Positions are for a 90 x 60mm card.
STARS = [
    ("star-lavender.svg", "5mm", "6mm", "4.5mm"),
    ("star-peachy-pink.svg", "6mm", "78mm", "3.6mm"),
    ("star-moon-blue.svg", "16mm", "81mm", "2.8mm"),
    ("star-deep-pink.svg", "17mm", "6mm", "2.8mm"),
]


class BadgeError(Exception):
    """Raised when badges cannot be generated."""


@dataclass(frozen=True)
class Assets:
    """Art embedded as data URIs so the HTML is self-contained."""

    landscape: str
    shield: str
    buggy: str
    stars: dict[str, str]


def data_uri(path: Path) -> str:
    """Return path as a base64 data URI."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise BadgeError(f"Missing art file: {path.relative_to(REPO)}") from exc
    mime = {".svg": "image/svg+xml", ".png": "image/png"}[path.suffix]
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def load_assets() -> Assets:
    """Load every image the cards use."""
    return Assets(
        landscape=data_uri(IMG / "moon-landscape.png"),
        shield=data_uri(IMG / "shield-guy.png"),
        buggy=data_uri(IMG / "buggy.svg"),
        stars={name: data_uri(IMG / "stars" / name) for name, *_ in STARS},
    )


def read_names(path: Path) -> list[str]:
    """Read one name per line, skipping blanks and # comments."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise BadgeError(f"No names file at {path}") from exc
    names = [line.strip() for line in lines]
    return [name for name in names if name and not name.startswith("#")]


def name_size_mm(name: str) -> float:
    """Pick a font size that keeps the name on the card."""
    length = len(name)
    if length <= 9:
        return 11.5
    if length <= 14:
        return 9.5
    if length <= 20:
        return 7.2
    return 5.8


def card_html(name: str, assets: Assets) -> str:
    """Render one 100 x 70mm card."""
    stars = "".join(
        f'<img class="star" src="{assets.stars[file]}" alt="" '
        f'style="top:{top};left:{left};width:{size}">'
        for file, top, left, size in STARS
    )
    label = html.escape(name)
    size = name_size_mm(name)
    return f"""
    <div class="card">
      {stars}
      <p class="eyebrow">{EYEBROW}</p>
      <p class="title">{TITLE}</p>
      <div class="name"><span style="font-size:{size}mm">{label}</span></div>
      <div class="landscape" style="background-image:url('{assets.landscape}')"></div>
      <img class="mascot shield" src="{assets.shield}" alt="">
      <img class="mascot buggy" src="{assets.buggy}" alt="">
    </div>"""


CSS = """
@page { size: A4 portrait; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 210mm; height: 297mm; padding: 16mm 11mm; display: grid;
  grid-template-columns: repeat(2, 90mm); grid-template-rows: repeat(4, 60mm);
  gap: 8mm; justify-content: center; align-content: center; break-after: page; }
.page:last-child { break-after: auto; }
.card { position: relative; width: 90mm; height: 60mm; overflow: hidden;
  border-radius: 5mm; text-align: center; color: #2b2f55;
  background: linear-gradient(180deg, #ece9fb 0%, #f6e9f8 100%);
  outline: 0.25mm solid #cfc9ea; outline-offset: -0.125mm; }
.star { position: absolute; height: auto; opacity: 0.85; }
.eyebrow { position: absolute; top: 5mm; left: 0; right: 0; margin: 0;
  font-size: 2.3mm; font-weight: 700; letter-spacing: 0.26em;
  text-transform: uppercase; color: #8277cc; }
.title { position: absolute; top: 9.5mm; left: 0; right: 0; margin: 0;
  font-size: 6.2mm; font-weight: 900; letter-spacing: -0.02em; line-height: 1;
  color: #2f2a73; }
.name { position: absolute; top: 18mm; left: 7mm; right: 7mm; height: 19mm;
  display: flex; align-items: center; justify-content: center;
  background: #fff; border-radius: 3.5mm; padding: 0 3mm; color: #1f2347;
  box-shadow: 0 0 0 0.25mm #ddd8f1; }
.name span { font-weight: 900; line-height: 1; letter-spacing: -0.02em;
  text-wrap: balance; }
.landscape { position: absolute; left: 0; right: 0; bottom: 0; height: 21mm;
  background-size: 100% auto; background-position: top center;
  background-repeat: no-repeat; opacity: 0.55; }
.mascot { position: absolute; height: auto; }
.shield { left: 5mm; bottom: 13mm; width: 9.5mm; opacity: 0.9; }
.buggy { right: 7mm; bottom: 13.5mm; width: 15mm; opacity: 0.9; }
"""


def build_html(names: list[str], assets: Assets) -> str:
    """Lay names out 8 per page."""
    pages = []
    for start in range(0, len(names), PER_PAGE):
        cards = "".join(card_html(n, assets) for n in names[start : start + PER_PAGE])
        pages.append(f'<div class="page">{cards}</div>')
    body = "".join(pages)
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'


def render_pdf(markup: str, out: Path, chrome: str) -> None:
    """Print the markup to a PDF with headless Chrome."""
    if not Path(chrome).exists():
        raise BadgeError(f"Chrome not found at {chrome} (set CHROME=/path/to/chrome)")

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "badges.html"
        source.write_text(markup, encoding="utf-8")
        try:
            subprocess.run(
                [
                    chrome,
                    "--headless",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-pdf-header-footer",
                    "--virtual-time-budget=5000",
                    f"--print-to-pdf={out}",
                    source.as_uri(),
                ],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            raise BadgeError(f"Chrome failed: {exc.stderr.decode(errors='replace')[-300:]}") from exc


@app.command()
def main(
    names_file: Annotated[
        Path, typer.Argument(help="Text file, one name per line")
    ] = DEFAULT_NAMES,
    out: Annotated[Path, typer.Option(help="PDF output path")] = DEFAULT_OUT,
    blank: Annotated[int, typer.Option(help="Extra blank write-in cards to append")] = 0,
) -> None:
    """Generate name cards, 8 per A4 page, from a names file."""
    try:
        names = read_names(names_file)
        if not names and not blank:
            raise BadgeError(f"No names in {names_file}")
        names += [""] * blank
        render_pdf(
            build_html(names, load_assets()),
            out,
            os.environ.get("CHROME", DEFAULT_CHROME),
        )
    except BadgeError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    pages = -(-len(names) // PER_PAGE)
    log.info("wrote badges", cards=len(names), pages=pages, out=str(out))


if __name__ == "__main__":
    app()
