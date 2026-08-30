import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    tests = [
        root / "tests" / "http_smoke_test.py",
        root / "tests" / "export_structure_test.py",
        root / "tests" / "word_count_test.py",
        root / "tests" / "natural_draft_test.py",
    ]
    for test in tests:
        print(f"Running {test.name}...")
        subprocess.run([sys.executable, str(test)], cwd=root.parent, check=True)
    print("All tests passed.")


if __name__ == "__main__":
    main()
