# R45-R47 In-page Model Quality Loop Review

```text
stage=1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_INTEGRATION
main_outcome=existing_workbench_in_page_component
main_review_url=http://127.0.0.1:5177/workbench/index.html?api=http%3A%2F%2F127.0.0.1%3A8084
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

- The model quality loop is mounted inside `frontend/workbench/index.html`.
- The in-page card is implemented by `frontend/workbench/workbench_in_page_model_quality_loop_1013R_R45_R47.js`.
- The card calls the local API routes:
  - `GET /api/prep-room/model-quality/state`
  - `POST /api/prep-room/model-quality/generate`
  - `POST /api/prep-room/model-quality/regenerate`
- Candidate content, quality score, adjustment input, and v1/v2 comparison stay on the same workbench page.

## Review Focus

- Open the workbench URL instead of opening standalone review HTML.
- Confirm the page contains the model candidate card after the current candidate card.
- Confirm generate/regenerate are sandbox-only and do not save or overwrite lesson text.
