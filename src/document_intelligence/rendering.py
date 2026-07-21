import io
from collections.abc import Iterator
from contextlib import contextmanager

import pypdfium2 as pdfium

PDF_CONTENT_TYPE = "application/pdf"
IMAGE_CONTENT_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
SUPPORTED_CONTENT_TYPES = IMAGE_CONTENT_TYPES | {PDF_CONTENT_TYPE}

# Points-per-inch (PDF canvas unit) to target DPI, per pypdfium2's `render(scale=...)` contract.
_RENDER_SCALE = 144 / 72


class RenderError(Exception):
    """Raised when Submission bytes can't be read as a supported PDF/image."""


@contextmanager
def _open_pdf(content_bytes: bytes, content_type: str) -> Iterator[pdfium.PdfDocument]:
    """Validate `content_type` is PDF and open it, closing it on exit either way."""
    if content_type != PDF_CONTENT_TYPE:
        raise RenderError(f"Unsupported content type: {content_type}")

    try:
        pdf = pdfium.PdfDocument(content_bytes)
    except pdfium.PdfiumError as exc:
        raise RenderError(f"Could not read PDF: {exc}") from exc
    try:
        yield pdf
    finally:
        pdf.close()


def count_pages(content_bytes: bytes, content_type: str) -> int:
    """Cheaply determine a Submission's page count without rasterizing any Page image — used
    to enforce the page-count limit (#25) synchronously at submission time, before the more
    expensive full render in `render_pages`.
    """
    if content_type in IMAGE_CONTENT_TYPES:
        return 1

    with _open_pdf(content_bytes, content_type) as pdf:
        return len(pdf)


def render_pages(content_bytes: bytes, content_type: str) -> list[tuple[bytes, str]]:
    """Render every Page of a Submission down to Page images, in order.

    An image passes through unchanged as a single Page. Each of a PDF's pages is
    rasterized to PNG independently — page-level splitting (#23) happens downstream,
    against however many Pages this produces.
    """
    if content_type in IMAGE_CONTENT_TYPES:
        return [(content_bytes, content_type)]

    with _open_pdf(content_bytes, content_type) as pdf:
        pages: list[tuple[bytes, str]] = []
        for pdf_page in pdf:
            bitmap = pdf_page.render(scale=_RENDER_SCALE)
            image = bitmap.to_pil()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            pages.append((buffer.getvalue(), "image/png"))
        return pages
