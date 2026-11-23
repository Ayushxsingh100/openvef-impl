"""D-002a broker protocol (runner side, src/openvef/sandbox.py).

The host side is runner/run_f18_container.sh; its end-to-end behaviour is exercised by
every containerized run. These tests pin the runner-side framing and the rule that the
runner cannot launch arbitrary commands through the broker.
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from openvef import sandbox  # noqa: E402


class BrokerProtocolTests(unittest.TestCase):
    def exchange(self, reply: str, request=None, timeout_s=7.5):
        out, inp = io.StringIO(), io.StringIO(reply)
        with mock.patch.dict(os.environ, {"OPENVEF_BROKER": "1"}), \
                mock.patch.object(sys, "__stdout__", out), mock.patch.object(sys, "__stdin__", inp):
            result = sandbox.run_harness(request or {"task": "factory"}, timeout_s)
        return out.getvalue(), result

    def test_request_framing(self):
        sent, _ = self.exchange("OPENVEF_SANDBOX_REPLY TIMEOUT\n", {"task": "checker", "x": "é"})
        marker, timeout, payload = sent.rstrip("\n").split(" ")
        self.assertEqual((marker, timeout), ("OPENVEF_SANDBOX_REQUEST", "7.5"))
        self.assertEqual(json.loads(base64.b64decode(payload)), {"task": "checker", "x": "é"})
        self.assertTrue(sent.endswith("\n") and sent.count("\n") == 1)

    def test_timeout_reply(self):
        _, r = self.exchange("OPENVEF_SANDBOX_REPLY TIMEOUT\n")
        self.assertEqual((r.timed_out, r.returncode, r.result), (True, None, None))

    def test_done_reply_parses_only_framed_result(self):
        stdout = b"noise\nOPENVEF_SANDBOX_RESULT {\"failure\": null}\n"
        reply = f"OPENVEF_SANDBOX_REPLY DONE 0 {base64.b64encode(stdout).decode()} {base64.b64encode(b'err').decode()}\n"
        _, r = self.exchange(reply)
        self.assertEqual((r.timed_out, r.returncode, r.result, r.stderr_tail), (False, 0, {"failure": None}, "err"))

    def test_done_reply_with_empty_output(self):
        _, r = self.exchange("OPENVEF_SANDBOX_REPLY DONE 137  \n")
        self.assertEqual((r.timed_out, r.returncode, r.result), (False, 137, None))

    def test_malformed_reply_is_unavailable_not_a_verdict(self):
        for reply in ("", "garbage\n", "OPENVEF_SANDBOX_REPLY MAYBE\n"):
            with self.assertRaises(sandbox.SandboxUnavailable):
                self.exchange(reply)

    def test_no_arbitrary_commands_in_broker_mode(self):
        with mock.patch.dict(os.environ, {"OPENVEF_BROKER": "1"}):
            with self.assertRaises(sandbox.SandboxUnavailable):
                sandbox.run_in_sandbox(["sh", "-c", "id"])

    def test_flags_have_one_source(self):
        flags = sandbox.artifact_flags("N")
        for required in ("--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                         "--user=10001:10001", "--name=N"):
            self.assertIn(required, flags)
        self.assertNotIn("{HARNESS_DIR}", " ".join(flags))


if __name__ == "__main__":
    unittest.main()
