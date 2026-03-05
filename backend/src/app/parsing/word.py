from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class WordReference:
    doc_id: str
    location: str
    excerpt: str


@dataclass(frozen=True)
class MappingCandidate:
    heading_path: str
    level: str
    expected_value_text: str
    reference: WordReference


@dataclass(frozen=True)
class WordParseResult:
    heading_paths: list[str]
    mapping_candidates: list[MappingCandidate]
    references: list[WordReference]


def parse_word_file(*, file_path: str | Path, doc_id: str) -> WordParseResult:
    return parse_word_bytes(file_bytes=Path(file_path).read_bytes(), doc_id=doc_id)


def parse_word_bytes(*, file_bytes: bytes, doc_id: str) -> WordParseResult:
    document_xml = _extract_document_xml(file_bytes)
    root = ET.fromstring(document_xml)
    body = root.find("w:body", WORD_NS)
    if body is None:
        return WordParseResult(heading_paths=[], mapping_candidates=[], references=[])

    heading_stack: list[str] = []
    heading_paths: list[str] = []
    references: list[WordReference] = []
    mapping_candidates: list[MappingCandidate] = []
    table_index = 0

    for child in body:
        local_name = child.tag.split("}")[-1]
        if local_name == "p":
            paragraph_text = _paragraph_text(child)
            if not paragraph_text:
                continue
            heading_level = _heading_level(child, paragraph_text)
            if heading_level is not None:
                _update_heading_stack(heading_stack, heading_level, paragraph_text)
                heading_path = " > ".join(heading_stack)
                heading_paths.append(heading_path)
                references.append(
                    WordReference(
                        doc_id=doc_id,
                        location=f"heading:{heading_path}",
                        excerpt=paragraph_text,
                    )
                )
        elif local_name == "tbl":
            table_index += 1
            heading_path = " > ".join(heading_stack)
            table_rows = _extract_table_rows(child)
            for row_index, row in enumerate(table_rows, start=1):
                if len(row) < 2:
                    continue
                level = row[0].strip()
                value_text = row[1].strip()
                if not level or not _contains_number(value_text):
                    continue
                ref = WordReference(
                    doc_id=doc_id,
                    location=f"table:{table_index}:row:{row_index}:heading:{heading_path}",
                    excerpt=f"{level} -> {value_text}",
                )
                mapping_candidates.append(
                    MappingCandidate(
                        heading_path=heading_path,
                        level=level,
                        expected_value_text=value_text,
                        reference=ref,
                    )
                )
                references.append(ref)

    return WordParseResult(
        heading_paths=heading_paths,
        mapping_candidates=mapping_candidates,
        references=references,
    )


def _extract_document_xml(file_bytes: bytes) -> bytes:
    with zipfile.ZipFile(BytesIO(file_bytes)) as archive:
        return archive.read("word/document.xml")


def _paragraph_text(paragraph: ET.Element) -> str:
    text_nodes = paragraph.findall(".//w:t", WORD_NS)
    return "".join(node.text or "" for node in text_nodes).strip()


def _heading_level(paragraph: ET.Element, text: str) -> int | None:
    style = paragraph.find("./w:pPr/w:pStyle", WORD_NS)
    if style is not None:
        val = style.attrib.get(f"{{{WORD_NS['w']}}}val", "")
        if val.startswith("Heading"):
            suffix = val.replace("Heading", "")
            if suffix.isdigit():
                return int(suffix)
    if re.match(r"^\d+(\.\d+)*\s+", text):
        return text.split(" ", 1)[0].count(".") + 1
    return None


def _update_heading_stack(stack: list[str], level: int, heading_text: str) -> None:
    while len(stack) >= level:
        stack.pop()
    stack.append(heading_text)


def _extract_table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in table.findall("./w:tr", WORD_NS):
        cells: list[str] = []
        for tc in tr.findall("./w:tc", WORD_NS):
            cell_text = "".join(node.text or "" for node in tc.findall(".//w:t", WORD_NS)).strip()
            cells.append(cell_text)
        rows.append(cells)
    return rows


def _contains_number(text: str) -> bool:
    return bool(re.search(r"\d", text))
