from __future__ import annotations

import importlib.util
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "loop-dashboard.py"
DEMO = ROOT / "examples" / "demo-product"
SPEC = importlib.util.spec_from_file_location("loop_dashboard", SCRIPT)
assert SPEC and SPEC.loader
loop_dashboard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop_dashboard)


class LoopDashboardApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_directory = Path.cwd()
        os.chdir(DEMO)
        self.running = mock.patch.object(loop_dashboard, "running_loops", return_value=[])
        self.state = mock.patch.object(loop_dashboard, "loop_state", return_value={})
        self.running.start()
        self.state.start()

    def tearDown(self) -> None:
        self.state.stop()
        self.running.stop()
        os.chdir(self.previous_directory)

    def test_snapshot_exposes_the_dashboard_read_model(self) -> None:
        status, payload = loop_dashboard.api_route("/api/v1/snapshot")

        self.assertEqual(status, 200)
        self.assertEqual(payload["schema_version"], 1)
        self.assertIs(payload["read_only"], True)
        self.assertEqual(payload["project"], "demo-product")
        self.assertEqual(payload["status_counts"]["Roadmap"], 4)
        self.assertEqual(len(payload["features"]), 10)
        self.assertEqual(len(payload["bugs"]), 3)

        features = {feature["id"]: feature for feature in payload["features"]}
        self.assertIs(features["PROJ-5"]["pickable"], True)
        self.assertEqual(features["PROJ-8"]["waiting_on"], ["PROJ-3", "PROJ-6"])
        self.assertEqual(features["PROJ-3"]["task_progress"], {
            "total": 7,
            "done": 4,
            "in_progress": 1,
            "open": 2,
        })
        self.assertEqual(features["PROJ-3"]["reports"]["qa"]["open_findings"], 1)

    def test_feature_endpoint_uses_nulls_and_returns_a_json_error(self) -> None:
        status, payload = loop_dashboard.api_route("/api/v1/features/PROJ-1")
        self.assertEqual(status, 200)
        self.assertIsNone(payload["feature"]["owner"])
        self.assertIsNone(payload["feature"]["branch"])

        status, payload = loop_dashboard.api_route("/api/v1/features/PROJ-404")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "feature_not_found")

    def test_loop_state_api_uses_an_explicit_field_allowlist(self) -> None:
        state = loop_dashboard.loop_state_snapshot({
            "stage": "review",
            "last_outcome": "complete",
            "attempts": {"review": 1},
            "run_id": "internal-run-id",
            "future_sensitive_field": "must not leak",
        })

        self.assertEqual(state["stage"], "review")
        self.assertEqual(state["attempts"], {"review": 1})
        self.assertNotIn("run_id", state)
        self.assertNotIn("future_sensitive_field", state)

    def test_historical_em_dash_empty_marker_remains_readable(self) -> None:
        self.assertIsNone(loop_dashboard.api_value("\u2014"))

    def test_http_surface_allows_only_get_and_head(self) -> None:
        server = HTTPServer(("127.0.0.1", 0), loop_dashboard.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(base, timeout=5) as response:
                self.assertEqual(response.headers.get_content_type(), "text/html")
                self.assertIn(b"demo-product", response.read())

            with urllib.request.urlopen(f"{base}/api/v1/features", timeout=5) as response:
                payload = json.load(response)
                self.assertEqual(response.headers.get_content_type(), "application/json")
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                self.assertEqual(len(payload["features"]), 10)

            request = urllib.request.Request(f"{base}/api/v1/snapshot", method="HEAD")
            with urllib.request.urlopen(request, timeout=5) as response:
                self.assertEqual(response.read(), b"")
                self.assertGreater(int(response.headers["Content-Length"]), 0)

            request = urllib.request.Request(f"{base}/api/v1/features", data=b"{}", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(request, timeout=5)
            try:
                self.assertEqual(raised.exception.code, 405)
                self.assertEqual(raised.exception.headers["Allow"], "GET, HEAD")
                error = json.loads(raised.exception.read())
                self.assertEqual(error["error"]["code"], "method_not_allowed")
            finally:
                raised.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
