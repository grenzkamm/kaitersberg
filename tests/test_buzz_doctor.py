from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "buzz-doctor.py"
SPEC = importlib.util.spec_from_file_location("buzz_doctor", SCRIPT)
assert SPEC and SPEC.loader
buzz_doctor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = buzz_doctor
SPEC.loader.exec_module(buzz_doctor)


class ProbeHandler(BaseHTTPRequestHandler):
    calls = 0

    def do_POST(self) -> None:
        type(self).calls += 1
        if self.headers.get("X-Webhook-Secret") != "test-secret":
            self.send_response(401)
        else:
            self.send_response(202)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        pass


class BuzzDoctorTest(unittest.TestCase):
    def test_log_facts_reads_transition_and_notification_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "loop.log"
            path.write_text(
                "\n".join([
                    json.dumps({"type": "kaitersberg_stage", "stage": "build", "run_id": "run-1"}),
                    json.dumps({
                        "type": "kaitersberg_transition", "stage": "build", "next_stage": "review",
                        "outcome": "complete", "run_id": "run-1",
                    }),
                    json.dumps({
                        "type": "kaitersberg_notification", "stage": "build", "next_stage": "review",
                        "exit_code": 22, "run_id": "run-1",
                    }),
                ]) + "\n",
                encoding="utf-8",
            )

            facts = buzz_doctor.log_facts(path)

            self.assertEqual(facts["stage"], "review")
            self.assertEqual(facts["run_id"], "run-1")
            self.assertEqual(facts["notification"]["exit_code"], 22)

    def test_diagnosis_prefers_failed_notification_over_stopped_loop(self) -> None:
        checks = [
            buzz_doctor.Check("Loop", "process", "warn", "stopped", code="loop_stopped"),
            buzz_doctor.Check("Buzz bridge", "notification", "fail", "exit 22", code="notification_failed"),
        ]
        summary, _ = buzz_doctor.diagnosis(checks, "PROJ-3")
        self.assertIn("notification hook failed", summary)

    def test_probe_uses_secret_without_returning_it(self) -> None:
        ProbeHandler.calls = 0
        server = HTTPServer(("127.0.0.1", 0), ProbeHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/hooks/test"
            with mock.patch.dict(os.environ, {"TEST_BUZZ_SECRET": "test-secret"}):
                result = buzz_doctor.probe_webhook(url, "TEST_BUZZ_SECRET")
            self.assertEqual(result.status, "ok")
            self.assertIn("HTTP 202", result.detail)
            self.assertNotIn("test-secret", result.detail)
            self.assertEqual(ProbeHandler.calls, 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_header_redaction(self) -> None:
        self.assertEqual(
            buzz_doctor.redacted("X-Webhook-Secret: very-secret"),
            "X-Webhook-Secret: <redacted>",
        )


if __name__ == "__main__":
    unittest.main()
