"""Restart-safe JSONL I/O helpers.

Padrão usado por todas as tasks de Phase B que processam laudos
um a um e podem ser interrompidas: append por linha com flush+fsync,
e resume via leitura dos report_ids já presentes.
"""

import json
import os
from pathlib import Path


def append_jsonl(path: str, record: dict) -> None:
    """Append a single record to JSONL file with fsync for crash safety.

    Cria diretório pai se necessário. Cada record vira uma linha JSON.
    flush + fsync garantem que se o processo for morto via kill -9 ou
    reboot, o que foi escrito está em disco.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done_ids(path: str, id_field: str = "report_id") -> set[str]:
    """Load report_ids already processed. Tolerates corrupt last line.

    Se o processo morreu durante uma escrita parcial, a última linha
    pode estar truncada. Pulamos linhas com JSON inválido ou sem o
    id_field — não falha.
    """
    if not Path(path).exists():
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done.add(rec[id_field])
            except (json.JSONDecodeError, KeyError):
                continue  # skip corrupt/incomplete
    return done
