import io

import pypdfium2 as pdfium

PDF_CONTENT_TYPE = "application/pdf"
IMAGE_CONTENT_TYPES = frozenset({"image/png", "image/jpeg", "image/webp"})
SUPPORTED_CONTENT_TYPES = IMAGE_CONTENT_TYPES | {PDF_CONTENT_TYPE}

# Points-per-inch (PDF canvas unit) to target DPI, per pypdfium2's `render(scale=...)` contract.
_RENDER_SCALE = 144 / 72


class RenderError(Exception):
    """Raised when Submission bytes can't be read as a supported PDF/image, or a PDF isn't
    single-page — multi-page splitting isn't implemented yet (#23)."""


def count_pdf_pages(pdf_bytes: bytes) -> int:
    """Open a PDF far enough to report its page count, without rendering anything."""
    try:
        pdf = pdfium.PdfDocument(pdf_bytes)
    except pdfium.PdfiumError as exc:
        raise RenderError(f"Could not read PDF: {exc}") from exc
    try:
        return len(pdf)
    finally:
        pdf.close()


def render_single_page(content_bytes: bytes, content_type: str) -> tuple[bytes, str]:
    """Render a single-page Submission down to one Page image.

    Images pass through unchanged. A PDF's sole page is rasterized to PNG.
    """
    if content_type in IMAGE_CONTENT_TYPES:
        return content_bytes, content_type

    if content_type != PDF_CONTENT_TYPE:
        raise RenderError(f"Unsupported content type: {content_type}")

    try:
        pdf = pdfium.PdfDocument(content_bytes)
    except pdfium.PdfiumError as exc:
        raise RenderError(f"Could not read PDF: {exc}") from exc
    try:
        if len(pdf) != 1:
            raise RenderError(f"Expected a single-page PDF, got {len(pdf)} pages")
        bitmap = pdf[0].render(scale=_RENDER_SCALE)
        image = bitmap.to_pil()
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue(), "image/png"
    finally:
        pdf.close()
