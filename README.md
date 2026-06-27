# R45-R47 In-page Model Quality Loop Review

Start with the existing workbench page, not a standalone review page:

```text
http://127.0.0.1:5177/workbench/index.html?api=http%3A%2F%2F127.0.0.1%3A8084
```

The reviewed change mounts a model candidate sandbox inside `frontend/workbench/index.html`.

Boundaries:

```text
sandbox_only=true
formal_apply_allowed=false
save_performed=false
export_performed=false
database_written=false
feishu_written=false
memory_written=false
original_lesson_overwritten=false
```
