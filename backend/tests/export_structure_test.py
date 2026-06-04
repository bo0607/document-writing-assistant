import json
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.writing_task_engine import WritingTaskEngine


def main() -> None:
    engine = WritingTaskEngine(BACKEND_ROOT / "data")
    task = engine.run_full(
        {
            "topic": "数字化工具对学习效率的影响",
            "genre": "议论文",
            "wordCount": 900,
            "style": "正式、逻辑清晰",
            "extraInstruction": "结合学习场景，观点积极但保持辩证",
        }
    )
    task = engine.summarize(task["taskId"])
    docx_result = engine.export_document(task["taskId"], "docx")
    txt_result = engine.export_document(task["taskId"], "txt")

    docx_path = Path(docx_result["file"]["path"])
    txt_path = Path(txt_result["file"]["path"])
    assert docx_path.exists()
    assert txt_path.exists()
    assert docx_path.stat().st_size > 0
    assert txt_path.stat().st_size > 0

    document = Document(docx_path)
    text = "\n".join(p.text for p in document.paragraphs)
    assert "数字化工具对学习效率的影响" in text
    assert "写作提纲" in text
    assert "正文" in text
    assert "摘要" in text

    section = document.sections[0]
    assert section.top_margin.inches == 1
    assert section.right_margin.inches == 1
    assert section.bottom_margin.inches == 1
    assert section.left_margin.inches == 1

    normal = document.styles["Normal"]
    assert normal.font.size.pt == 11
    east_asia = normal.element.rPr.rFonts.get(qn("w:eastAsia"))
    assert east_asia == "Microsoft YaHei"

    txt = txt_path.read_text(encoding="utf-8")
    assert "写作提纲" in txt
    assert "正文" in txt

    print(
        json.dumps(
            {
                "success": True,
                "docxPath": str(docx_path),
                "txtPath": str(txt_path),
                "docxSize": docx_path.stat().st_size,
                "txtSize": txt_path.stat().st_size,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

