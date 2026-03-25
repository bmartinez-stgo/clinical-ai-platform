from __future__ import annotations

from typing import Any
from uuid import uuid4
import base64
from io import BytesIO

import fitz
from PIL import Image

from app.core.config import get_settings

settings = get_settings()


def build_layout_lines(page: fitz.Page) -> list[str]:
    words = page.get_text("words", sort=True)
    if not words:
        return []

    rows: list[list[tuple[float, float, str]]] = []
    current_row: list[tuple[float, float, str]] = []
    current_y: float | None = None

    for x0, y0, x1, _y1, text, *_rest in words:
        if current_y is None or abs(y0 - current_y) <= 2.5:
            current_row.append((x0, x1, text))
            current_y = y0 if current_y is None else current_y
            continue

        rows.append(current_row)
        current_row = [(x0, x1, text)]
        current_y = y0

    if current_row:
        rows.append(current_row)

    layout_lines: list[str] = []
    for row in rows:
        row = sorted(row, key=lambda item: item[0])
        parts: list[str] = []
        previous_x1: float | None = None

        for x0, x1, text in row:
            if previous_x1 is not None:
                gap = x0 - previous_x1
                if gap > 70:
                    parts.append("        ")
                elif gap > 28:
                    parts.append("    ")
                else:
                    parts.append(" ")
            parts.append(text)
            previous_x1 = x1

        line = "".join(parts).strip()
        if line:
            layout_lines.append(line)

    return layout_lines


def resize_png_bytes(image_bytes: bytes, max_dimension: int) -> bytes:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    width, height = image.size
    longest_edge = max(width, height)

    if longest_edge <= max_dimension:
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue()

    scale = max_dimension / float(longest_edge)
    resized = image.resize(
        (max(1, int(width * scale)), max(1, int(height * scale))),
        Image.Resampling.LANCZOS,
    )
    buffer = BytesIO()
    resized.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def extract_document_payload(file_bytes: bytes, filename: str, content_type: str | None) -> dict[str, Any]:
    document = fitz.open(stream=file_bytes, filetype="pdf")
    metadata = document.metadata or {}
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(document, start=1):
        raw_blocks = page.get_text("blocks")
        sorted_blocks = sorted(raw_blocks, key=lambda item: (round(item[1], 2), round(item[0], 2)))
        blocks = []
        page_lines: list[str] = []
        layout_lines = build_layout_lines(page)

        for block in sorted_blocks:
            block_text = block[4].strip()
            if not block_text:
                continue

            block_lines = [line.strip() for line in block_text.splitlines() if line.strip()]
            if not block_lines:
                continue

            blocks.append(
                {
                    "text": block_text,
                    "lines": block_lines,
                    "bbox": [round(value, 2) for value in block[:4]],
                }
            )
            page_lines.extend(block_lines)

        page_text = "\n".join(page_lines).strip()
        pixmap = page.get_pixmap(dpi=settings.render_dpi, alpha=False)
        png_bytes = resize_png_bytes(pixmap.tobytes("png"), settings.max_image_dimension)

        pages.append(
            {
                "page_number": index,
                "text": page_text,
                "lines": page_lines,
                "layout_lines": layout_lines,
                "image_base64": base64.b64encode(png_bytes).decode("ascii"),
                "mime_type": "image/png",
                "blocks": blocks,
            }
        )

    full_text = "\n\n".join(page["text"] for page in pages if page["text"]).strip()
    lines = [line for page in pages for line in page["lines"]]

    return {
        "document_id": str(uuid4()),
        "filename": filename,
        "content_type": content_type or "application/pdf",
        "page_count": len(pages),
        "character_count": len(full_text),
        "full_text": full_text,
        "lines": lines,
        "metadata": {
            "title": metadata.get("title") or None,
            "author": metadata.get("author") or None,
            "subject": metadata.get("subject") or None,
            "creator": metadata.get("creator") or None,
            "producer": metadata.get("producer") or None,
        },
        "pages": pages,
    }


def extract_image_payload(file_bytes: bytes, filename: str, content_type: str) -> dict[str, Any]:
    normalized_image_bytes = resize_png_bytes(file_bytes, settings.max_image_dimension)
    encoded = base64.b64encode(normalized_image_bytes).decode("ascii")
    return {
        "document_id": str(uuid4()),
        "filename": filename,
        "content_type": content_type,
        "page_count": 1,
        "character_count": 0,
        "full_text": "",
        "lines": [],
        "metadata": {},
        "pages": [
            {
                "page_number": 1,
                "text": "",
                "lines": [],
                "layout_lines": [],
                "image_base64": encoded,
                "mime_type": "image/png",
                "blocks": [],
            }
        ],
    }
