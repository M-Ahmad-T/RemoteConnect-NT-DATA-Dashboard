"""Verify missing-output launch paths; back up only the three generated files."""
import json
import subprocess
import sys
from pathlib import Path
from tempfile import mkdtemp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
NAMES = ("communities.csv", "infrastructure_nt.csv", "data_summary.json")


def remove_outputs_to_backup(label):
    backup = Path(mkdtemp(prefix=label, dir=ROOT / ".tmp")).resolve()
    assert ROOT in backup.parents
    for name in NAMES:
        source = (ROOT / "data/processed" / name).resolve()
        assert ROOT in source.parents
        if source.exists():
            source.rename(backup / name)
    return backup


def verify():
    summary = json.loads((ROOT / "data/processed/data_summary.json").read_text())
    assert summary["community_records"] == 188
    assert summary["infrastructure_operator_records_in_nt"] == 419
    assert summary["distinct_mapped_site_keys_in_nt"] == 405


def main():
    (ROOT / ".tmp").mkdir(exist_ok=True)
    for mode in ("batch", "direct"):
        backup = remove_outputs_to_backup(mode)
        try:
            if mode == "batch":
                subprocess.run(["cmd.exe", "/c", "run_app.bat", "--prepare-only"], cwd=ROOT, check=True)
            else:
                from streamlit.testing.v1 import AppTest
                app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
                assert not app.exception, [e.message for e in app.exception]
            verify()
            print(f"PASS: {mode} launch rebuilt all missing processed files", flush=True)
        finally:
            for name in NAMES:
                target = ROOT / "data/processed" / name
                if not target.exists() and (backup / name).exists():
                    (backup / name).rename(target)


if __name__ == "__main__":
    main()
