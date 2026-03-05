from helpers import make_word_bytes

from app.parsing.word import parse_word_bytes


def test_word_parser_extracts_heading_paths_mapping_and_references() -> None:
    result = parse_word_bytes(file_bytes=make_word_bytes(), doc_id="doc-word-1")

    assert result.heading_paths == ["4 Display", "4 Display > 4.3 Backlight Mapping"]
    assert len(result.mapping_candidates) == 2

    first = result.mapping_candidates[0]
    assert first.heading_path == "4 Display > 4.3 Backlight Mapping"
    assert first.level == "L1"
    assert first.expected_value_text == "500"
    assert first.reference.doc_id == "doc-word-1"
    assert "table:1:row:2" in first.reference.location
