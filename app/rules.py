"""规则引擎：用于判断“是否应该先招聘”。

第一版采用关键词 + 权重 的可解释规则，
后续可以替换成更复杂的策略（例如模型评分），
但对外保持 diagnose(text) 接口不变。
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class RuleConfig:
    """单类规则配置。"""

    category: str
    essence: str
    hire_recommendation: str
    reason_template: str
    advice: List[str]
    keywords: List[str]


RULES: Dict[str, RuleConfig] = {
    "hiring": RuleConfig(
        category="招聘问题",
        essence="当前问题更像“职责缺口/承接缺口”，存在真实人力缺位。",
        hire_recommendation="建议",
        reason_template="识别到职责缺失或新增业务无人承接信号：{hits}",
        advice=[
            "先明确该岗位的结果责任与边界，再启动招聘。",
            "把“必须新增”的工作与“可优化/可外包”的工作拆开。",
            "设定30-60-90天目标，避免“招了但没人管”。",
        ],
        keywords=["没人", "无人", "缺人", "新增业务", "没人接", "负责人", "承接", "空缺", "招人"],
    ),
    "organization": RuleConfig(
        category="组织结构问题",
        essence="当前问题更像组织分工与结构设计失衡，而非单纯人手不足。",
        hire_recommendation="不建议",
        reason_template="识别到组织冗余/分工混乱信号：{hits}",
        advice=[
            "先梳理组织层级与汇报关系，减少重叠岗位。",
            "明确每个团队的唯一责任目标，避免多人对同一结果负责。",
            "在组织边界清晰后，再评估是否补充关键岗位。",
        ],
        keywords=["组织冗余", "架构混乱", "分工混乱", "重叠", "重复", "职责不清", "层级过多"],
    ),
    "process": RuleConfig(
        category="流程问题",
        essence="当前问题更像流程效率瓶颈，新增人员未必能解决核心约束。",
        hire_recommendation="不建议",
        reason_template="识别到流程低效/交付卡点信号：{hits}",
        advice=[
            "先定位关键流程瓶颈（例如审批、交付、跨部门协同）。",
            "建立SOP与节奏看板，先提升单人产能。",
            "若流程优化后仍存在稳定产能缺口，再考虑招聘。",
        ],
        keywords=["流程", "低效", "交付跟不上", "审批慢", "卡点", "协同低效", "扯皮"],
    ),
    "role_design": RuleConfig(
        category="角色设计问题",
        essence="当前问题更像角色定义不清或岗位设计失衡。",
        hire_recommendation="暂不确定",
        reason_template="识别到角色边界不清信号：{hits}",
        advice=[
            "先定义关键角色的职责边界、决策权与协作接口。",
            "把“岗位名”改成“结果责任”，再判断是否缺编。",
            "必要时先试行代理负责人机制，验证岗位必要性。",
        ],
        keywords=["角色不清", "岗位不清", "定位不清", "没人负责", "职责边界", "负责什么"],
    ),
    "management": RuleConfig(
        category="管理能力问题",
        essence="当前问题更像管理动作不到位，直接加人可能放大低效。",
        hire_recommendation="不建议",
        reason_template="识别到执行力/管理机制不足信号：{hits}",
        advice=[
            "先建立目标拆解、过程复盘和责任追踪机制。",
            "补齐中层管理动作：周节奏、复盘、跨部门对齐。",
            "管理机制稳定后再判断是否需要增员。",
        ],
        keywords=["执行差", "推不动", "管理不到位", "协同弱", "中层无力", "老板太累", "没人盯"],
    ),
}


def _count_hits(text: str, keywords: List[str]) -> Tuple[int, List[str]]:
    """统计命中关键词数量。"""

    hits = [kw for kw in keywords if kw in text]
    return len(hits), hits


def diagnose(problem_text: str) -> Dict[str, object]:
    """根据输入文本进行规则诊断。"""

    cleaned = (problem_text or "").strip()
    if len(cleaned) < 6:
        return {
            "问题本质": "输入信息过少，暂时无法判断是否属于招聘问题。",
            "是否建议招聘": "暂不确定",
            "问题类型": "信息不足",
            "判断理由": ["描述字数过少，缺乏场景、对象和结果信息。"],
            "建议": [
                "补充现象：发生在什么业务环节。",
                "补充影响：对收入、成本、交付或团队的影响。",
                "补充责任：当前由谁负责、卡在哪里。",
            ],
        }

    score_board = {}
    hit_board = {}

    # 遍历所有类别进行关键词命中打分。
    for key, cfg in RULES.items():
        score, hits = _count_hits(cleaned, cfg.keywords)
        score_board[key] = score
        hit_board[key] = hits

    best_category, best_score = max(score_board.items(), key=lambda item: item[1])

    # 当所有命中都为0，或者存在明显并列，返回“信息不足/暂不确定”。
    sorted_scores = sorted(score_board.values(), reverse=True)
    if best_score == 0 or (len(sorted_scores) > 1 and sorted_scores[0] == sorted_scores[1]):
        return {
            "问题本质": "当前描述可指向多种管理问题，暂时无法定位单一根因。",
            "是否建议招聘": "暂不确定",
            "问题类型": "信息不足",
            "判断理由": [
                "关键词信号不足或存在并列，无法形成稳定判断。",
                "建议补充“具体场景 + 当前负责人 + 已尝试动作”。",
            ],
            "建议": [
                "先用一周记录法梳理问题出现频次与环节。",
                "补充一条“如果不解决，会损失什么”的业务描述。",
                "补充当前团队分工图，再次诊断。",
            ],
        }

    cfg = RULES[best_category]
    hits_text = "、".join(hit_board[best_category])

    return {
        "问题本质": cfg.essence,
        "是否建议招聘": cfg.hire_recommendation,
        "问题类型": cfg.category,
        "判断理由": [
            cfg.reason_template.format(hits=hits_text),
            "该结论来自可解释规则引擎（关键词命中与类别得分）。",
        ],
        "建议": cfg.advice,
    }
