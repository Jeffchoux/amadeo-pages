import copy
import subprocess
import unittest
from unittest.mock import patch

import pages_publication as p

HEAD = "a" * 40
CANDIDATE = "b" * 40
PAGES = {"html_url": p.URL, "build_type": "legacy", "status": "built",
         "source": {"branch": "main", "path": "/"}}
BUILD = {"status": "built", "commit": HEAD, "error": {"message": None}, "updated_at": "today"}


class BindingTests(unittest.TestCase):
    def test_verified_binding(self):
        p.validate_binding(PAGES, BUILD, HEAD)

    def test_unknown_page_states_refuse(self):
        for state in [None, "building", "errored", "unknown"]:
            data = copy.deepcopy(PAGES)
            data["status"] = state
            with self.subTest(state=state), self.assertRaises(p.Refusal):
                p.validate_binding(data, BUILD, HEAD)

    def test_wrong_source_and_provider_refuse(self):
        variants = [{"source": {"branch": "develop", "path": "/"}},
                    {"source": {"branch": "main", "path": "/docs"}},
                    {"build_type": "workflow"}, {"html_url": "https://other.example/"}]
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(p.Refusal):
                p.validate_binding({**PAGES, **variant}, BUILD, HEAD)

    def test_build_unknown_or_failed_refuses(self):
        for variant in [{"status": "queued"}, {"commit": "unknown"}, {"error": None}, {"error": {}},
                        {"error": {"message": "failed"}}, {"commit": "c" * 40}]:
            with self.subTest(variant=variant), self.assertRaises(p.Refusal):
                p.validate_binding(PAGES, {**BUILD, **variant}, HEAD)

    def test_missing_response_refuses(self):
        with self.assertRaises(p.Refusal):
            p.validate_binding({}, {}, HEAD)


class InspectionTests(unittest.TestCase):
    def test_public_bytes_mismatch_refuses(self):
        with patch.object(p, "git", return_value=next(iter(p.ORIGINS))), \
             patch.object(p, "remote_main", return_value=HEAD), \
             patch.object(p, "api", side_effect=[PAGES, BUILD]), \
             patch.object(p, "command", return_value=b"source"), \
             patch.object(p, "public_file", return_value=b"stale"):
            with self.assertRaisesRegex(p.Refusal, "html_source_mismatch"):
                p.inspect()

    def test_remote_mutation_during_inspection_refuses(self):
        with patch.object(p, "git", return_value=next(iter(p.ORIGINS))), \
             patch.object(p, "remote_main", side_effect=[HEAD, CANDIDATE]), \
             patch.object(p, "api", side_effect=[PAGES, BUILD]), \
             patch.object(p, "command", return_value=b"source"), \
             patch.object(p, "public_file", return_value=b"source"):
            with self.assertRaisesRegex(p.Refusal, "remote_changed"):
                p.inspect()

    def test_live_inspection_returns_verified_sha(self):
        with patch.object(p, "git", return_value=next(iter(p.ORIGINS))), \
             patch.object(p, "remote_main", return_value=HEAD), \
             patch.object(p, "api", side_effect=[PAGES, BUILD]), \
             patch.object(p, "command", return_value=b"source"), \
             patch.object(p, "public_file", return_value=b"source"):
            result = p.inspect()
            self.assertEqual(result["head"], HEAD)
            self.assertEqual(result["state"], "READY")
            self.assertEqual(set(result["html_sha256"]), set(p.FILES))


class DeployTests(unittest.TestCase):
    def test_dirty_tree_refuses(self):
        with patch.object(p, "git", side_effect=[next(iter(p.ORIGINS)), " M confidentialite.html"]):
            with self.assertRaisesRegex(p.Refusal, "dirty"):
                p.candidate()

    def test_changes_beyond_reviewed_patch_refuse(self):
        with patch.object(p, "git", side_effect=[next(iter(p.ORIGINS)), "", CANDIDATE, "", "index.html"]):
            with self.assertRaisesRegex(p.Refusal, "exceeds_reviewed"):
                p.candidate()

    def test_diverged_candidate_refuses_push(self):
        with patch.object(p, "candidate", return_value=CANDIDATE), \
             patch.object(p, "inspect", return_value={"head": HEAD}), \
             patch.object(p, "git", side_effect=p.Refusal("not_ancestor")), \
             patch.object(p.subprocess, "run") as run:
            with self.assertRaises(p.Refusal):
                p.deploy()
            run.assert_not_called()

    def test_local_mutation_before_push_refuses(self):
        with patch.object(p, "candidate", side_effect=[CANDIDATE, "c" * 40]), \
             patch.object(p, "inspect", return_value={"head": HEAD}), \
             patch.object(p, "git", return_value=""), \
             patch.object(p.subprocess, "run") as run:
            with self.assertRaisesRegex(p.Refusal, "candidate_changed"):
                p.deploy()
            run.assert_not_called()

    def test_remote_mutation_before_push_refuses(self):
        with patch.object(p, "candidate", return_value=CANDIDATE), \
             patch.object(p, "inspect", return_value={"head": HEAD}), \
             patch.object(p, "git", return_value=""), \
             patch.object(p, "remote_main", return_value="c" * 40), \
             patch.object(p.subprocess, "run") as run:
            with self.assertRaisesRegex(p.Refusal, "remote_changed"):
                p.deploy()
            run.assert_not_called()

    def test_push_exact_candidate_without_force(self):
        with patch.object(p, "candidate", return_value=CANDIDATE), \
             patch.object(p, "inspect", return_value={"head": HEAD}), \
             patch.object(p, "git", return_value=""), \
             patch.object(p, "remote_main", side_effect=[HEAD, CANDIDATE]), \
             patch.object(p.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(p.deploy(), 0)
            self.assertEqual(run.call_args.args[0], ["git", "push", "origin", CANDIDATE + ":refs/heads/main"])

    def test_push_timeout_reports_unknown(self):
        with patch.object(p, "candidate", return_value=CANDIDATE), \
             patch.object(p, "inspect", return_value={"head": HEAD}), \
             patch.object(p, "git", return_value=""), \
             patch.object(p, "remote_main", return_value=HEAD), \
             patch.object(p.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 90)):
            with self.assertRaisesRegex(p.Refusal, "outcome_unknown"):
                p.deploy()


if __name__ == "__main__":
    unittest.main()
