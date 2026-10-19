from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedSection:
    heading: str
    text: str
    source_locator: str


@dataclass(frozen=True)
class ParsedDocument:
    title: str
    sections: list[ParsedSection]


def _clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n")).strip()


def parse_document(filename: str, content: bytes) -> ParsedDocument:
    name = filename.rsplit("/", 1)[-1]
    stem = name.rsplit(".", 1)[0] or name
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else "txt"
    text = content.decode("utf-8-sig", errors="replace")
    if suffix == "csv":
        reader = csv.DictReader(io.StringIO(text))
        rows: list[ParsedSection] = []
        for row_number, row in enumerate(reader, start=2):
            fields = [f"{key}: {value}" for key, value in row.items() if key and value]
            rows.append(ParsedSection(stem, _clean("\n".join(fields)), f"row:{row_number}"))
        return ParsedDocument(stem, rows)
    lines = text.replace("\r\n", "\n").splitlines()
    sections: list[ParsedSection] = []
    heading = stem
    buffer: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal buffer, start_line
        cleaned = _clean("\n".join(buffer))
        if cleaned:
            sections.append(ParsedSection(heading, cleaned, f"line:{start_line}-{end_line}"))
        buffer = []

    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            flush(line_number - 1)
            heading = _clean(match.group(1))
            start_line = line_number
        else:
            if not buffer:
                start_line = line_number
            buffer.append(line)
    flush(len(lines))
    if not sections and text.strip():
        sections.append(ParsedSection(stem, _clean(text), f"line:1-{len(lines)}"))
    title = sections[0].heading if sections else stem
    return ParsedDocument(title, sections)
