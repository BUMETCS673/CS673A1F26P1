# AI-USAGE SUMMARY
# Authors: OpenAI Codex, requested by Ji Wu
# Tools: OpenAI Codex
# AI-Assisted Areas: FV-109 negative controls for benchmark failures and cleanup
# Human Contributions: Ji Wu supplied the implementation request and plan.
# Notes/Verification: no server, database or browser required; HTTP is simulated.

"""Ensure the performance check cannot silently pass an unsuccessful workload."""

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock

import httpx2 as httpx

SOURCE = Path(__file__).resolve().parents[2] / "browser_checks" / "speed_check.py"
SPEC = importlib.util.spec_from_file_location("speed_check", SOURCE)
speed = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(speed)


class SpeedCheckTests(unittest.TestCase):
    def setUp(self):
        self.clients = []
        self.cleaned = []
        self.output = io.StringIO()
        capture = contextlib.redirect_stdout(self.output)
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)

    def factory(self, handler):
        def create(**options):
            client = httpx.Client(**options, transport=httpx.MockTransport(handler))
            self.clients.append(client)
            return client
        return create

    @staticmethod
    def healthy(request):
        return httpx.Response(201 if request.url.path.endswith("register") else 200, json={})

    def run_check(self, handler=None, **options):
        return speed.run(2, 2, client_factory=self.factory(handler or self.healthy),
                         cleanup=self.cleaned.append, **options)

    def assert_cleaned(self, count=2):
        self.assertEqual(len(self.cleaned), count)
        self.assertEqual(len(set(self.cleaned)), count)
        self.assertTrue(all(client.is_closed for client in self.clients))

    def test_complete_successful_workload_returns_zero_and_cleans_accounts(self):
        self.assertEqual(self.run_check(), 0)
        self.assert_cleaned()
        self.assertIn("browser rendering not measured", self.output.getvalue())

    def test_http_503_is_nonzero_without_exposing_response_body(self):
        def handler(request):
            if request.url.path == "/api/chat":
                return httpx.Response(503, text="secret database settings")
            return self.healthy(request)
        self.assertEqual(self.run_check(handler), 1)
        self.assertIn("HTTP 503", self.output.getvalue())
        self.assertNotIn("secret database settings", self.output.getvalue())
        self.assert_cleaned()

    def test_timeout_is_recorded_and_does_not_drop_workload_samples(self):
        def handler(request):
            raise httpx.ReadTimeout("do not print this URL or credential", request=request)
        client = httpx.Client(base_url=speed.BASE, transport=httpx.MockTransport(handler))
        self.addCleanup(client.close)
        samples, errors, _ = speed.workload([client], 2)
        self.assertEqual(len(samples), 6)
        self.assertEqual(len(errors), 6)
        self.assertTrue(all(item["error"] == "ReadTimeout" for item in errors))
        self.assertEqual(len(speed.failures(samples, errors, 1, 2, 3000)), 6)

    def test_unexpected_worker_crash_fails_and_cleans_up(self):
        def handler(request):
            if request.url.path == "/api/chat":
                raise RuntimeError("worker crashed")
            return self.healthy(request)
        self.assertEqual(self.run_check(handler), 1)
        self.assertIn("setup/workload failed", self.output.getvalue())
        self.assert_cleaned()

    def test_setup_failure_cleans_successful_and_partially_created_accounts(self):
        registrations = 0

        def handler(request):
            nonlocal registrations
            if request.url.path.endswith("register"):
                registrations += 1
            if registrations == 2 and request.url.path.endswith("login"):
                return httpx.Response(503)
            return self.healthy(request)
        self.assertEqual(self.run_check(handler), 1)
        self.assert_cleaned()

    def test_one_slow_response_fails_even_when_median_is_fast(self):
        samples = [{"path": path, "ms": 10} for path in ("chat", "history", "plans") for _ in range(20)]
        samples[0]["ms"] = 3001
        problems = speed.failures(samples, [], 1, 20, 3000)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0]["ms"], 3001)
        samples[0]["ms"] = 3000
        self.assertEqual(speed.failures(samples, [], 1, 20, 3000), [])

    def test_missing_samples_fail_even_when_no_http_error_was_reported(self):
        problems = speed.failures([], [], 10, 20, 3000)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all("0/200" in problem["error"] for problem in problems))

    def test_run_returns_nonzero_for_incomplete_workload(self):
        self.assertEqual(self.run_check(benchmark=lambda *_: ([], [], 1)), 1)
        self.assert_cleaned()

    def test_cleanup_failure_is_nonzero_and_other_accounts_still_get_cleaned(self):
        def cleanup(username):
            self.cleaned.append(username)
            raise RuntimeError("cleanup unavailable")
        result = speed.run(2, 1, client_factory=self.factory(self.healthy), cleanup=cleanup)
        self.assertEqual(result, 1)
        self.assert_cleaned()

    def test_import_has_no_network_or_database_side_effects(self):
        with mock.patch.object(httpx, "Client", side_effect=AssertionError("network on import")):
            module = importlib.util.module_from_spec(SPEC)
            SPEC.loader.exec_module(module)

    def test_invalid_workload_sizes_are_rejected_before_any_request(self):
        for arguments in (["0"], ["-1"], ["2", "--rounds", "0"], ["--max-chat-ms", "0"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    speed.main(arguments)
                self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
