from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def _pdf_safe(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def markdown_to_pdf(md_path: Path, pdf_path: Path, title: str | None = None) -> None:
    """Create a small text-only PDF without third-party dependencies."""
    raw_lines = md_path.read_text(encoding="utf-8").splitlines()
    lines = []
    if title:
        lines.append(title)
        lines.append("")
    for line in raw_lines:
        clean = re.sub(r"`([^`]+)`", r"\1", line)
        clean = clean.replace("#", "").replace("*", "")
        lines.append(clean[:105])

    page_height = 792
    margin_x = 54
    y_start = 742
    line_height = 13
    lines_per_page = 52
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)] or [[]]

    objects: list[str] = []
    page_ids: list[int] = []

    def add_object(body: str) -> int:
        objects.append(body)
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object("")
    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for page_lines in pages:
        stream_lines = ["BT", f"/F1 10 Tf", f"{margin_x} {y_start} Td"]
        for index, line in enumerate(page_lines):
            if index:
                stream_lines.append(f"0 -{line_height} Td")
            stream_lines.append(f"({_pdf_safe(line)}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        content_id = add_object(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
        page_id = add_object(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 {page_height}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] "
        f"/Count {len(page_ids)} >>"
    )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    output = ["%PDF-1.4\n"]
    offsets = [0]
    current = len(output[0].encode("latin-1"))
    for object_id, body in enumerate(objects, start=1):
        chunk = f"{object_id} 0 obj\n{body}\nendobj\n"
        offsets.append(current)
        output.append(chunk)
        current += len(chunk.encode("latin-1"))
    xref_offset = current
    output.append(f"xref\n0 {len(objects) + 1}\n")
    output.append("0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.append(f"{offset:010d} 00000 n \n")
    output.append(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    pdf_path.write_bytes("".join(output).encode("latin-1"))
