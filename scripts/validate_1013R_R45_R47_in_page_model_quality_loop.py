from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / "1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_REVIEW"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    index = read_text(ROOT / "frontend" / "workbench" / "index.html")
    js = read_text(ROOT / "frontend" / "workbench" / "workbench_in_page_model_quality_loop_1013R_R45_R47.js")
    css = read_text(ROOT / "frontend" / "workbench" / "workbench_in_page_model_quality_loop_1013R_R45_R47.css")
    backend = read_text(ROOT / "backend" / "xiaobei_ai" / "prep_room_in_page_model_quality_loop_1013R_R45_R47.py")
    server = read_text(ROOT / "scripts" / "start_workbench_ai_v13_local.py")

    require("workbench_in_page_model_quality_loop_1013R_R45_R47.js" in index, "index_html_missing_r45_r47_js")
    require("workbench_in_page_model_quality_loop_1013R_R45_R47.css" in index, "index_html_missing_r45_r47_css")
    require('data-card="modelQualityLoop"' in js or "modelQualityLoop" in js, "frontend_missing_model_quality_card")
    require("/api/prep-room/model-quality/state" in js, "frontend_missing_state_route")
    require("/api/prep-room/model-quality/generate" in js, "frontend_missing_generate_route")
    require("/api/prep-room/model-quality/regenerate" in js, "frontend_missing_regenerate_route")
    require("候选只用于预览和质量观察" in js, "frontend_missing_teacher_visible_boundary")
    require("审核生成物" not in js + css + index, "forbidden_review_artifact_copy_visible")
    require("STATE_ROUTE" in backend and "GENERATE_ROUTE" in backend and "REGENERATE_ROUTE" in backend, "backend_missing_routes")
    require("formal_apply_allowed" in backend and "False" in backend, "backend_missing_formal_apply_guard")
    require("standalone_html_is_main_outcome" in backend, "backend_missing_not_standalone_flag")
    require("prep_room_in_page_model_quality_loop_1013R_R45_R47" in server, "server_missing_import")
    require("GENERATE_ROUTE" in server and "REGENERATE_ROUTE" in server, "server_missing_route_handlers")

    result = read_json(OUT_DIR / "R45_R47_result.json")
    boundary = result.get("boundary") or {}
    require(result.get("ok") is True, "result_not_ok")
    require(result.get("main_outcome") == "existing_workbench_in_page_component", "main_outcome_not_workbench_component")
    require(result.get("standalone_html_main_outcome") is False, "standalone_html_marked_as_main")
    require(boundary.get("sandbox_only") is True, "sandbox_only_not_true")
    require(boundary.get("formal_apply_allowed") is False, "formal_apply_allowed_not_false")
    require(boundary.get("save_performed") is False, "save_performed_not_false")
    require(boundary.get("export_performed") is False, "export_performed_not_false")
    require(boundary.get("database_written") is False, "database_written_not_false")
    require(boundary.get("feishu_written") is False, "feishu_written_not_false")
    require(boundary.get("memory_written") is False, "memory_written_not_false")
    require(boundary.get("original_lesson_overwritten") is False, "original_lesson_overwritten_not_false")
    require((result.get("r46") or {}).get("provider_called") is True, "r46_provider_not_called")
    require((result.get("r46") or {}).get("model_called") is True, "r46_model_not_called")
    comparison = (result.get("r47") or {}).get("comparison") or {}
    require("improved" in comparison and "improvement_delta" in comparison, "r47_comparison_missing")
    if comparison.get("improvement_delta") == 0:
        require(comparison.get("improved") is False, "zero_delta_must_not_be_improved")

    print(json.dumps({"ok": True, "stage": "1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_INTEGRATION"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
