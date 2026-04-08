from typing import Dict


def _normalize_text(data: Dict[str, str]) -> str:
    parts = [
        data.get("company_stage", ""),
        data.get("team_size", ""),
        data.get("current_problem", ""),
        data.get("hiring_reason", ""),
        data.get("q1_owner", ""),
        data.get("q2_timeline", ""),
        data.get("q3_alternative", ""),
    ]
    return " ".join(str(p).strip().lower() for p in parts if str(p).strip())


def diagnose(data: dict) -> dict:
    text = _normalize_text(data)
    problem = str(data.get("current_problem", "")).strip()
    reason = str(data.get("hiring_reason", "")).strip()
    owner_answer = str(data.get("q1_owner", "")).strip()
    timeline_answer = str(data.get("q2_timeline", "")).strip()
    alternative_answer = str(data.get("q3_alternative", "")).strip()

    has_org_signal = (
        "职责不清" in text
        or "分工混乱" in text
        or "边界不清" in text
        or "重复" in text
    )
    has_gap_signal = (
        "没人负责" in text
        or "没人做" in text
        or "无人承接" in text
        or "空缺" in text
    )
    has_management_signal = (
        "老板很累" in text
        or "推不动" in text
        or "没人推进" in text
        or "管理" in text and "跟不上" in text
    )

    if has_org_signal:
        essence = "更可能是组织分工问题，而不是单纯缺人。"
        why_like_hiring = (
            f"你提到“{problem or '当前问题'}”与“{reason or '招聘动机'}”，"
            "看起来像人手不足，但信号更偏向职责边界和协作关系未理顺。"
        )
    elif has_management_signal:
        essence = "更可能是管理机制问题，直接招人可能放大低效。"
        why_like_hiring = (
            f"你提到“{problem or '当前问题'}”，同时出现推进乏力或管理承压迹象，"
            "因此容易把管理压力误判为编制不足。"
        )
    elif has_gap_signal or ("没有" in owner_answer and "负责人" in owner_answer):
        essence = "更可能存在职责缺口，确实有新增承接位的可能。"
        why_like_hiring = (
            f"你给出的场景“{problem or '当前问题'}”与“{reason or '招聘动机'}”显示已有事项无人稳定负责，"
            "因此会出现明显“缺人感”。"
        )
    else:
        essence = "当前信息显示是“人、流程、职责”混合问题，不能只按缺人处理。"
        why_like_hiring = (
            f"你提到“{reason or '需要招人'}”，但追问信息尚未形成单一根因，"
            "因此看起来像缺人，实则可能是多因素叠加。"
        )

    hiring_condition = "当问题是长期且持续增长、且目前明确无人稳定承接关键结果时。"
    if "短期" in timeline_answer:
        hiring_risk = "你已提示是短期问题，若立即正式招聘，可能造成固定成本和人岗错配风险。"
    else:
        hiring_risk = "若目标和职责边界不清，招到人后仍可能出现“有人但问题没解”的风险。"

    internal_condition = "当团队内有可重排工作、可明确责任人，且问题可通过节奏和分工优化改善时。"
    internal_risk = "若只调整分工但不给权限与考核，容易变成“名义负责、实际无人负责”。"

    outsource_condition = "当需求阶段性波动、专业能力短期缺口明显，且可被清晰拆分成交付任务时。"
    if "没有" in alternative_answer or "不可能" in alternative_answer:
        outsource_risk = "你目前认为替代方案空间有限，若强行外包可能增加沟通和质量返工成本。"
    else:
        outsource_risk = "外包能缓冲压力，但若验收标准不清，容易形成进度和质量失控。"

    if has_gap_signal and "长期" in timeline_answer:
        priority_action = "先定义该岗位的结果责任与90天目标，再小范围启动招聘验证。"
    elif has_org_signal or has_management_signal:
        priority_action = "先做一次职责与推进机制梳理，用两周验证内部调整效果，再决定是否招聘。"
    else:
        priority_action = "先把问题拆成“必须新增”与“可替代处理”两类，再按轻重缓急组合动作。"

    return {
        "problem_essence": essence,
        "why_feels_like_hiring": why_like_hiring,
        "paths": [
            {
                "name": "招聘",
                "condition": hiring_condition,
                "risk": hiring_risk,
            },
            {
                "name": "内部调整",
                "condition": internal_condition,
                "risk": internal_risk,
            },
            {
                "name": "外包/临时方案",
                "condition": outsource_condition,
                "risk": outsource_risk,
            },
        ],
        "priority_action": priority_action,
    }
