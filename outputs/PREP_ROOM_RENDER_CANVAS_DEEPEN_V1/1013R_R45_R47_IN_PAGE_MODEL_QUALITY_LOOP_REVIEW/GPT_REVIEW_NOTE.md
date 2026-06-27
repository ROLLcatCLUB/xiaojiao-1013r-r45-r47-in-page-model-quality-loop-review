# R45-R47 In-page Model Quality Loop Review

```text
stage=1013R_R45_R47_IN_PAGE_MODEL_QUALITY_LOOP_INTEGRATION
main_outcome=current_R21_page_copy_in_page_component
main_review_url=file:///D:/Documents/SmartEdu/xiaobei-core/outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/1013R_R21_page_copy_binds_unified_package/prep_room_page_copy_binds_unified_package_1013R_R21.html
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
