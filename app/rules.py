from __future__ import annotations

import re
from typing import Dict, List, Tuple


def build_restatement(user_input: Dict[str, str]) -> str:
    company_stage = user_input.get("company_stage", "").strip() or "阶段信息暂未说明"
    team_size = user_input.get("team_size", "").strip() or "团队规模暂未说明"
    problem = user_input.get("current_problem", "").strip() or "你当前的问题描述还比较笼统"

    return (
        "我先复述你当前的情况，确认我们对问题理解一致：\n"
        f"- 企业阶段：{company_stage}。\n"
        f"- 团队规模：{team_size}。\n"
        f"- 核心问题：{problem}。\n"
        "接下来我会从“责任是否闭环 + 能力是否具备 + 团队阶段是否匹配”三个维度做判断。"
    )


def _extract_team_size(team_size_text: str) -> int | None:
    match = re.search(r"\d+", team_size_text or "")
    if not match:
        return None
    return int(match.group())


def _team_context(team_size_text: str) -> Tuple[str, str]:
    size = _extract_team_size(team_size_text)
    if size is None:
        return "unknown", "组织上下文暂不完整，建议结合实际编制再复核。"
    if size <= 15:
        return "small", "当前团队偏小，优先靠责任聚焦与一人多能解决问题。"
    if size <= 80:
        return "growing", "当前团队处于扩张阶段，职责清晰与能力补位要同步设计。"
    return "large", "当前团队规模较大，先校准责任链路再扩编更稳健。"


def _responsibility_status(owner_answer: str, root_answer: str) -> Tuple[bool, str]:
    owner_text = (owner_answer or "").strip()
    root_text = (root_answer or "").strip()
    merged = f"{owner_text} {root_text}".lower()

    has_owner_signal = (
        "有" in owner_text and "负责" in owner_text and "没" not in owner_text and "不" not in owner_text
    ) or any(token in merged for token in ["明确负责人", "责任明确", "有人盯结果", "owner明确"])

    no_owner_signal = any(
        token in merged
        for token in ["没人负责", "没有负责人", "责任不清", "职责不清", "都在负责", "老板自己盯", "扯皮"]
    )

    if no_owner_signal and not has_owner_signal:
        return True, "责任信号显示结果没有稳定负责人，责任链路未闭环。"
    if has_owner_signal and not no_owner_signal:
        return False, "责任信号显示已有明确负责人。"
    return True, "责任描述存在冲突或模糊，按“责任未闭环”处理更安全。"


def _capability_status(problem: str, root_answer: str) -> Tuple[bool, str]:
    problem_text = (problem or "").lower()
    root_text = (root_answer or "").lower()

    capability_gap_signal = any(
        token in f"{problem_text} {root_text}"
        for token in [
            "没人会做",
            "不会做",
            "缺经验",
            "缺能力",
            "专业能力不足",
            "需要专家",
            "技术短板",
            "方法不会",
        ]
    )

    no_capability_gap_signal = any(
        token in root_text
        for token in ["不是能力问题", "有能力完成", "能够完成", "主要是没人负责", "只是责任问题"]
    )

    if capability_gap_signal and not no_capability_gap_signal:
        return True, "能力信号显示团队缺少完成结果所需的关键能力。"
    if no_capability_gap_signal and not capability_gap_signal:
        return False, "能力信号显示并非能力缺口，核心矛盾不在技能。"
    return False, "能力描述暂无明确缺口信号，按“能力可内部承接”处理。"


def _build_task_brief(
    *,
    problem: str,
    goal: str,
    responsibility_problem: bool,
    capability_problem: bool,
    recruitable_parts: List[str],
    non_recruitable_parts: List[str],
) -> Dict[str, object]:
    core_problem = problem or "当前关键结果无人稳定达成"
    core_goal = goal or "90天内把关键结果拉到可复盘、可持续的稳定状态"

    if capability_problem:
        key_capabilities = [
            "能独立拆解目标并把结果推进到落地，不依赖高频盯人。",
            "在复杂协作场景下对结果负责，能把跨部门阻塞快速打通。",
            "用数据复盘过程与结果，能持续优化方法而不是重复救火。",
        ]
    else:
        key_capabilities = [
            "在既定目标下稳定交付，不把执行问题上抛给老板。",
            "能将模糊任务转化为清晰路径并按节奏闭环。",
            "对结果负责到最后一公里，出现偏差能主动修正。",
        ]

    risk_parts = ["招聘只解决能力问题，不能替代责任定义。"]
    if responsibility_problem:
        risk_parts.append("当前责任边界不清，直接招聘会出现“招到人但没人真正对结果负责”的风险。")
    else:
        risk_parts.append("即使责任清晰，若目标口径和验收标准不具体，也会造成新人与团队反复返工。")

    return {
        "problem_to_solve": f"本次招聘只解决一个问题：{core_problem}。",
        "core_goal": f"3个月目标：{core_goal}，并形成可月度复盘的结果曲线。",
        "owner_scope": "该岗位对最终业务结果负责，不以“完成动作数量”作为交付标准。",
        "key_capabilities": key_capabilities[:3],
        "milestones_30_60_90": {
            "30_days": f"搞清楚为什么现在{problem}做不出来，并接管这个结果",
            "60_days": "开始对关键结果负责，能明显看到改善趋势",
            "90_days": f"把{core_goal}跑通，形成稳定交付能力",
        },
        "non_recruitment_parts": non_recruitable_parts,
        "risk_warning": "；".join(risk_parts),
    }


def make_decision(user_input: Dict[str, str]) -> Dict[str, object]:
    problem = user_input.get("current_problem", "").strip()
    goal = user_input.get("q1_goal", "").strip()
    owner_answer = user_input.get("q2_owner", "").strip()
    root_answer = user_input.get("q3_root", "").strip()
    team_size = user_input.get("team_size", "").strip()

    responsibility_problem, responsibility_reason = _responsibility_status(owner_answer, root_answer)
    capability_problem, capability_reason = _capability_status(problem, root_answer)
    team_stage, team_reason = _team_context(team_size)

    if responsibility_problem and not capability_problem:
        needs_hiring = False
        judgment = "当前问题不建议优先招聘，更本质是责任问题。"
        recruitable_parts = [
            "在责任人明确后，若仍有长期无人承接的具体结果位，可再补招聘。"
        ]
        non_recruitable_parts = [
            "结果责任未锁定，单纯加人无法形成闭环。",
            "汇报关系与决策权未明确前，新人很难真正对结果负责。",
        ]
        talent_profile: List[str] = []
        final_suggestion = "先确定唯一结果负责人和考核口径，再决定是否招聘。"
    elif capability_problem and not responsibility_problem:
        needs_hiring = True
        judgment = "当前问题可以通过招聘优先解决，核心矛盾是能力缺口。"
        recruitable_parts = [
            "关键任务缺少可独立交付的人，适合通过招聘补齐能力。",
            "该结果目标具备持续性，适合设置长期岗位承接。",
        ]
        non_recruitable_parts = [
            "招聘前仍需明确目标边界与协作接口，避免入职后反复返工。"
        ]
        talent_profile = [
            f"负责的结果：对“{goal or '关键业务结果'}”负责，并按月复盘结果。",
            "核心能力：具备相关场景的实战经验，可独立推进跨部门协作。",
            "成功标准：90天内接管关键任务并交付可量化改进。",
        ]
        final_suggestion = "立即启动招聘，但先把结果指标与汇报关系写清。"
    else:
        needs_hiring = True
        judgment = "这是责任问题与能力问题并存的混合问题，应先定责任再招聘。"
        recruitable_parts = [
            "在责任人锁定后，针对能力短板补充关键岗位，能直接提升交付质量。"
        ]
        non_recruitable_parts = [
            "责任链路未闭环前，新增人手会先放大协作成本。",
            "如果不先定义谁对结果负责，能力再强的人也难稳定出结果。",
        ]
        talent_profile = [
            f"负责的结果：围绕“{goal or '关键业务结果'}”承担端到端交付责任。",
            "核心能力：既能专业交付，又能推动流程与责任协同。",
            "成功标准：60-90天内完成职责接管并让核心指标稳定改善。",
        ]
        final_suggestion = "本周先明确结果负责人，再启动针对能力缺口的招聘。"

    if team_stage == "small" and needs_hiring:
        final_suggestion = "先明确负责人并验证最小岗位模型，再谨慎招聘1个关键位。"
    elif team_stage == "large" and responsibility_problem:
        final_suggestion = "先完成责任链路校准，再按能力缺口分批招聘。"

    non_recruitable_parts.append(f"组织阶段提醒：{team_reason}")
    non_recruitable_parts.append(f"推理依据：{responsibility_reason}；{capability_reason}")

    task_brief = None
    if needs_hiring:
        task_brief = _build_task_brief(
            problem=problem,
            goal=goal,
            responsibility_problem=responsibility_problem,
            capability_problem=capability_problem,
            recruitable_parts=recruitable_parts,
            non_recruitable_parts=non_recruitable_parts,
        )

    return {
        "judgment": judgment,
        "recruitable_parts": recruitable_parts,
        "non_recruitable_parts": non_recruitable_parts,
        "needs_hiring": needs_hiring,
        "talent_profile": talent_profile,
        "final_suggestion": final_suggestion,
        "task_brief": task_brief,
    }
