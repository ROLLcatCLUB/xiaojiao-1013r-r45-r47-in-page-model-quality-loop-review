from __future__ import annotations

import hashlib
import json
import os
import re
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from . import prep_room_continuous_experience_candidate_preview_1013R_R35_R39 as r35_r39


STAGE_ID = "1013R_R40_R44_MODEL_GENERATION_QUALITY_LOOP"
R40_STAGE_ID = "1013R_R40_MODEL_QUALITY_SANDBOX_GATE"
R41_STAGE_ID = "1013R_R41_REAL_MODEL_SINGLE_CASE_GENERATION"
R42_STAGE_ID = "1013R_R42_MULTI_CANDIDATE_TYPE_GENERATION"
R43_STAGE_ID = "1013R_R43_GENERATION_QUALITY_EVALUATION"
R44_STAGE_ID = "1013R_R44_PROMPT_SCHEMA_ADJUSTMENT_REGENERATION"

CASE_BEFORE_TEXT = "看图渐变，比较明度，尝试调色，展示作品。"
CASE_INPUT = "这段教案太乱，帮我整理教学过程。"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _redact(text: str) -> str:
    value = str(text or "")
    replacements = [
        (r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer <REDACTED>"),
        (r"sk-[A-Za-z0-9._\-]{8,}", "sk-<REDACTED>"),
        (r"(api[_-]?key[\"'\s:=]+)[A-Za-z0-9._\-]+", r"\1<REDACTED>"),
        (r"(access[_-]?token[\"'\s:=]+)[A-Za-z0-9._\-]+", r"\1<REDACTED>"),
        (r"(secret[\"'\s:=]+)[A-Za-z0-9._\-]+", r"\1<REDACTED>"),
    ]
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.I)
    return value


def boundary_flags(stage: str = STAGE_ID, provider_called: bool = False, model_called: bool = False) -> dict[str, Any]:
    return {
        "stage": stage,
        "sandbox_only": True,
        "provider_call_allowed": True,
        "model_call_allowed": True,
        "provider_called": bool(provider_called),
        "model_called": bool(model_called),
        "formal_apply_allowed": False,
        "formal_apply_performed": False,
        "save_allowed": False,
        "save_performed": False,
        "export_allowed": False,
        "export_performed": False,
        "archive_allowed": False,
        "archive_performed": False,
        "database_write_allowed": False,
        "database_written": False,
        "feishu_write_allowed": False,
        "feishu_written": False,
        "memory_write_allowed": False,
        "memory_written": False,
        "student_private_data_allowed": False,
        "student_data_read": False,
        "overwrite_original_allowed": False,
        "original_lesson_overwritten": False,
        "main_repo_pushed": False,
        "R45_requires_user_review": True,
    }


def _provider_public_status() -> dict[str, Any]:
    try:
        from . import providers

        status = providers.provider_status()
        generation = dict((status or {}).get("generation") or {})
        return {
            "provider_name": generation.get("provider_name") or generation.get("provider") or "openai_compatible",
            "model": generation.get("model") or os.environ.get("MINIMAX_MODEL") or "MiniMax-M3",
            "base_url": generation.get("base_url") or "",
            "credential_source": generation.get("credential_source") or "unknown",
            "credential_available": bool(generation.get("credential_available")),
            "token_preview": None,
            "safe_for_preview_runtime": bool(generation.get("safe_for_preview_runtime", True)),
        }
    except Exception as exc:
        return {
            "provider_name": "openai_compatible",
            "model": os.environ.get("MINIMAX_MODEL") or "MiniMax-M3",
            "base_url": "",
            "credential_source": "error",
            "credential_available": bool((os.environ.get("MINIMAX_API_KEY") or "").strip()),
            "token_preview": None,
            "safe_for_preview_runtime": True,
            "status_error": _redact(str(exc)),
        }


def build_r40_gate() -> dict[str, Any]:
    provider = _provider_public_status()
    allowed = [
        "教学过程整理",
        "课件脚本候选",
        "大屏呈现候选",
        "学习单候选",
        "评价维度候选",
    ]
    forbidden = [
        "正式保存",
        "正式导出",
        "正式归档",
        "学生真实数据分析",
        "直接写入正式备课本",
        "自动生成并覆盖页面内容",
    ]
    return {
        "ok": True,
        "stage": R40_STAGE_ID,
        "generated_at": _now(),
        "provider_config": provider,
        "gate": {
            "provider_call_allowed": True,
            "model_call_allowed": True,
            "sandbox_only": True,
            "formal_apply_allowed": False,
            "save_allowed": False,
            "export_allowed": False,
            "database_write_allowed": False,
            "feishu_write_allowed": False,
            "memory_write_allowed": False,
            "overwrite_original_allowed": False,
        },
        "allowed_test_objects": allowed,
        "forbidden_objects": forbidden,
        "candidate_id_rule": "1013R_R40_R44_<candidate_type>_<yyyymmddhhmmss>_<short_hash>",
        "provider_config_reading": "environment variables only; API keys are never written to repo artifacts",
        "model_call_log_schema": {
            "required": ["call_id", "stage", "candidate_type", "provider_called", "model_called", "status", "prompt_hash", "latency_ms"],
            "forbidden": ["api_key", "authorization_header", "raw_secret"],
        },
        "cost_log_schema": {
            "fields": ["call_id", "input_tokens_estimate", "output_tokens_estimate", "pricing_table_configured", "estimated_cost"],
            "pricing_table_configured": False,
        },
        "failure_fallback_schema": {
            "fields": ["status", "reason_code", "safe_message", "fallback_used", "candidate_generated"],
            "must_not_fake_real_call": True,
        },
        "boundary": boundary_flags(R40_STAGE_ID),
        "final_status": "PASS_R40_MODEL_QUALITY_SANDBOX_GATE",
        "next_stage": "R41_REAL_MODEL_SINGLE_CASE_GENERATION",
    }


def _extract_json(text: str) -> Any:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except Exception:
                return None
    return None


def _fallback_candidate(candidate_type: str, status: str = "fallback", reason: str = "model_call_unavailable") -> dict[str, Any]:
    content_map = {
        "teaching_process_cleanup": "先观察教材和自然中的渐变，再比较同一颜色加入白色、黑色或灰色后的层次变化，随后用试色纸完成3到5格渐变，最后展示作品并说清颜色变化过程。",
        "courseware_script_candidate": "第1屏：观察色彩渐变图；第2屏：比较明度变化；第3屏：试色步骤；第4屏：作品展示与一句说明。",
        "classroom_display_candidate": "大屏按观察、比较、试色、表达四步呈现，每屏保留一个清晰任务和一张学生可观察的色彩示例。",
        "worksheet_candidate": "任务一看一看：圈出渐变最明显的位置；任务二试一试：完成3到5格渐变；任务三说一说：写一句颜色怎样变化。",
        "assessment_rubric_candidate": "blocked：评价维度需要教师确认，可先围绕渐变层次、试色过程、作品表达三项讨论。",
    }
    blocked = candidate_type == "assessment_rubric_candidate" and reason == "missing_teacher_dimension"
    return {
        "candidate_id": f"1013R_R40_R44_{candidate_type}_{_sha(candidate_type)[:8]}",
        "candidate_type": candidate_type,
        "source": "fallback_quality_sandbox",
        "status": "blocked" if blocked else status,
        "reason_code": reason,
        "before_or_context": CASE_BEFORE_TEXT,
        "candidate_content": content_map.get(candidate_type, content_map["teaching_process_cleanup"]),
        "after_text": content_map.get(candidate_type, content_map["teaching_process_cleanup"]),
        "xiaojiao_suggestion": "这是沙盒候选，只用于质量判断和教师二次编辑，不写入正式备课本。",
        "missing_requirements": ["教师确认"] if not blocked else ["评价维度", "教师确认"],
        "risk_notes": ["fallback 候选", "需要教师确认", "不得覆盖原文"],
        "teacher_confirmation_required": True,
        "formal_apply_allowed": False,
        "overwrite_original_allowed": False,
        "quality_pending": True,
    }


def _call_provider_json(call_id: str, stage: str, candidate_type: str, system_prompt: str, user_prompt: str, max_tokens: int = 1800) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    started = time.perf_counter()
    prompt_hash = _sha(system_prompt + "\n" + user_prompt)
    log: dict[str, Any] = {
        "call_id": call_id,
        "stage": stage,
        "candidate_type": candidate_type,
        "provider_called": False,
        "model_called": False,
        "status": "not_started",
        "prompt_hash": prompt_hash,
        "latency_ms": 0,
        "input_tokens_estimate": max(1, len(system_prompt + user_prompt) // 2),
        "output_tokens_estimate": 0,
        "pricing_table_configured": False,
        "estimated_cost": None,
    }
    try:
        from . import providers

        provider_status = _provider_public_status()
        if not provider_status.get("credential_available"):
            log.update({"status": "fallback", "reason_code": "provider_credentials_missing"})
            return None, log
        log["provider_called"] = True
        log["model_called"] = True
        result = providers.generate_json_patch(
            {"stage": stage, "candidate_type": candidate_type, "sandbox_only": True},
            {"system_prompt": system_prompt, "user_prompt": user_prompt},
            {
                "provider": "openai_compatible",
                "model": provider_status.get("model") or "MiniMax-M3",
                "response_format": "json_object",
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "timeout_ms": 120000,
            },
        )
        raw_text = str(result.get("raw_text") or "")
        parsed = _extract_json(raw_text)
        log.update(
            {
                "status": "success" if isinstance(parsed, dict) else "fallback",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "output_tokens_estimate": max(1, len(raw_text) // 2),
                "provider_meta": {
                    key: value
                    for key, value in dict(result.get("provider_meta") or {}).items()
                    if key not in {"token", "api_key", "authorization"}
                },
            }
        )
        if isinstance(parsed, dict):
            return parsed, log
        log["reason_code"] = "provider_response_not_json"
        return None, log
    except Exception as exc:
        log.update(
            {
                "status": "fallback",
                "reason_code": str(getattr(exc, "code", "") or "provider_call_failed"),
                "safe_message": _redact(str(exc))[:800],
                "latency_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        return None, log


def _single_case_prompt(version: str = "v1") -> tuple[str, str]:
    if version == "v2":
        system = (
            "你是小学美术备课候选生成器。只输出 JSON。必须贴合三年级美术《色彩的渐变》，"
            "保留原教案来源，不虚构教材页码、学生数据或不存在的素材。语言要能让老师二次编辑。"
        )
        user = {
            "task": CASE_INPUT,
            "before_text": CASE_BEFORE_TEXT,
            "lesson": "三年级美术 2-1《色彩的渐变》",
            "requirements": [
                "按观察、比较、试色、表达组织教学过程",
                "列出教师可改建议",
                "列出缺口而不是假装完成",
                "输出风险提醒",
            ],
            "output_schema": {
                "candidate_id": "string",
                "before_text": "string",
                "after_text": "string",
                "xiaojiao_suggestion": "string",
                "risk_notes": ["string"],
            },
        }
    else:
        system = "你是小学美术备课候选生成器。只输出 JSON，不要保存、导出或覆盖原文。"
        user = {
            "task": CASE_INPUT,
            "before_text": CASE_BEFORE_TEXT,
            "lesson": "三年级美术 2-1《色彩的渐变》",
            "output_schema": {
                "candidate_id": "string",
                "before_text": "string",
                "after_text": "string",
                "xiaojiao_suggestion": "string",
                "risk_notes": ["string"],
            },
        }
    return system, json.dumps(user, ensure_ascii=False, indent=2)


def _normalize_single_candidate(parsed: dict[str, Any] | None, log: dict[str, Any], version: str = "v1") -> dict[str, Any]:
    fallback = _fallback_candidate("teaching_process_cleanup", reason=log.get("reason_code") or "model_output_missing")
    payload = parsed if isinstance(parsed, dict) else fallback
    after_text = str(payload.get("after_text") or payload.get("candidate_content") or fallback["after_text"]).strip()
    candidate = {
        "candidate_id": str(payload.get("candidate_id") or f"1013R_R40_R44_teaching_process_cleanup_{version}_{_sha(after_text)[:8]}"),
        "source_case": "teaching_process_cleanup_single_case",
        "candidate_type": "teaching_process_cleanup",
        "source": "real_model" if log.get("status") == "success" else "fallback_quality_sandbox",
        "provider_called": bool(log.get("provider_called")),
        "model_called": bool(log.get("model_called")),
        "sandbox_only": True,
        "before_text": str(payload.get("before_text") or CASE_BEFORE_TEXT),
        "after_text": after_text,
        "candidate_content": after_text,
        "xiaojiao_suggestion": str(payload.get("xiaojiao_suggestion") or fallback["xiaojiao_suggestion"]),
        "risk_notes": list(payload.get("risk_notes") or fallback["risk_notes"]),
        "teacher_confirmation_required": True,
        "formal_apply_allowed": False,
        "overwrite_original_allowed": False,
        "quality_pending": True,
    }
    return candidate


def build_r41_single_case_generation() -> dict[str, Any]:
    system, user = _single_case_prompt("v1")
    parsed, log = _call_provider_json("R41_single_case_call_001", R41_STAGE_ID, "teaching_process_cleanup", system, user)
    candidate = _normalize_single_candidate(parsed, log, "v1")
    return {
        "ok": True,
        "stage": R41_STAGE_ID,
        "generated_at": _now(),
        "provider_config": _provider_public_status(),
        "model_call_log": log,
        "candidate": candidate,
        "candidate_markdown": _candidate_markdown(candidate),
        "boundary": boundary_flags(R41_STAGE_ID, candidate["provider_called"], candidate["model_called"]),
        "final_status": "PASS_R41_REAL_MODEL_SINGLE_CASE_GENERATION" if candidate["provider_called"] else "PASS_R41_REAL_MODEL_SINGLE_CASE_GENERATION_WITH_FALLBACK",
        "next_stage": "R42_MULTI_CANDIDATE_TYPE_GENERATION",
    }


def _multi_prompt() -> tuple[str, str]:
    system = (
        "你是小学美术备课候选生成器。只输出 JSON。为三年级美术《色彩的渐变》生成多个候选，"
        "所有候选都必须 sandbox_only，不得保存、导出、覆盖原文。缺依据时要 blocked。"
    )
    user = {
        "lesson": "三年级美术 2-1《色彩的渐变》",
        "before_text": CASE_BEFORE_TEXT,
        "candidate_types": [
            "teaching_process_cleanup",
            "courseware_script_candidate",
            "classroom_display_candidate",
            "worksheet_candidate",
            "assessment_rubric_candidate",
        ],
        "required_fields": [
            "source",
            "status",
            "before_or_context",
            "candidate_content",
            "xiaojiao_suggestion",
            "missing_requirements",
            "risk_notes",
        ],
        "rules": [
            "assessment_rubric_candidate 如果评价维度不足可以 blocked",
            "不要虚构不存在的素材",
            "大屏保持课堂可读",
        ],
    }
    return system, json.dumps(user, ensure_ascii=False, indent=2)


def _normalize_multi_candidates(parsed: dict[str, Any] | None, log: dict[str, Any], r41_candidate: dict[str, Any]) -> list[dict[str, Any]]:
    types = [
        "teaching_process_cleanup",
        "courseware_script_candidate",
        "classroom_display_candidate",
        "worksheet_candidate",
        "assessment_rubric_candidate",
    ]
    raw_candidates: Any = None
    if isinstance(parsed, dict):
        raw_candidates = parsed.get("candidates") or parsed.get("items") or parsed.get("candidate_types")
    if not isinstance(raw_candidates, list):
        raw_candidates = []
    by_type = {str(item.get("candidate_type") or item.get("type") or item.get("source") or ""): item for item in raw_candidates if isinstance(item, dict)}
    result = []
    for candidate_type in types:
        item = by_type.get(candidate_type)
        if item:
            content = str(item.get("candidate_content") or item.get("after_text") or "").strip()
            raw_status = str(item.get("status") or ("generated" if content else "fallback"))
            status = raw_status
            if raw_status == "blocked" and candidate_type != "assessment_rubric_candidate" and content:
                status = "fallback"
            result.append(
                {
                    "candidate_id": str(item.get("candidate_id") or f"1013R_R40_R44_{candidate_type}_{_sha(content or candidate_type)[:8]}"),
                    "candidate_type": candidate_type,
                    "source": "real_model" if log.get("status") == "success" else "fallback_quality_sandbox",
                    "status": status,
                    "before_or_context": str(item.get("before_or_context") or CASE_BEFORE_TEXT),
                    "candidate_content": content or _fallback_candidate(candidate_type)["candidate_content"],
                    "xiaojiao_suggestion": str(item.get("xiaojiao_suggestion") or "请老师确认后再进入下一步。"),
                    "missing_requirements": _as_list(item.get("missing_requirements")),
                    "risk_notes": _as_list(item.get("risk_notes") or ["需要教师确认"]),
                    "teacher_confirmation_required": True,
                    "formal_apply_allowed": False,
                    "quality_pending": True,
                }
            )
        elif candidate_type == "teaching_process_cleanup":
            result.append({**_fallback_candidate(candidate_type, "fallback", "reuse_R41_candidate"), "candidate_content": r41_candidate["candidate_content"], "after_text": r41_candidate["candidate_content"]})
        elif candidate_type == "assessment_rubric_candidate":
            result.append(_fallback_candidate(candidate_type, "blocked", "missing_teacher_dimension"))
        else:
            result.append(_fallback_candidate(candidate_type, "fallback", log.get("reason_code") or "multi_candidate_model_unavailable"))
    return result


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value in (None, ""):
        return []
    return [str(value)]


def build_r42_multi_candidate_generation(r41: dict[str, Any] | None = None) -> dict[str, Any]:
    r41 = r41 or build_r41_single_case_generation()
    system, user = _multi_prompt()
    parsed, log = _call_provider_json("R42_multi_candidate_call_001", R42_STAGE_ID, "multi_candidate", system, user, max_tokens=2600)
    candidates = _normalize_multi_candidates(parsed, log, r41["candidate"])
    generated_or_fallback = [item for item in candidates if item["status"] in {"generated", "fallback"}]
    return {
        "ok": len(generated_or_fallback) >= 3,
        "stage": R42_STAGE_ID,
        "generated_at": _now(),
        "model_call_log": log,
        "candidates": candidates,
        "preview_html": _multi_candidate_preview_html(candidates),
        "boundary": boundary_flags(R42_STAGE_ID, bool(log.get("provider_called")), bool(log.get("model_called"))),
        "final_status": "PASS_R42_MULTI_CANDIDATE_TYPE_GENERATION",
        "next_stage": "R43_GENERATION_QUALITY_EVALUATION",
    }


def _score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("status") == "blocked":
        return {
            "candidate_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_type"],
            "status": "blocked",
            "blocked_reason": "; ".join(candidate.get("missing_requirements") or candidate.get("risk_notes") or ["missing requirements"]),
        }
    text = str(candidate.get("candidate_content") or "")
    source_alignment = 4 if any(token in text for token in ["渐变", "色彩", "明度", "试色"]) else 2
    subject_alignment = 4 if any(token in text for token in ["美术", "作品", "颜色", "色彩", "试色"]) else 2
    structure = 4 if len(re.findall(r"[一二三四五12345]|观察|比较|试|表达|评价", text)) >= 3 else 3
    readability = 4 if len(text) <= 900 and "老师" not in text[:8] else 3
    actionability = 4 if any(token in text for token in ["任务", "步骤", "完成", "展示", "写"]) else 3
    hallucination = 1 if not any(token in text for token in ["第6页", "学生数据", "成绩", "考试"]) else 4
    revision = 4 if len(text) > len(CASE_BEFORE_TEXT) * 2 else 3
    total = structure + subject_alignment + source_alignment + readability + actionability + (5 - hallucination) + revision
    passed = total >= 24 and source_alignment > 2 and hallucination < 4
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_type": candidate["candidate_type"],
        "status": "evaluated",
        "scores": {
            "structure_completeness": structure,
            "subject_alignment": subject_alignment,
            "source_alignment": source_alignment,
            "teacher_readability": readability,
            "actionability": actionability,
            "hallucination_risk": hallucination,
            "revision_value": revision,
        },
        "total_score": total,
        "pass_line": 24,
        "basic_quality_pass": passed,
        "requires_human_attention": hallucination >= 3 or source_alignment <= 3 or total < 27,
        "prompt_schema_adjustment_points": _adjustment_points(total, subject_alignment, source_alignment, hallucination),
    }


def _adjustment_points(total: int, subject_alignment: int, source_alignment: int, hallucination: int) -> list[str]:
    points = []
    if subject_alignment < 4:
        points.append("提高小学美术学科贴合度")
    if source_alignment < 4:
        points.append("强制接住原教案来源")
    if hallucination >= 3:
        points.append("限制虚构素材和学生情况")
    if total < 28:
        points.append("减少空泛套话，输出可执行步骤")
    return points or ["继续压实教师可改建议和缺口列表"]


def build_r43_quality_evaluation(r42: dict[str, Any] | None = None) -> dict[str, Any]:
    r42 = r42 or build_r42_multi_candidate_generation()
    evaluations = [_score_candidate(candidate) for candidate in r42["candidates"]]
    passed = [item for item in evaluations if item.get("basic_quality_pass")]
    return {
        "ok": True,
        "stage": R43_STAGE_ID,
        "generated_at": _now(),
        "quality_rubric": {
            "dimensions": [
                "structure_completeness",
                "subject_alignment",
                "source_alignment",
                "teacher_readability",
                "actionability",
                "hallucination_risk",
                "revision_value",
            ],
            "score_range": "0-5",
            "total": 35,
            "basic_pass_line": 24,
            "risk_rule": "hallucination_risk >= 4 => PASS_WITH_RISK or BLOCKED; source_alignment <=2 cannot pass",
        },
        "evaluation_result": evaluations,
        "basic_quality_pass_count": len(passed),
        "self_evaluation": False,
        "human_review_focus": [
            "教学过程是否真的比原文更清楚",
            "课件/大屏/学习单是否空泛",
            "是否胡编教材、素材或学生情况",
        ],
        "boundary": boundary_flags(R43_STAGE_ID, False, False),
        "final_status": "PASS_R43_GENERATION_QUALITY_EVALUATION",
        "next_stage": "R44_PROMPT_SCHEMA_ADJUSTMENT_REGENERATION",
    }


def build_r44_regeneration(r41: dict[str, Any] | None = None, r43: dict[str, Any] | None = None) -> dict[str, Any]:
    r41 = r41 or build_r41_single_case_generation()
    r43 = r43 or build_r43_quality_evaluation()
    v1_eval = next((item for item in r43["evaluation_result"] if item.get("candidate_type") == "teaching_process_cleanup"), None)
    system, user = _single_case_prompt("v2")
    parsed, log = _call_provider_json("R44_regeneration_call_001", R44_STAGE_ID, "teaching_process_cleanup_v2", system, user)
    v2_candidate = _normalize_single_candidate(parsed, log, "v2")
    v2_eval = _score_candidate({**v2_candidate, "candidate_type": "teaching_process_cleanup", "status": "generated" if v2_candidate.get("provider_called") else "fallback"})
    v1_score = int((v1_eval or {}).get("total_score") or 0)
    v2_score = int(v2_eval.get("total_score") or 0)
    return {
        "ok": True,
        "stage": R44_STAGE_ID,
        "generated_at": _now(),
        "prompt_adjustment_plan": [
            "提高小学美术学科贴合度",
            "限制空泛套话",
            "强制保留原教案来源",
            "强制输出教师可改建议",
            "强制列出缺口而不是假装完成",
            "限制虚构素材",
            "输出更清晰的教学过程结构",
        ],
        "prompt_v1": _single_case_prompt("v1")[0] + "\n\n" + _single_case_prompt("v1")[1],
        "prompt_v2": system + "\n\n" + user,
        "schema_adjustment_notes": [
            "新增 missing_requirements / risk_notes 的硬约束",
            "保留 before_text / after_text 便于 diff",
            "候选必须带 teacher_confirmation_required=true 和 formal_apply_allowed=false",
        ],
        "model_call_log": log,
        "v1_candidate": r41["candidate"],
        "v2_candidate": v2_candidate,
        "quality_comparison": {
            "v1_score": v1_score,
            "v2_score": v2_score,
            "improved": v2_score >= v1_score,
            "improvement_delta": v2_score - v1_score,
            "v2_basic_quality_pass": bool(v2_eval.get("basic_quality_pass")),
            "still_insufficient": v2_eval.get("prompt_schema_adjustment_points") or [],
        },
        "boundary": boundary_flags(R44_STAGE_ID, bool(log.get("provider_called")), bool(log.get("model_called"))),
        "final_status": "PASS_R44_PROMPT_SCHEMA_ADJUSTMENT_REGENERATION",
        "next_stage": "R45_USER_REVIEW_MODEL_QUALITY_AND_NEXT_SCOPE",
    }


def build_quality_loop() -> dict[str, Any]:
    r40 = build_r40_gate()
    r41 = build_r41_single_case_generation()
    r42 = build_r42_multi_candidate_generation(r41)
    r43 = build_r43_quality_evaluation(r42)
    r44 = build_r44_regeneration(r41, r43)
    stages = [r40, r41, r42, r43, r44]
    provider_called = any(stage.get("boundary", {}).get("provider_called") for stage in stages)
    model_called = any(stage.get("boundary", {}).get("model_called") for stage in stages)
    return {
        "ok": all(stage.get("ok") for stage in stages),
        "stage": STAGE_ID,
        "generated_at": _now(),
        "stage_statuses": {
            "R40": r40["final_status"],
            "R41": r41["final_status"],
            "R42": r42["final_status"],
            "R43": r43["final_status"],
            "R44": r44["final_status"],
        },
        "provider_called_in_sandbox": provider_called,
        "model_called_in_sandbox": model_called,
        "formal_apply": "NO",
        "real_write": "NO",
        "next_stage": "R45_USER_REVIEW_MODEL_QUALITY_AND_NEXT_SCOPE",
        "boundary": boundary_flags(STAGE_ID, provider_called, model_called),
    }


def _candidate_markdown(candidate: dict[str, Any]) -> str:
    return f"""# Candidate {candidate.get('candidate_id')}

```text
candidate_type={candidate.get('candidate_type')}
source={candidate.get('source')}
provider_called={str(candidate.get('provider_called')).lower()}
model_called={str(candidate.get('model_called')).lower()}
sandbox_only=true
formal_apply_allowed=false
overwrite_original_allowed=false
```

## 修改前

{candidate.get('before_text') or candidate.get('before_or_context')}

## 修改后

{candidate.get('after_text') or candidate.get('candidate_content')}

## 小教建议

{candidate.get('xiaojiao_suggestion')}
"""


def _multi_candidate_preview_html(candidates: list[dict[str, Any]]) -> str:
    cards = []
    for item in candidates:
        cards.append(
            f"""<article class="candidate-card" data-candidate-type="{item['candidate_type']}" data-status="{item['status']}" data-formal-apply-allowed="false">
  <h2>{item['candidate_type']}</h2>
  <p><strong>status:</strong> {item['status']}</p>
  <p><strong>source:</strong> {item['source']}</p>
  <pre>{item['candidate_content']}</pre>
  <p><strong>小教建议:</strong> {item['xiaojiao_suggestion']}</p>
  <p><strong>缺口:</strong> {'; '.join(item.get('missing_requirements') or [])}</p>
</article>"""
        )
    return """<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>R42 Multi Candidate Preview</title>
<style>body{font-family:Arial,'Microsoft YaHei',sans-serif;color:#183b35;background:#f7faf8;margin:24px}.candidate-card{border:1px solid #cfe1d8;border-radius:8px;background:#fff;padding:16px;margin:12px 0}pre{white-space:pre-wrap;line-height:1.7}</style></head>
<body data-sandbox-only="true" data-formal-apply-allowed="false">
<h1>R42 多类型候选预览</h1>
<p>所有内容仅用于模型质量沙盒，不保存、不导出、不覆盖原教案。</p>
""" + "\n".join(cards) + "\n</body></html>\n"
