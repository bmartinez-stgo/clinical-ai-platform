from __future__ import annotations

from typing import Any
from uuid import uuid4

import fitz


def extract_document_payload(file_bytes: bytes, filename: str, content_type: str | None) -> dict[str, Any]:
    document = fitz.open(stream=file_bytes, filetype="pdf")
    metadata = document.metadata or {}
    pages: list[dict[str, Any]] = []

    for index, page in enumerate(document, start=1):
        raw_blocks = page.get_text("blocks")
        sorted_blocks = sorted(raw_blocks, key=lambda item: (round(item[1], 2), round(item[0], 2)))
        blocks = []
        page_lines: list[str] = []

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

        pages.append(
            {
                "page_number": index,
                "text": page_text,
                "lines": page_lines,
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
