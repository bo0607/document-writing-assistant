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
from app.core.model_adapter import ModelAdapter
from app.core.result_assembler import ResultAssembler
from app.skills.draft_skill import DraftSkill


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = WritingTaskEngine(Path(tmp_dir))
        tasks = {
            genre: engine.run_full(
                {
                    "topic": "人工智能对学习方式的影响",
                    "genre": genre,
                    "wordCount": 800,
                    "style": "正式、自然",
                    "extraInstruction": "结合大学生日常学习展开",
                }
            )
            for genre in ("议论文", "记叙文", "说明文", "应用文", "报告", "总结")
        }

    for genre, task in tasks.items():
        content = task["draft"]["content"]
        lower, upper = target_word_range(800)
        assert lower <= count_text_units(content) <= upper, (genre, content)
        assert "方面，围绕" not in content, (genre, content)
        paragraph_count = len([part for part in content.split("\n\n") if part.strip()])
        assert 4 <= paragraph_count <= 6, (genre, paragraph_count, content)

    assert "那天晚自习" in tasks["记叙文"]["draft"]["content"]
    assert "要理解人工智能对学习方式的影响" in tasks["说明文"]["draft"]["content"]
    assert "这一阶段" in tasks["总结"]["draft"]["content"]

    cleaner = DraftSkill(ModelAdapter(base_url="", api_key=""), ResultAssembler())
    formatted = (
        "学习更高效：人工智能能帮助学生快速找到适合自己的练习。\n\n"
        "总结：技术是否有价值，仍取决于学习者是否保持判断。"
    )
    cleaned = cleaner._prepare_draft(formatted)
    assert cleaned == formatted

    repeated = "同一段内容。\n\n同一段内容。"
    deduplicated = cleaner._deduplicate_exact_paragraphs(repeated)
    assert len(deduplicated.split("\n\n")) == 1
    print("Natural draft test passed.")


if __name__ == "__main__":
    main()
