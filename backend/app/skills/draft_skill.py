import json
import re
from typing import Any

from app.core.text_metrics import count_text_units, target_word_range
from app.skills.base import WritingSkill


class DraftSkill(WritingSkill):
    name = "draft"
    description = "Compose a full draft from requirement and outline."

    def execute(
        self, context: dict[str, Any], instruction: str | None = None
    ) -> str:
        requirement = context.get("requirement", {})
        outline = context.get("outline", {})
        content = self.call_model(
            "你是一名熟悉不同中文文体的写作者。只输出成稿内容。",
            self._build_prompt(requirement, outline),
            temperature=0.8,
            max_tokens=self._max_tokens_for_requirement(requirement),
        )
        if content:
            return self._fit_word_count(
                self._prepare_draft(content),
                requirement,
                outline,
                allow_model_adjust=True,
            )
        return self._fit_word_count(
            self._fallback(requirement, outline),
            requirement,
            outline,
            allow_model_adjust=False,
        )

    def _build_prompt(
        self, requirement: dict[str, Any], outline: dict[str, Any]
    ) -> str:
        genre = str(requirement.get("genre") or "议论文")
        return (
            "请完成下面的中文写作任务。先在心里组织材料，再直接给出成稿。"
            "不要解释写作思路，也不要逐条复述内部要点。\n\n"
            "共同要求：\n"
            "- 让内容自然连贯，每一段都推进新的信息、经历或判断。\n"
            "- 避免把同一个观点换词重复；没有依据时不要编造具体数据、机构或人物。\n"
            "- 普通文章不需要额外标题；应用文或报告只有在任务确实需要时才保留称谓、落款或小标题。\n"
            "- 不要机械套用“引言、论述、总结”框架，但也不要为了避开格式而删除本来有意义的句子。\n"
            "- 只输出成稿，字数控制在目标字数的正负 10% 内。\n\n"
            f"文体写法：\n{self._genre_guidance(genre)}\n\n"
            f"写作要求：\n{json.dumps(requirement, ensure_ascii=False, indent=2)}\n\n"
            f"内部参考信息：\n{json.dumps(self._writing_plan(outline), ensure_ascii=False, indent=2)}"
        )

    def _genre_guidance(self, genre: str) -> str:
        if "记叙" in genre:
            return (
                "写成一段完整经历。用具体场景、动作、细节和人物感受推进事件，"
                "让认识变化从经历中自然出现，不要写成分点议论。"
            )
        if "说明" in genre:
            return (
                "把对象、过程或特点说清楚。按读者理解事物的顺序展开，"
                "语言准确、平实，重点是解释而不是表态。"
            )
        if "应用" in genre:
            return (
                "先根据补充要求判断具体场景。需要书信、通知、申请或倡议格式时再使用相应格式；"
                "其余内容以明确、可执行的沟通为主。"
            )
        if "报告" in genre:
            return (
                "围绕对象、观察或材料、分析和建议展开。可使用必要的小标题，"
                "但每一部分都要有具体信息，不能把报告写成空泛作文。"
            )
        if "总结" in genre:
            return (
                "围绕一个阶段的学习或工作过程，写清做了什么、有哪些收获、还存在哪些问题，"
                "并提出贴合实际的下一步安排。"
            )
        return (
            "提出明确但不过度绝对的判断，用现象、例子和分析彼此支撑。"
            "观点要在行文中逐渐展开，不要用固定的三段论标签。"
        )

    def _fallback(self, requirement: dict[str, Any], outline: dict[str, Any]) -> str:
        genre = str(requirement.get("genre") or "议论文")
        if "记叙" in genre:
            return self._narrative_fallback(requirement)
        if "说明" in genre:
            return self._expository_fallback(requirement, outline)
        if "应用" in genre:
            return self._practical_fallback(requirement)
        if "报告" in genre:
            return self._report_fallback(requirement)
        if "总结" in genre:
            return self._summary_fallback(requirement)
        return self._argument_fallback(requirement, outline)

    def _argument_fallback(
        self, requirement: dict[str, Any], outline: dict[str, Any]
    ) -> str:
        topic = self._topic(requirement)
        points = self._outline_points(outline)
        first = self._point_at(points, 0, "日常选择")
        second = self._point_at(points, 1, "实际体验")
        return "\n\n".join(
            [
                (
                    f"{topic}之所以值得讨论，不在于它听起来多么新鲜，而在于它已经"
                    f"进入了{first}这样的具体时刻。人们的习惯和判断会因此发生变化，"
                    "而这些变化往往要在反复经历之后才会显露出来。"
                ),
                (
                    f"从{second}可以看见，{topic}带来的并不只是表面的便利。"
                    "它有可能帮助人找到新的方法，也可能让人更依赖现成的答案。"
                    "差别并不取决于工具本身，而在于人是否仍愿意花时间理解问题。"
                ),
                (
                    f"讨论{topic}时，最需要避免的是把复杂问题说成非黑即白。"
                    "有些顾虑确实存在，但它们并不意味着拒绝变化；"
                    "有些好处也很明显，却不能代替独立思考和彼此沟通。"
                ),
                (
                    "真正有意义的选择，常常发生在细节里。多核对一次信息，"
                    "多询问一个人的实际处境，多给自己留一点思考的时间，"
                    "都能让看法不止停在口头上。"
                ),
            ]
        )

    def _narrative_fallback(self, requirement: dict[str, Any]) -> str:
        topic = self._topic(requirement)
        return "\n\n".join(
            [
                (
                    f"那天晚自习快结束时，教室里只剩下翻书和敲键盘的声音。"
                    f"我盯着一道题很久，脑子里却反复想到{topic}。"
                    "桌上的笔记写了又划，越想越觉得自己像是被一道看不见的墙挡住了。"
                ),
                (
                    "同桌见我迟迟没有动笔，轻声问我卡在哪里。我们把题目重新读了一遍，"
                    "又把已经做过的步骤一项项排开。后来，我试着借助新的学习工具寻找思路，"
                    "屏幕上出现的并不是现成答案，而是几个需要继续追问的提示。"
                ),
                (
                    "我一开始有些着急，恨不得立刻得到结论。可在同桌的提醒下，"
                    "我把每一步为什么这样做重新写下来。等最后一个环节终于想通时，"
                    "窗外已经黑透了，心里却忽然安静下来。"
                ),
                (
                    f"回家的路上，我没有再把{topic}看成一句很大的口号。"
                    "它更像一次具体的提醒，工具可以帮人打开一扇门，"
                    "但走进去、看清里面有什么，仍然需要自己一步一步完成。"
                ),
            ]
        )

    def _expository_fallback(
        self, requirement: dict[str, Any], outline: dict[str, Any]
    ) -> str:
        topic = self._topic(requirement)
        points = self._outline_points(outline)
        first = self._point_at(points, 0, "使用过程")
        second = self._point_at(points, 1, "实际作用")
        return "\n\n".join(
            [
                (
                    f"要理解{topic}，可以先从{first}看起。"
                    "它通常不是突然改变一件事，而是在使用、反馈和调整的过程中，"
                    "慢慢改变人们处理信息和安排时间的方式。"
                ),
                (
                    f"它的特点体现在{second}。不同的人会根据自己的需要选择不同功能，"
                    "于是同样的工具或方法，在不同场景里会呈现出不一样的效果。"
                ),
                (
                    "这种变化也有边界。输入的信息是否可靠、使用者是否理解结果、"
                    "使用环境是否合适，都会影响最终效果。因此，不能只看速度或表面结果。"
                ),
                (
                    f"把这些环节连起来看，{topic}就不再是一个抽象概念。"
                    "它既有明确的作用，也需要在具体情境中被合理使用。"
                ),
            ]
        )

    def _practical_fallback(self, requirement: dict[str, Any]) -> str:
        topic = self._topic(requirement)
        return "\n\n".join(
            [
                f"围绕{topic}，可以先把需要解决的实际问题说清楚。",
                "在安排具体措施时，应当明确参与对象、完成时间和可获得的支持，"
                "让每个人知道自己需要做什么，而不是只收到笼统的要求。",
                "执行过程中可以保留反馈渠道，及时发现不方便或不合理的地方，"
                "再根据实际情况调整安排。",
                "这样做既能让沟通更有效，也能让提出的计划真正落到日常行动中。",
            ]
        )

    def _report_fallback(self, requirement: dict[str, Any]) -> str:
        topic = self._topic(requirement)
        return "\n\n".join(
            [
                f"围绕{topic}进行初步整理时，可以看到不同使用者的关注点并不相同。"
                "有人关心效率，有人更在意过程中的可靠性和可控性。",
                "从已有现象看，相关做法能够带来一定便利，但实际效果会受到使用场景、"
                "信息质量和参与者习惯的共同影响。",
                "后续可以继续收集具体反馈，区分哪些问题来自工具本身，"
                "哪些问题来自使用方式，再有针对性地完善安排。",
                "在缺少充分材料时，应当保留判断的余地，避免把个别现象直接当成普遍结论。",
            ]
        )

    def _summary_fallback(self, requirement: dict[str, Any]) -> str:
        topic = self._topic(requirement)
        return "\n\n".join(
            [
                f"这一阶段围绕{topic}开展了资料整理、实践尝试和问题梳理。"
                "通过逐步推进，对相关内容的重点和难点有了更清楚的认识。",
                "已经完成的部分说明，前期安排能够提供基本支撑；"
                "同时也发现，一些细节还需要结合实际情况继续调整。",
                "目前的主要问题是对部分环节理解还不够深入，处理方式也需要进一步积累。"
                "这些问题将在后续学习和实践中逐步解决。",
                "下一阶段将继续补充材料、核对已有结论，并把注意力放在最需要改进的具体环节上。",
            ]
        )

    def _fit_word_count(
        self,
        draft: str,
        requirement: dict[str, Any],
        outline: dict[str, Any],
        allow_model_adjust: bool,
    ) -> str:
        draft = self._deduplicate_exact_paragraphs(draft)
        target = self._target_word_count(requirement)
        if not target:
            return draft

        lower, upper = target_word_range(target)
        current = count_text_units(draft)
        if lower <= current <= upper:
            return draft

        if allow_model_adjust:
            adjusted = self._model_adjust_word_count(draft, requirement)
            if adjusted:
                adjusted = self._prepare_draft(adjusted)
                adjusted_count = count_text_units(adjusted)
                if lower <= adjusted_count <= upper:
                    return self._deduplicate_exact_paragraphs(adjusted)

        if current > upper:
            # Keep the complete text when no model is available to shorten it naturally.
            return draft
        return self._extend_without_repeating(draft, requirement, outline, lower, upper)

    def _model_adjust_word_count(
        self, draft: str, requirement: dict[str, Any]
    ) -> str | None:
        target = self._target_word_count(requirement)
        if not target:
            return None
        lower, upper = target_word_range(target)
        action = "扩写" if count_text_units(draft) < lower else "压缩"
        prompt = (
            f"请将下面的{requirement.get('genre') or '中文'}成稿{action}到{target}字左右，"
            f"控制在{lower}到{upper}字之间。保留原文的文体、事件、观点和有效细节，"
            "通过补充或精简句子完成调整，不要删掉一整段后硬接，也不要加入解释。\n\n"
            f"原文：\n{draft}"
        )
        return self.call_model(
            "你是一名中文编辑，擅长在不破坏文体和内容完整性的前提下调整篇幅。",
            prompt,
            temperature=0.45,
            max_tokens=self._max_tokens_for_requirement(requirement),
        )

    def _extend_without_repeating(
        self,
        draft: str,
        requirement: dict[str, Any],
        outline: dict[str, Any],
        lower: int,
        upper: int,
    ) -> str:
        paragraphs = [part.strip() for part in draft.split("\n\n") if part.strip()]
        result = "\n\n".join(paragraphs)
        missing = max(0, lower - count_text_units(result))
        available_slots = max(1, 6 - len(paragraphs))
        chunk_target = max(80, (missing + available_slots - 1) // available_slots)
        additions: list[str] = []
        buffer = ""
        for addition in self._extension_paragraphs(requirement, outline):
            if count_text_units(result) >= lower:
                break
            candidate = f"{result}\n\n{addition}"
            if count_text_units(candidate) <= upper:
                result = candidate
                buffer = f"{buffer}{addition}"
                if (
                    len(additions) < available_slots - 1
                    and count_text_units(buffer) >= chunk_target
                ):
                    additions.append(buffer)
                    buffer = ""

        if buffer:
            additions.append(buffer)
        return self._deduplicate_exact_paragraphs(
            "\n\n".join(paragraphs + additions)
        )

    def _extension_paragraphs(
        self, requirement: dict[str, Any], outline: dict[str, Any]
    ) -> list[str]:
        topic = self._topic(requirement)
        genre = str(requirement.get("genre") or "议论文")
        points = self._outline_points(outline)
        point_a = self._point_at(points, 0, "日常细节")
        point_b = self._point_at(points, 1, "实际体验")
        supplement = self._supplementary_paragraphs(genre, topic)

        if "记叙" in genre:
            return [
                "我收好书包时，才发现刚才的着急已经慢慢退了下去。教室里的灯还亮着，桌上的草稿纸被风吹得轻轻翻动。",
                "后来再遇到类似的问题，我仍会先自己想一会儿。那次经历没有让我变得更快，却让我知道了什么时候该停下来把问题看清。",
                "第二天把这件事讲给同桌听时，他笑着说，原来答案不重要，重要的是我没有在最困难的时候放弃追问。",
                f"这段经历让我重新理解了{topic}。它留在记忆里的，不是某个结果，而是那一刻重新找回主动的感觉。",
                "走出教学楼时，夜风有些凉。我把纸折好放进书里，心里已经开始盘算下次该怎样把学习安排得更踏实。",
                "回头看去，很多看似过不去的时刻，其实只差一次耐心的梳理和一次愿意开口的交流。",
            ] + supplement

        if "说明" in genre:
            return [
                f"在{point_a}这一环节中，使用者通常先获得信息，再根据反馈作出调整。这个过程决定了后续效果是否稳定。",
                f"{point_b}能够帮助人们判断其实际作用。只有把使用前后的变化放在一起比较，才能得到较为准确的认识。",
                "此外，还应当注意不同环境带来的差异。设备条件、使用频率和个人基础不同，最终呈现的结果也会不同。",
                f"因此，理解{topic}需要同时看到它的特点、适用范围和使用条件，不能用单一标准概括全部情况。",
                "这些因素彼此关联，共同构成了一个完整过程。把过程说清楚，比简单地下结论更有助于形成可靠认识。",
            ] + supplement

        if "应用" in genre:
            return [
                "在具体执行前，可以先确认现有资源和可能遇到的困难，避免安排与实际条件脱节。",
                "对于需要协作的部分，应当把负责人和沟通方式提前明确下来，减少信息遗漏。",
                "完成后还可以根据反馈进行一次简短复盘，把有效做法保留下来。",
                f"这样，围绕{topic}提出的安排才能既有方向，也能在实际过程中不断完善。",
                "清楚、尊重并且可执行的表达，往往比堆砌口号更能获得理解和配合。",
            ] + supplement

        if "报告" in genre:
            return [
                f"进一步观察{point_a}后发现，参与者对同一问题的理解存在差异，这些差异需要在后续材料中继续核对。",
                "为提高结论的可靠性，可以补充访谈、记录或对比材料，并把不同来源的信息分开说明。",
                "对于暂时无法确认的部分，应当标明其局限，避免把推测写成既定事实。",
                f"围绕{topic}的后续工作，可以优先处理影响较大、反馈较集中的问题，再逐步完善其他环节。",
                "这种处理方式有助于把讨论从泛泛而谈转向可验证、可跟进的具体事项。",
            ] + supplement

        if "总结" in genre:
            return [
                "在推进过程中，有些安排比预想顺利，也有些问题需要反复调整。把这些差异记录下来，有助于下一阶段少走弯路。",
                "后续会继续把尚未完成的事项拆分成更具体的步骤，并及时检查完成情况。",
                f"围绕{topic}积累下来的经验，将作为下一步改进安排的重要参考。",
                "对暂时没有解决的问题保持跟进，比急于给出结论更重要。",
                "在不断复盘和调整中，原本零散的经验会逐渐形成更稳定的工作方法。",
            ] + supplement

        return [
            f"{point_a}往往最能检验一个判断是否可靠。离开具体处境，再有力的观点也容易变得空泛。",
            f"当人们认真对待{point_b}时，会发现许多看似简单的选择其实需要更多耐心。",
            "不同立场之间未必只能对立。把各自担心的部分说出来，反而更容易找到可以共同接受的做法。",
            f"这也是为什么，讨论{topic}时既要保持开放，也要保留必要的谨慎。",
            "有些答案不会立刻出现，但持续观察和诚实交流会让问题逐步变得清晰。",
            "真正成熟的判断，不是把所有问题说完，而是知道下一步应该从哪里继续。",
            "很多改变的意义，要等到一段时间后才看得更清楚。眼前看似微小的选择，往往会在之后形成不同的习惯。",
            "也有人担心新的做法会带来额外负担。这种担心值得认真对待，因为任何安排都需要照顾到不同人的能力和节奏。",
            "把问题说得更细，不会削弱观点，反而能让观点更经得起追问。越是重要的事情，越不能只靠一句漂亮的话来判断。",
            f"对于{topic}而言，保持好奇心很重要，保留核实和反思的习惯同样重要。两者并不冲突，反而能够互相支撑。",
            "当经验越来越多时，人们会发现，真正改变我们的往往不是某个单独的选择，而是一次次选择之间形成的联系。",
            "把注意力放回真实的人和真实的处境，讨论才会更有温度，也更容易找到能够持续下去的办法。",
            "没有哪一种做法适合所有人。承认差异，并在差异中寻找相互理解的可能，是比简单站队更有价值的事情。",
            "从这个角度看，许多看似遥远的话题其实和每个人的日常决定有关。认真对待这些决定，就是在认真对待未来。",
        ] + supplement

    def _supplementary_paragraphs(self, genre: str, topic: str) -> list[str]:
        if "记叙" in genre:
            return [
                "我没有立刻离开座位，而是把刚才卡住的地方又看了一遍。那些原本杂乱的符号，慢慢有了顺序。",
                "同桌没有催我，只是把他的草稿推过来。两张纸放在一起时，我才发现我们走了不同的路，却都在认真寻找答案。",
                "铃声响起后，走廊里一下热闹起来。我背着书包跟在人群后面，心里还在回想刚才那个转折。",
                "回到家后，我把问题重新整理在本子上，没有写下漂亮的结论，只记下哪些地方还想继续弄明白。",
                "几天以后再翻到那页笔记，我仍能想起当时的犹豫。正是那一点犹豫，让我没有轻易把思考交给别人。",
                f"关于{topic}，那天的经历没有给我一个标准答案，却让我学会把每一次帮助都当成继续前进的起点。",
                "有时成长并不是突然懂得很多道理，而是在一个普通的夜晚，愿意再多坚持几分钟。",
                "我后来才明白，真正留在心里的，是解决问题时那种重新获得掌控感的踏实。",
            ]

        if "说明" in genre:
            return [
                "从操作顺序看，使用者通常先接触信息，再进行筛选和判断，最后根据结果作出调整。每一步都会影响下一步。",
                "从适用范围看，有些方法适合处理重复性较强的任务，有些则更依赖使用者的经验，因此不能混为一谈。",
                "从反馈方式看，及时而清楚的反馈能够帮助人发现问题；反馈模糊时，使用者反而可能增加不必要的尝试。",
                "从长期效果看，稳定的使用习惯比短时间的高频使用更重要。只有形成合理节奏，作用才能持续显现。",
                f"这些特点说明，{topic}涉及多个相互关联的环节。理解其中任何一个环节，都不能脱离整体过程。",
                "在实际介绍时，既要说明它能够做什么，也要说明它在什么条件下才能发挥作用。",
                "这样得到的认识更接近事物本身，也更方便读者结合自己的情况作出判断。",
                "把复杂过程拆开说明，并不是把问题简单化，而是为了让每个关键因素都被看见。",
            ]

        if "应用" in genre:
            return [
                "提出安排时，还应当考虑接收者最关心的问题，用清楚的语言说明这样做能够带来什么实际帮助。",
                "遇到特殊情况时，可以预留调整空间，避免一套固定做法给参与者造成额外压力。",
                "必要的信息应当一次说明完整，包括时间、地点、联系人和需要准备的事项，减少来回确认。",
                "在正式实施后，可以用简短记录保留过程中的有效经验，为下一次安排提供参考。",
                f"这样处理{topic}，既能体现对实际问题的重视，也能让每一项要求更容易被理解和执行。",
                "良好的沟通不是单向发布，而是让参与者能够提出疑问，并得到及时回应。",
                "当安排与真实需求相互贴合时，原本复杂的协作也会变得更顺畅。",
                "把关键细节提前想清楚，能够减少后续的误会，让行动保持稳定的节奏。",
                "对于尚未考虑周全的情况，可以在执行中及时补充说明。与其假装安排已经完善，不如让调整过程保持公开和清楚。",
                "不同参与者的时间和条件并不完全相同，安排时留出适度弹性，能够让更多人顺利完成自己的部分。",
                "在沟通中说明理由，也能帮助接收者理解安排背后的考虑，从而把被动接受转变为主动配合。",
                "当每个人都知道问题出现后应当向谁反馈、怎样处理，实际执行就会少一些犹豫和等待。",
            ]

        if "报告" in genre:
            return [
                "在整理材料时，应当区分直接观察到的事实和基于事实作出的判断，两者不能混写。",
                "对不同来源的信息进行交叉核对，可以减少偶然情况带来的影响，也能让分析更有依据。",
                "发现问题后，不宜只描述现象，还应当继续追问问题出现的条件和可能造成的后果。",
                "提出建议时，可以优先选择成本可控、便于跟进的措施，并说明后续如何检验效果。",
                f"这些工作将帮助人们更完整地理解{topic}，也让后续决策建立在更可靠的材料上。",
                "报告的价值不在于使用多少抽象词，而在于能否把已经掌握的情况讲清楚。",
                "对于暂时没有答案的部分，保留问题本身也是一种负责任的表达。",
                "随着材料不断补充，原先的判断也应当允许被修正和完善。",
                "在分析过程中，还应当留意少数人的特殊体验。它们未必代表全部情况，却可能提示被多数材料忽略的问题。",
                "把问题按照影响程度排序，能够帮助后续工作先解决最紧迫的部分，避免资源被零散事项分散。",
                "对已经采取的措施进行阶段性检查，可以及时发现目标与实际结果之间的差距，并据此调整方向。",
                "这样形成的结论既有材料支撑，也能为下一阶段的具体行动提供清晰依据。",
            ]

        if "总结" in genre:
            return [
                "回顾这一阶段，最明显的收获是对工作节奏有了更具体的认识，知道哪些环节需要提前准备。",
                "在处理问题时，也逐渐学会把大任务拆成小步骤，通过记录减少遗漏和反复。",
                "仍有一些内容没有达到预期，这些不足提醒后续安排不能只追求速度，还要重视质量。",
                "下一步会先梳理最紧急的事项，再按轻重缓急逐项推进，避免目标过多而失去重点。",
                f"围绕{topic}的持续实践，使前期经验不再停留在零散感受，而能转化为可参考的做法。",
                "在新的阶段中，还会继续保留复盘习惯，把有效经验沉淀下来。",
                "对出现的问题及时调整，比等到最后集中处理更容易保持工作的稳定性。",
                "通过不断学习和完善，下一阶段的安排会更清楚，也更贴近实际需要。",
                "在回顾时，也会把没有达到预期的部分单独列出，分析是时间安排、准备不足还是方法选择的问题。",
                "对已经有效的做法，会继续保留并适当推广；对效果不明显的环节，则及时停止投入并寻找新的方案。",
                "下一步的计划会设置清晰的小目标，通过阶段性检查确认是否真正取得进展。",
                "这样既能保持持续推进，也能在出现偏差时尽早发现并作出调整。",
            ]

        return [
            "现实中的情况很少完全符合预设。愿意根据新的信息调整原有判断，才能避免把问题看得过于简单。",
            "许多分歧来自关注重点不同。把不同重点摆出来讨论，比急于证明谁对谁错更有助于解决问题。",
            "人们既需要看到眼前的变化，也要留意那些暂时不容易察觉的影响，它们往往决定了选择能否长久。",
            f"因此，围绕{topic}形成观点时，既要有自己的立场，也要给事实和他人的经验留下位置。",
            "当判断能够经受具体情境的检验，它才不会只是一句听起来正确的话。",
            "保持思考并不意味着拒绝行动，而是在行动之前知道自己为什么这样做。",
            "有些问题没有一次解决的办法，但认真处理每一个细节，会让事情朝着更好的方向发展。",
            "把复杂性看清之后，人们反而更容易找到真正可行的下一步。",
        ]

    def _topic(self, requirement: dict[str, Any]) -> str:
        return str(requirement.get("topic") or "这一主题").strip()

    def _outline_points(self, outline: dict[str, Any]) -> list[str]:
        points: list[str] = []
        for section in outline.get("sections") or []:
            for point in section.get("points") or []:
                text = str(point).strip()
                text = re.sub(r"^[^：:]{1,18}[：:]\s*", "", text)
                if text and text not in points:
                    points.append(text)
        return points

    def _point_at(self, points: list[str], index: int, default: str) -> str:
        return points[index] if index < len(points) else default

    def _writing_plan(self, outline: dict[str, Any]) -> dict[str, Any]:
        return {
            "centralIdea": outline.get("thesis") or "",
            "referencePoints": self._outline_points(outline),
        }

    def _prepare_draft(self, content: str) -> str:
        return self.assembler.normalize_paragraphs(content)

    def _deduplicate_exact_paragraphs(self, draft: str) -> str:
        kept: list[str] = []
        seen: set[str] = set()
        for paragraph in draft.split("\n\n"):
            text = paragraph.strip()
            fingerprint = re.sub(r"\s+", "", text)
            if text and fingerprint not in seen:
                kept.append(text)
                seen.add(fingerprint)
        return "\n\n".join(kept)

    def _target_word_count(self, requirement: dict[str, Any]) -> int | None:
        try:
            target = int(requirement.get("wordCount") or 0)
        except (TypeError, ValueError):
            return None
        return target if target > 0 else None

    def _max_tokens_for_requirement(self, requirement: dict[str, Any]) -> int:
        target = self._target_word_count(requirement) or 1000
        return max(1200, min(8000, int(target * 2.2)))
