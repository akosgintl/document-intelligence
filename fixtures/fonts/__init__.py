"""The vendored typefaces every fixture page is drawn with.

`ImageFont.load_default()` cannot draw a Hungarian document: `Ő`, `Ö`, `Ű`, `Ü`, `é` and `á`
all come out as the *same* `.notdef` box (verified byte-for-byte, #46). So the faces are
vendored here rather than taken from the host — a fixture must render identically on any
machine, and a missing system font would silently degrade a page to boxes rather than fail.

DejaVu is redistributable under the Bitstream Vera license; see `LICENSE.txt` beside the
`.ttf` files. Mono exists for the machine-readable zone, which is OCR-B on a real document.
"""

from functools import cache
from pathlib import Path

from PIL import ImageFont

FONT_DIR = Path(__file__).parent

SANS = FONT_DIR / "DejaVuSans.ttf"
SANS_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
MONO = FONT_DIR / "DejaVuSansMono.ttf"


@cache
def _load(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def sans(size: int) -> ImageFont.FreeTypeFont:
    """The face for field labels and body text."""
    return _load(SANS, size)


def sans_bold(size: int) -> ImageFont.FreeTypeFont:
    """The face for titles and field values — real documents set values heavier than labels."""
    return _load(SANS_BOLD, size)


def mono(size: int) -> ImageFont.FreeTypeFont:
    """The face for the machine-readable zone."""
    return _load(MONO, size)
