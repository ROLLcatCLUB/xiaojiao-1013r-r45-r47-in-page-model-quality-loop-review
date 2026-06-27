from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from . import prep_room_model_quality_loop_1013R_R40_R44 as r40_r44


STAGE_ID = "1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_INTEGRATION"
STATE_ROUTE = "/api/prep-room/model-quality/state"
GENERATE_ROUTE = "/api/prep-room/model-quality/generate"
REGENERATE_ROUTE = "/api/prep-room/model-quality/regenerate"

DEFAULT_CONTEXT = {
    "lesson": "三年级美术 2-1《色彩的渐变》",
    "source": "current_workbench_prep_room",
    "context_source": "workbench/index.html in-page component",
    "before_text": r40_r44.CASE_BEFORE_TEXT,
    "teacher_problem": r40_r44.CASE_INPUT,
}

CANDIDATE_TYPES = [
    {
        "id": "teaching_process_cleanup",
        "label": "教学过程整理",
        "target_slot": "当前教案教学过程预览槽",
    },
    {
        "id": "courseware_script_candidate",
        "label": "课件脚本候选",
        "target_slot": "右侧课件/课件制作预览",
    },
    {
        "id": "classroom_display_candidate",
        "label": "大屏呈现候选",
        "target_slot": "大屏草稿预览",
    },
    {
        "id": "worksheet_candidate",
        "label": "学习单候选",
        "target_slot": "学生任务单预览",
    },
    {
        "id": "assessment_rubric_candidate",
        "label": "评价维度候选",
        "target_slot": "评价表预览",
    },
]


def _boundary(provider_called: bool = False, model_called: bool = False) -> dict[str, Any]:
    boundary = r40_r44.boundary_flags(STAGE_ID, provider_called, model_called)
    boundary.update(
        {
            "in_page_integration": True,
            "main_outcome_is_workbench_component": True,
            "standalone_html_is_main_outcome": False,
            "formal_apply_allowed": False,
            "save_allowed": False,
            "export_allowed": False,
            "archive_allowed": False,
            "database_write_allowed": False,
            "feishu_write_allowed": False,
            "memory_write_allowed": False,
            "overwrite_original_allowed": False,
        }
    )
    return boundary


def _provider_status() -> dict[str, Any]:
    return r40_r44._provider_public_status()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if value in (None, ""):
        return []
    return [str(value)]


def _candidate_label(candidate_type: str) -> str:
    for item in CANDIDATE_TYPES:
        if item["id"] == candidate_type:
            return item["label"]
    return candidate_type


def _target_slot(candidate_type: str) -> str:
    for item in CANDIDATE_TYPES:
        if item["id"] == candidate_type:
            return item["target_slot"]
    return "当前页面候选预览槽"


def _prompt(candidate_type: str, before_text: str, adjustment_text: str = "", previous_text: str = "") -> tuple[str, str]:
    label = _candidate_label(candidate_type)
    system = (
        "你是师维智教里的小教页面内候选生成器。只输出 JSON。"
        "候选只能用于当前工作台页面预览和质量观察，不能保存、导出、归档、写数据库、写飞书、写记忆或覆盖原教案。"
        "必须贴合三年级美术《色彩的渐变》，缺依据时要写 missing_requirements 或 blocked。"
    )
    user = {
        "stage": STAGE_ID,
        "candidate_type": candidate_type,
        "candidate_label": label,
        "lesson": DEFAULT_CONTEXT["lesson"],
        "before_text": before_text or DEFAULT_CONTEXT["before_text"],
        "previous_candidate": previous_text,
        "teacher_adjustment": adjustment_text,
        "target_slot": _target_slot(candidate_type),
        "rules": [
            "不要虚构教材页码、学生数据、真实班级情况或不存在的素材",
            "输出要让老师能直接二次编辑",
            "评价维度依据不足时可以 blocked",
            "候选内容不自动采纳",
        ],
        "output_schema": {
            "candidate_id": "string",
            "status": "generated | blocked",
            "before_or_context": "string",
            "candidate_content": "string",
            "xiaojiao_suggestion": "string",
            "missing_requirements": ["string"],
            "risk_notes": ["string"],
        },
    }
    return system, json.dumps(user, ensure_ascii=False, indent=2)


def initial_state() -> tuple[dict[str, Any], int]:
    return {
        "success": True,
        "stage": STAGE_ID,
        "mode": "in_page_model_quality_loop",
        "context": deepcopy(DEFAULT_CONTEXT),
        "candidate_types": deepcopy(CANDIDATE_TYPES),
        "provider": _provider_status(),
        "message": "候选只用于预览和质量观察，不会保存到正式备课本。",
        "boundary": _boundary(),
    }, 200


def _normalize_candidate(candidate_type: str, parsed: dict[str, Any] | None, log: dict[str, Any], before_text: str) -> dict[str, Any]:
    if candidate_type == "assessment_rubric_candidate" and not isinstance(parsed, dict):
        fallback = r40_r44._fallback_candidate(candidate_type, "blocked", "missing_teacher_dimension")
    else:
        fallback = r40_r44._fallback_candidate(candidate_type, "fallback", log.get("reason_code") or "model_unavailable")
    payload = parsed if isinstance(parsed, dict) else fallback
    content = str(payload.get("candidate_content") or payload.get("after_text") or fallback.get("candidate_content") or "").strip()
    status = str(payload.get("status") or ("generated" if content else "blocked")).strip()
    if status == "blocked" and candidate_type != "assessment_rubric_candidate" and content:
        status = "generated"
    if candidate_type == "assessment_rubric_candidate" and "评价" not in content and not _as_list(payload.get("missing_requirements")):
        status = "blocked"
    return {
        "candidate_id": str(payload.get("candidate_id") or fallback.get("candidate_id")),
        "candidate_type": candidate_type,
        "candidate_label": _candidate_label(candidate_type),
        "target_slot": _target_slot(candidate_type),
        "source": "real_model" if log.get("status") == "success" else "fallback_quality_sandbox",
        "status": status,
        "provider_called": bool(log.get("provider_called")),
        "model_called": bool(log.get("model_called")),
        "sandbox_only": True,
        "formal_apply_allowed": False,
        "overwrite_original_allowed": False,
        "teacher_confirmation_required": True,
        "before_or_context": str(payload.get("before_or_context") or payload.get("before_text") or before_text or DEFAULT_CONTEXT["before_text"]),
        "candidate_content": content,
        "xiaojiao_suggestion": str(payload.get("xiaojiao_suggestion") or fallback.get("xiaojiao_suggestion") or "请老师确认后再进入下一步。"),
        "missing_requirements": _as_list(payload.get("missing_requirements") or fallback.get("missing_requirements")),
        "risk_notes": _as_list(payload.get("risk_notes") or fallback.get("risk_notes") or ["需要教师确认", "不得覆盖原文"]),
    }


def _quality_panel(candidate: dict[str, Any]) -> dict[str, Any]:
    scored = r40_r44._score_candidate(
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_type"],
            "candidate_content": candidate.get("candidate_content") or "",
            "status": "blocked" if candidate.get("status") == "blocked" else "generated",
            "missing_requirements": candidate.get("missing_requirements") or [],
            "risk_notes": candidate.get("risk_notes") or [],
        }
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_type": candidate["candidate_type"],
        "status": scored.get("status"),
        "scores": scored.get("scores") or {},
        "total_score": scored.get("total_score"),
        "pass_line": scored.get("pass_line", 24),
        "basic_quality_pass": bool(scored.get("basic_quality_pass")),
        "requires_human_attention": bool(scored.get("requires_human_attention", True)),
        "blocked_reason": scored.get("blocked_reason"),
        "adjustment_points": scored.get("prompt_schema_adjustment_points") or [],
    }


def generate_candidate(payload: Any) -> tuple[dict[str, Any], int]:
    request_payload = payload if isinstance(payload, dict) else {}
    candidate_type = str(request_payload.get("candidate_type") or "teaching_process_cleanup").strip()
    if candidate_type not in {item["id"] for item in CANDIDATE_TYPES}:
        return {"success": False, "error": "unsupported_candidate_type", "candidate_type": candidate_type}, 400
    before_text = str(request_payload.get("before_text") or DEFAULT_CONTEXT["before_text"]).strip()
    adjustment_text = str(request_payload.get("adjustment_text") or "").strip()
    system, user = _prompt(candidate_type, before_text, adjustment_text)
    parsed, log = r40_r44._call_provider_json(
        f"R45_R47_in_page_{candidate_type}",
        STAGE_ID,
        candidate_type,
        system,
        user,
        max_tokens=2200,
    )
    candidate = _normalize_candidate(candidate_type, parsed, log, before_text)
    quality = _quality_panel(candidate)
    return {
        "success": True,
        "stage": STAGE_ID,
        "mode": "generate_in_page_candidate",
        "context": {**deepcopy(DEFAULT_CONTEXT), "before_text": before_text},
        "candidate": candidate,
        "quality_panel": quality,
        "model_call_log_redacted": log,
        "message": "候选已回填到当前工作台组件，未保存、未导出、未覆盖。",
        "boundary": _boundary(candidate["provider_called"], candidate["model_called"]),
    }, 200


def regenerate_candidate(payload: Any) -> tuple[dict[str, Any], int]:
    request_payload = payload if isinstance(payload, dict) else {}
    previous = request_payload.get("previous_candidate") if isinstance(request_payload.get("previous_candidate"), dict) else {}
    candidate_type = str(request_payload.get("candidate_type") or previous.get("candidate_type") or "teaching_process_cleanup").strip()
    before_text = str(request_payload.get("before_text") or previous.get("before_or_context") or DEFAULT_CONTEXT["before_text"]).strip()
    adjustment_text = str(request_payload.get("adjustment_text") or "").strip()
    previous_text = str(previous.get("candidate_content") or "").strip()
    if not adjustment_text:
        adjustment_text = "让候选更贴近小学美术课堂，步骤更清楚，减少空泛表达。"
    system, user = _prompt(candidate_type, before_text, adjustment_text, previous_text)
    parsed, log = r40_r44._call_provider_json(
        f"R47_in_page_regenerate_{candidate_type}",
        STAGE_ID,
        f"{candidate_type}_regenerate",
        system,
        user,
        max_tokens=2200,
    )
    v2 = _normalize_candidate(candidate_type, parsed, log, before_text)
    v1_quality = _quality_panel(previous) if previous else {}
    v2_quality = _quality_panel(v2)
    v1_score = int(v1_quality.get("total_score") or 0)
    v2_score = int(v2_quality.get("total_score") or 0)
    comparison = {
        "v1_score": v1_score,
        "v2_score": v2_score,
        "improvement_delta": v2_score - v1_score,
        "improved": v2_score > v1_score,
        "same_score": v2_score == v1_score,
        "v2_basic_quality_pass": bool(v2_quality.get("basic_quality_pass")),
    }
    return {
        "success": True,
        "stage": STAGE_ID,
        "mode": "regenerate_in_page_candidate",
        "context": {**deepcopy(DEFAULT_CONTEXT), "before_text": before_text},
        "v1_candidate": previous,
        "v2_candidate": v2,
        "candidate": v2,
        "quality_panel": v2_quality,
        "comparison": comparison,
        "model_call_log_redacted": log,
        "message": "再生成结果已回填到当前工作台组件，未保存、未导出、未覆盖。",
        "boundary": _boundary(v2["provider_called"], v2["model_called"]),
    }, 200
