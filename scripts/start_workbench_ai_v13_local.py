"""Start a minimal local Xiaobei workbench API server for v1.3 testing.

This server only exposes /api/workbench/* dry-run endpoints. It intentionally avoids
loading the production Feishu/OCR/upload server so local page testing stays safe.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.environ.setdefault("XIAOBEI_WORKBENCH_AI_CANDIDATE_ENABLED", "true")
    os.environ.setdefault("XIAOBEI_WORKBENCH_AI_MODE", "real_candidate")
    if (os.environ.get("MINIMAX_API_KEY") or os.environ.get("MINIAMX_API_KEY")) and not os.environ.get("XIAOBEI_WORKBENCH_AI_PROVIDER"):
        os.environ.setdefault("XIAOBEI_WORKBENCH_AI_PROVIDER", "anthropic_compatible")


_bootstrap()
from backend.xiaobei_ai import workbench_dry_run  # noqa: E402
from backend.xiaobei_ai import workbench_agent_runtime  # noqa: E402
from backend.xiaobei_ai import workbench_issue_capture  # noqa: E402
from backend.xiaobei_ai import kb_evidence_service  # noqa: E402
from backend.xiaobei_ai import prep_room_task_state_bridge_1013R_R6  # noqa: E402
from backend.xiaobei_ai import prep_room_in_page_model_quality_loop_1013R_R45_R47  # noqa: E402
from backend.xiaobei_ai import teaching_planning_business_pack_adapter_0998D  # noqa: E402
from backend.xiaobei_ai import teaching_planning_runtime_readonly_0998E  # noqa: E402


class WorkbenchHandler(BaseHTTPRequestHandler):
    server_version = "XiaobeiWorkbenchLocal/1.3"

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/workbench/session/mock":
            payload, status = workbench_dry_run.get_session_mock()
            return self._send_json(payload, status)
        if path == "/api/workbench/ai/status":
            payload, status = workbench_dry_run.ai_status()
            return self._send_json(payload, status)
        if path == "/api/workbench/teaching-planning/status":
            payload, status = teaching_planning_runtime_readonly_0998E.status()
            return self._send_json(payload, status)
        if path.startswith("/api/workbench/teaching-planning/session/"):
            session_id = unquote(path.rsplit("/", 1)[-1])
            payload, status = teaching_planning_runtime_readonly_0998E.get_session(session_id)
            return self._send_json(payload, status)
        if path.startswith("/api/workbench/teaching-planning/renderer-payload/"):
            session_id = unquote(path.rsplit("/", 1)[-1])
            payload, status = teaching_planning_runtime_readonly_0998E.get_renderer_payload(session_id)
            return self._send_json(payload, status)
        if path == "/api/workbench/download/manifest/mock":
            payload, status = workbench_dry_run.download_manifest_mock()
            return self._send_json(payload, status)
        if path == "/api/workbench/issues/list":
            payload, status = workbench_issue_capture.list_issues()
            return self._send_json(payload, status)
        if path == "/api/xiaobei/kb/status":
            payload, status = kb_evidence_service.status()
            return self._send_json(payload, status)
        if path == prep_room_task_state_bridge_1013R_R6.TASK_ROUTE:
            payload, status = prep_room_task_state_bridge_1013R_R6.handle_task_state_request()
            return self._send_json(payload, status)
        if path == prep_room_in_page_model_quality_loop_1013R_R45_R47.STATE_ROUTE:
            payload, status = prep_room_in_page_model_quality_loop_1013R_R45_R47.initial_state()
            return self._send_json(payload, status)
        return self._send_json({"error": "not_found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            payload = {}

        if path == "/api/workbench/ai/dry-run":
            data, status = workbench_dry_run.ai_dry_run(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/agent/turn":
            data, status = workbench_agent_runtime.run_runtime_dry_run(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/issues/capture":
            data, status = workbench_issue_capture.record_issue(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/intent/route":
            data, status = workbench_dry_run.intent_route(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/teaching-planning/semantic-turn":
            data, status = teaching_planning_business_pack_adapter_0998D.semantic_turn(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/candidate/accept-dry-run":
            data, status = workbench_dry_run.accept_candidate_dry_run(payload)
            return self._send_json(data, status)
        if path == "/api/workbench/candidate/discard-dry-run":
            data, status = workbench_dry_run.discard_candidate_dry_run(payload)
            return self._send_json(data, status)
        if path == "/api/xiaobei/kb/search_evidence":
            data, status = kb_evidence_service.search_evidence(payload)
            return self._send_json(data, status)
        if path == "/api/xiaobei/kb/get_chunk":
            data, status = kb_evidence_service.get_chunk(payload)
            return self._send_json(data, status)
        if path == "/api/xiaobei/kb/lesson_resources":
            data, status = kb_evidence_service.lesson_resources(payload)
            return self._send_json(data, status)
        if path == prep_room_task_state_bridge_1013R_R6.ACTION_ROUTE:
            data, status = prep_room_task_state_bridge_1013R_R6.handle_action_request(payload)
            return self._send_json(data, status)
        if path == prep_room_in_page_model_quality_loop_1013R_R45_R47.GENERATE_ROUTE:
            data, status = prep_room_in_page_model_quality_loop_1013R_R45_R47.generate_candidate(payload)
            return self._send_json(data, status)
        if path == prep_room_in_page_model_quality_loop_1013R_R45_R47.REGENERATE_ROUTE:
            data, status = prep_room_in_page_model_quality_loop_1013R_R45_R47.regenerate_candidate(payload)
            return self._send_json(data, status)
        return self._send_json({"error": "not_found"}, 404)

    def log_message(self, format: str, *args) -> None:
        print("[workbench-local] " + (format % args))


def main() -> int:
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "8082"))
    server = ThreadingHTTPServer((host, port), WorkbenchHandler)
    print("Xiaobei workbench v1.3 minimal local AI server")
    print(f"- URL: http://{host}:{port}")
    print(f"- Workbench API: http://{host}:{port}/api/workbench")
    print(f"- KB evidence API: http://{host}:{port}/api/xiaobei/kb")
    print(f"- Prep room task state: http://{host}:{port}/api/prep-room/task-state/g3_u2_color_gradient")
    print(f"- In-page model quality loop: http://{host}:{port}/api/prep-room/model-quality/state")
    print("- Real candidate guard: enabled")
    print("- Safety: no DB write, no Feishu write, no scoring, no classroom app, no real export")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
