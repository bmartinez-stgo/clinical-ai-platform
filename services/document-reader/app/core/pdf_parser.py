from __future__ import annotations

from typing import Any
from uuid import uuid4

import fitz


def extract_document_payload(file_bytes: bytes, filename: str, content_type: str | None) -> dict[str, Any]:
    document = fitz.open(stream=file_bytes, filetype="pdf")
    metadata = document.metadata or {}
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(document, start=1):
        page_text = page.get_text("text").strip()
        blocks = []

        for block in page.get_text("blocks"):
            block_text = block[4].strip()
            if not block_text:
                continue
            blocks.append(
                {
                    "text": block_text,
                    "bbox": [round(value, 2) for value in block[:4]],
                }
            )

        pages.append(
            {
                "page_number": index,
                "text": page_text,
                "blocks": blocks,
            }
        )

    full_text = "\n\n".join(page["text"] for page in pages if page["text"]).strip()
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]

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
