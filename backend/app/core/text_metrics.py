import re


COUNTABLE_RE = re.compile(r"[\u3400-\u9fffA-Za-z0-9]")


def count_text_units(text: str) -> int:
    """Approximate Chinese essay word count.

    Chinese writing assignments usually mean visible Chinese characters rather
    than model tokens. This counter ignores whitespace and punctuation, and
    counts CJK characters, letters, and digits.
    """

    return len(COUNTABLE_RE.findall(text or ""))


def target_word_range(target: int, tolerance: float = 0.1) -> tuple[int, int]:
    lower = max(1, int(target * (1 - tolerance)))
    upper = max(lower, int(target * (1 + tolerance)))
    return lower, upper


def is_within_target(text: str, target: int, tolerance: float = 0.1) -> bool:
    lower, upper = target_word_range(target, tolerance)
    count = count_text_units(text)
    return lower <= count <= upper


def truncate_to_count(text: str, max_count: int) -> str:
    if max_count <= 0:
        return ""

    kept: list[str] = []
    count = 0
    for char in text:
        if COUNTABLE_RE.match(char):
            if count >= max_count:
                break
            count += 1
        kept.append(char)

    result = "".join(kept).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = result.rstrip("，、；：,. ")
    if result and result[-1] not in "。！？.!?":
        result += "。"
    return result
