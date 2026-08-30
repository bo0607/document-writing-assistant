import json
import os
import sys
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

for key in (
    "WRITING_ASSISTANT_BASE_URL",
    "WRITING_ASSISTANT_API_KEY",
    "WRITING_ASSISTANT_MODEL",
    "OPENAI_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
):
    os.environ.pop(key, None)

from app.core.text_metrics import count_text_units, target_word_range
from app.core.writing_task_engine import WritingTaskEngine


def assert_word_count(task: dict, target: int) -> dict:
    content = task["draft"]["content"]
    actual = count_text_units(content)
    lower, upper = target_word_range(target)
    assert lower <= actual <= upper, {
        "target": target,
        "actual": actual,
        "lower": lower,
        "upper": upper,
    }
    assert task["draft"]["wordCount"] == actual
    return {
        "target": target,
        "actual": actual,
        "lower": lower,
        "upper": upper,
    }


def main() -> None:
    results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = WritingTaskEngine(Path(tmp_dir))
        for target in (500, 800, 1200):
            task = engine.run_full(
                {
                    "topic": "人工智能对学习方式的影响",
                    "genre": "议论文",
                    "wordCount": target,
                    "style": "正式、逻辑清晰",
                    "extraInstruction": "观点积极，结合现实例子",
                }
            )
            results.append(assert_word_count(task, target))

    print(json.dumps({"success": True, "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
