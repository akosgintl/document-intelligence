import io

import pypdfium2 as pdfium

PDF_CONTENT_TYPE = "application/pdf"
IMAGE_CONTENT_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
SUPPORTED_CONTENT_TYPES = IMAGE_CONTENT_TYPES | {PDF_CONTENT_TYPE}

# Points-per-inch (PDF canvas unit) to target DPI, per pypdfium2's `render(scale=...)` contract.
_RENDER_SCALE = 144 / 72


class RenderError(Exception):
    """Raised when Submission bytes can't be read as a supported PDF/image."""


def render_pages(content_bytes: bytes, content_type: str) -> list[tuple[bytes, str]]:
    """Render every Page of a Submission down to Page images, in order.

    An image passes through unchanged as a single Page. Each of a PDF's pages is
    rasterized to PNG independently — page-level splitting (#23) happens downstream,
    against however many Pages this produces.
    """
    if content_type in IMAGE_CONTENT_TYPES:
        return [(content_bytes, content_type)]

    if content_type != PDF_CONTENT_TYPE:
        raise RenderError(f"Unsupported content type: {content_type}")

    try:
        pdf = pdfium.PdfDocument(content_bytes)
    except pdfium.PdfiumError as exc:
        raise RenderError(f"Could not read PDF: {exc}") from exc
    try:
        pages: list[tuple[bytes, str]] = []
        for pdf_page in pdf:
            bitmap = pdf_page.render(scale=_RENDER_SCALE)
            image = bitmap.to_pil()
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            pages.append((buffer.getvalue(), "image/png"))
        return pages
    finally:
        pdf.close()
