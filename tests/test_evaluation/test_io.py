"""Tests para src/evaluation/io.py — helpers JSONL restart-safe."""

import json

from src.evaluation.io import append_jsonl, load_done_ids


def test_append_jsonl_creates_file(tmp_path):
    """Append cria arquivo + diretório pai se não existirem."""
    path = tmp_path / "subdir" / "out.jsonl"
    append_jsonl(str(path), {"report_id": "RPT_001", "score": 9})

    assert path.exists()
    content = path.read_text(encoding="utf-8").strip()
    assert json.loads(content) == {"report_id": "RPT_001", "score": 9}


def test_append_jsonl_appends_multiple(tmp_path):
    """Cada chamada adiciona uma linha; arquivo cresce monotonicamente."""
    path = tmp_path / "out.jsonl"
    append_jsonl(str(path), {"report_id": "RPT_001"})
    append_jsonl(str(path), {"report_id": "RPT_002"})
    append_jsonl(str(path), {"report_id": "RPT_003"})

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    assert json.loads(lines[0])["report_id"] == "RPT_001"
    assert json.loads(lines[2])["report_id"] == "RPT_003"


def test_load_done_ids_skips_corrupt(tmp_path):
    """Última linha truncada (crash mid-write) é ignorada graciosamente."""
    path = tmp_path / "out.jsonl"
    path.write_text(
        '{"report_id": "RPT_001"}\n'
        '{"report_id": "RPT_002"}\n'
        '{corrupt',
        encoding="utf-8",
    )
    assert load_done_ids(str(path)) == {"RPT_001", "RPT_002"}


def test_load_done_ids_missing_file(tmp_path):
    """Arquivo inexistente retorna set vazio (não levanta)."""
    path = tmp_path / "does_not_exist.jsonl"
    assert load_done_ids(str(path)) == set()


def test_load_done_ids_skips_record_without_id_field(tmp_path):
    """Record sem report_id é pulado, não derruba o load."""
    path = tmp_path / "out.jsonl"
    path.write_text(
        '{"report_id": "RPT_001"}\n'
        '{"some_other_field": "noise"}\n'
        '{"report_id": "RPT_002"}\n',
        encoding="utf-8",
    )
    assert load_done_ids(str(path)) == {"RPT_001", "RPT_002"}


def test_unicode_preserved(tmp_path):
    """Append + load preserva acentos PT-br (ensure_ascii=False)."""
    path = tmp_path / "out.jsonl"
    append_jsonl(str(path), {"report_id": "RPT_X", "texto": "espiculação"})

    raw = path.read_text(encoding="utf-8").strip()
    # ensure_ascii=False mantém o caractere acentuado, não ção
    assert "espiculação" in raw
