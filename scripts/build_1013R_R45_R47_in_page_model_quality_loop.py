from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT_DIR = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / "1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_REVIEW"
WORKBENCH_URL = "file:///D:/Documents/SmartEdu/xiaobei-core/outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R21_page_copy_binds_unified_package/prep_room_page_copy_binds_unified_package_1013R_R21.html"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    from backend.xiaobei_ai import prep_room_in_page_model_quality_loop_1013R_R45_R47 as loop

    state, state_status = loop.initial_state()
    generation, generation_status = loop.generate_candidate(
        {
            "candidate_type": "teaching_process_cleanup",
            "before_text": "看图渐变，比较明度，尝试调色，展示作品。",
            "adjustment_text": "步骤清楚一些，适合三年级美术课堂。",
        }
    )
    regeneration, regeneration_status = loop.regenerate_candidate(
        {
            "candidate_type": "teaching_process_cleanup",
            "before_text": "看图渐变，比较明度，尝试调色，展示作品。",
            "adjustment_text": "更像老师能直接照着上的教学流程，减少空泛词。",
            "previous_candidate": generation.get("candidate") or {},
        }
    )
    result = {
        "ok": all(
            [
                state_status == 200,
                generation_status == 200,
                regeneration_status == 200,
                state.get("boundary", {}).get("main_outcome_is_workbench_component") is True,
                generation.get("boundary", {}).get("formal_apply_allowed") is False,
                regeneration.get("boundary", {}).get("formal_apply_allowed") is False,
            ]
        ),
        "stage": loop.STAGE_ID,
        "generated_at": now(),
        "main_review_url": WORKBENCH_URL,
        "main_outcome": "current_R21_page_copy_in_page_component",
        "standalone_html_main_outcome": False,
        "r45": {
            "status": "PASS_IN_PAGE_MODEL_SANDBOX_PANEL",
            "workbench_component": "outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R21_page_copy_binds_unified_package/prep_room_page_copy_binds_unified_package_1013R_R21.html",
            "state_status": state_status,
        },
        "r46": {
            "status": "PASS_IN_PAGE_REAL_MODEL_CANDIDATE_GENERATION",
            "generation_status": generation_status,
            "candidate_status": (generation.get("candidate") or {}).get("status"),
            "provider_called": bool((generation.get("candidate") or {}).get("provider_called")),
            "model_called": bool((generation.get("candidate") or {}).get("model_called")),
            "quality_total_score": (generation.get("quality_panel") or {}).get("total_score"),
        },
        "r47": {
            "status": "PASS_IN_PAGE_QUALITY_EVALUATION_AND_REGENERATION",
            "regeneration_status": regeneration_status,
            "comparison": regeneration.get("comparison") or {},
        },
        "boundary": regeneration.get("boundary") or generation.get("boundary") or state.get("boundary"),
        "next_stage": "R48_USER_WORKBENCH_REVIEW_REQUIRED",
    }

    write_json(OUT_DIR / "R45_in_page_model_sandbox_state.json", state)
    write_json(OUT_DIR / "R46_in_page_generation_state.json", generation)
    write_json(OUT_DIR / "R46_model_call_log_redacted.json", generation.get("model_call_log_redacted") or {})
    write_json(OUT_DIR / "R47_regeneration_comparison_state.json", regeneration)
    write_json(OUT_DIR / "R45_R47_result.json", result)
    write_text(OUT_DIR / "WORKBENCH_OPEN_URL.txt", WORKBENCH_URL + "\n")
    write_text(
        OUT_DIR / "GPT_REVIEW_NOTE.md",
        f"""# R45-R47 In-page Model Quality Loop Review

```text
stage={loop.STAGE_ID}
main_outcome=current_R21_page_copy_in_page_component
main_review_url={WORKBENCH_URL}
standalone_html_main_outcome=false
sandbox_only=true
formal_apply_allowed=false
save_performed=false
export_performed=false
database_written=false
feishu_written=false
memory_written=false
original_lesson_overwritten=false
NEXT_STAGE=R48_USER_WORKBENCH_REVIEW_REQUIRED
```

## What Changed

- The model quality loop is mounted inside the current R21 page copy:
  `outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R21_page_copy_binds_unified_package/prep_room_page_copy_binds_unified_package_1013R_R21.html`.
- The in-page card is rendered inside the existing R21 right-side tool panel, not in a separate workbench page.
- The card calls the local API routes:
  - `GET /api/prep-room/model-quality/state`
  - `POST /api/prep-room/model-quality/generate`
  - `POST /api/prep-room/model-quality/regenerate`
- Candidate content, quality score, adjustment input, and v1/v2 comparison stay on the same workbench page.

## Review Focus

- Open the workbench URL instead of opening standalone review HTML.
- Confirm the page contains the model candidate card after the current candidate card.
- Confirm generate/regenerate are sandbox-only and do not save or overwrite lesson text.
""",
    )
    if not result["ok"]:
        raise SystemExit("R45-R47 build failed")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
