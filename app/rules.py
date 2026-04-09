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


def _industry_gap_status(problem: str, root_answer: str, owner_answer: str) -> Tuple[bool, str]:
    merged = f"{problem or ''} {root_answer or ''} {owner_answer or ''}".lower()

    new_industry_signal = any(
        token in merged
        for token in ["新行业", "新领域", "新市场", "第二曲线", "开拓新市场"]
    )
    industry_knowhow_signal = any(
        token in merged
        for token in [
            "不懂行业",
            "没有行业经验",
            "不知道knowhow",
            "不知道 knowhow",
            "不清楚决策路径",
            "不清楚人脉关系",
            "不懂决策路径",
            "不懂人脉关系",
        ]
    )
    owner_stuck_signal = any(
        token in merged
        for token in ["自己不会做", "还在摸索", "分身乏术", "负责人也不会", "我也不会做"]
    )

    if (new_industry_signal and industry_knowhow_signal) or owner_stuck_signal:
        return True, "识别到新行业进入阶段的能力断层，核心短板在行业 knowhow、路径认知与关键资源理解。"
    return False, "未识别到明确的新行业能力断层信号。"


def _stage_problem_status(problem: str, root_answer: str, owner_answer: str) -> Tuple[bool, str]:
    merged = f"{problem or ''} {root_answer or ''} {owner_answer or ''}".lower()
    has_new_track = any(token in merged for token in ["新业务", "新赛道", "第二曲线"])
    has_early_market = any(token in merged for token in ["尚未进入市场", "没有成熟客户", "未进入市场", "还没有客户"])
    has_path_uncertainty = any(
        token in merged
        for token in ["不清楚行业决策链", "不清楚决策链", "不清楚路径", "不清楚人脉", "不清楚行业决策路径"]
    )
    has_resource_breakthrough = any(
        token in merged for token in ["需要认识人", "打开资源", "找突破口", "打开关系", "找关键关系"]
    )

    if (has_new_track and (has_early_market or has_path_uncertainty)) or has_resource_breakthrough:
        return True, "识别为行业进入阶段问题，核心在战略路径与关键关系尚未打通。"
    return False, "未识别到明确的行业进入阶段问题信号。"


def _role_definition_problem_status(problem: str, root_answer: str, owner_answer: str) -> Tuple[bool, str]:
    merged = f"{problem or ''} {root_answer or ''} {owner_answer or ''}".lower()
    execution_tokens = ["执行", "交付", "落地", "推进", "转化", "运营", "销售", "增长", "拓客", "线索"]
    management_tokens = ["管理", "带团队", "带人", "培养", "绩效", "流程", "机制", "体系", "组织"]
    strategy_tokens = ["战略", "规划", "bp", "决策支持", "策略", "路径设计", "业务模型", "方向"]

    category_count = 0
    if any(token in merged for token in execution_tokens):
        category_count += 1
    if any(token in merged for token in management_tokens):
        category_count += 1
    if any(token in merged for token in strategy_tokens):
        category_count += 1

    overload_pattern = (
        ("既要" in merged and "又要" in merged)
        or ("又要" in merged and "还要" in merged)
        or ("一个人" in merged and ("全部" in merged or "全都" in merged or "搞定" in merged))
        or ("什么都能做" in merged or "什么都要做" in merged)
    )
    early_stage_signal = any(token in merged for token in ["早期", "初创", "团队小", "刚起步"])
    jd_overload_signal = ("jd" in merged or "岗位描述" in merged or "职责描述" in merged) and category_count >= 2

    if category_count >= 3 or overload_pattern or (early_stage_signal and category_count >= 2) or jd_overload_signal:
        return True, "识别到岗位定义过载：岗位目标过多且边界不清，招聘目标需要先收敛。"
    return False, "未识别到明显的岗位定义过载信号。"


def _build_task_brief(
    *,
    problem: str,
    goal: str,
    responsibility_problem: bool,
    capability_problem: bool,
    industry_gap: bool,
    role_definition_problem: bool,
    recruitable_parts: List[str],
    non_recruitable_parts: List[str],
) -> Dict[str, object]:
    core_problem = problem or "当前关键结果无人稳定达成"
    core_goal = goal or "90天内把关键结果拉到可复盘、可持续的稳定状态"

    if role_definition_problem:
        key_capabilities = [
            "能围绕单一核心结果快速落地（如渠道拓展或销售转化）。",
            "在高节奏环境下稳定执行并持续复盘，不承担管理/BP/体系搭建职责。",
            "具备直接拿结果的前线能力，能在90天内形成可验证改善。",
        ]
    elif industry_gap:
        key_capabilities = [
            "在目标行业有一线实战经验，熟悉关键玩家、关键关系与进入节奏。",
            "清楚行业决策路径与成交逻辑，能快速定位首批突破口。",
            "具备行业资源理解与连接能力，能把关键关系转化为实际推进。",
        ]
    elif capability_problem:
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

    if role_definition_problem:
        problem_to_solve = "本次招聘只解决一个核心问题：补齐当前最关键结果的直接交付能力。"
        core_goal_text = "3个月内让单一核心结果显著改善（如有效线索、签约转化或渠道产出）。"
        owner_scope = "仅对当前最关键结果负责，不包含管理、BP或体系建设职责。"
        risk_warning = "若继续按“全能岗位”招聘，入职后会因目标过载导致结果分散、产出不稳定。"
    elif industry_gap:
        problem_to_solve = "本次招聘要解决新行业进入阶段缺少行业 knowhow、路径认知和关键资源理解的问题。"
        core_goal_text = "3个月内建立行业理解、关键客户路径认知和初步突破方案。"
        owner_scope = "对新行业进入路径、关键关系突破和落地推进负责。"
        risk_warning = "招聘只解决能力问题，不能替代责任定义。若没有行业型人才，仅靠内部摸索会导致试错周期过长。"
    else:
        problem_to_solve = f"本次招聘只解决一个问题：{core_problem}。"
        core_goal_text = f"3个月目标：{core_goal}，并形成可月度复盘的结果曲线。"
        owner_scope = "该岗位对最终业务结果负责，不以“完成动作数量”作为交付标准。"
        risk_warning = "；".join(risk_parts)

    return {
        "problem_to_solve": problem_to_solve,
        "core_goal": core_goal_text,
        "owner_scope": owner_scope,
        "key_capabilities": key_capabilities[:3],
        "milestones_30_60_90": {
            "30_days": f"搞清楚为什么现在{problem}做不出来，并接管这个结果",
            "60_days": "开始对关键结果负责，能明显看到改善趋势",
            "90_days": f"把{core_goal}跑通，形成稳定交付能力",
        },
        "non_recruitment_parts": non_recruitable_parts,
        "risk_warning": risk_warning,
    }


def make_decision(user_input: Dict[str, str]) -> Dict[str, object]:
    problem = user_input.get("current_problem", "").strip()
    goal = user_input.get("q1_goal", "").strip()
    owner_answer = user_input.get("q2_owner", "").strip()
    root_answer = user_input.get("q3_root", "").strip()
    team_size = user_input.get("team_size", "").strip()

    responsibility_problem, responsibility_reason = _responsibility_status(owner_answer, root_answer)
    capability_problem, capability_reason = _capability_status(problem, root_answer)
    industry_gap, industry_reason = _industry_gap_status(problem, root_answer, owner_answer)
    stage_problem, stage_reason = _stage_problem_status(problem, root_answer, owner_answer)
    role_definition_problem, role_definition_reason = _role_definition_problem_status(
        problem, root_answer, owner_answer
    )
    team_stage, team_reason = _team_context(team_size)

    if stage_problem:
        needs_hiring = False
        judgment = "当前问题不在于缺人，而在于尚未打通行业进入路径。"
        recruitable_parts = [
            "待行业进入路径清晰后，再评估是否需要补充执行或销售岗位。"
        ]
        non_recruitable_parts = [
            "当前阶段招聘销售或执行人员难以解决问题。",
            "路径未清晰前，新增执行人手会放大试错和沟通成本。",
        ]
        talent_profile: List[str] = []
        final_suggestion = "建议优先进行行业高层交流、建立认知和路径，再考虑招聘。"
    elif role_definition_problem:
        needs_hiring = True
        judgment = "当前问题不是缺人，而是岗位定义过载，需要先收敛招聘目标。"
        recruitable_parts = [
            "聚焦招聘一个能直接拿下当前关键结果的人，而不是“全能型岗位”。"
        ]
        non_recruitable_parts = [
            "管理、BP、体系建设不能一并塞进同一个新增岗位。",
            "岗位目标不收敛时，新增人手会被多线程任务稀释产出。",
        ]
        talent_profile = [
            f"负责的结果：仅对“{goal or '当前最关键业务结果'}”负责，并按周复盘。",
            "核心能力：具备与该结果直接相关的前线能力（如渠道拓展或销售转化）。",
            "成功标准：90天内单一核心结果出现稳定可验证提升。",
        ]
        final_suggestion = "建议先拆分岗位目标，只招聘当前最关键结果所需的人。"
    elif responsibility_problem and not capability_problem:
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
        if industry_gap:
            judgment = "当前问题优先不是责任问题，而是行业能力缺口，建议引入行业型人才。"
            recruitable_parts = [
                "补齐行业 knowhow、决策路径认知与关键资源理解，可直接缩短进入周期。",
                "引入懂行业的人，能快速建立关键客户路径并形成可执行突破方案。",
            ]
            non_recruitable_parts = [
                "内部职责划分仍需同步明确，否则行业人才入场后会被日常事务消耗。"
            ]
            talent_profile = [
                f"负责的结果：围绕“{goal or '新行业进入结果'}”完成路径打通并形成阶段性突破。",
                "核心能力：具备目标行业实战经验，熟悉关键关系与决策链路。",
                "成功标准：90天内完成行业路径认知搭建并推动首批可验证突破。",
            ]
            final_suggestion = "优先引入懂行业的人才，补齐行业 knowhow、关键路径和资源理解。"
        else:
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

    if team_stage == "small" and needs_hiring and not role_definition_problem:
        final_suggestion = "先明确负责人并验证最小岗位模型，再谨慎招聘1个关键位。"
    elif team_stage == "large" and responsibility_problem:
        final_suggestion = "先完成责任链路校准，再按能力缺口分批招聘。"

    non_recruitable_parts.append(f"组织阶段提醒：{team_reason}")
    non_recruitable_parts.append(
        f"推理依据：{stage_reason}；{role_definition_reason}；{industry_reason}；{responsibility_reason}；{capability_reason}"
    )

    task_brief = None
    if needs_hiring:
        task_brief = _build_task_brief(
            problem=problem,
            goal=goal,
            responsibility_problem=responsibility_problem,
            capability_problem=capability_problem,
            industry_gap=industry_gap,
            role_definition_problem=role_definition_problem,
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
