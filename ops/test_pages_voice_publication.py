"""Apply the established production/ancestry refusal suite to the new pinned adapter."""
import unittest
from unittest.mock import patch
import test_pages_publication as original_tests
import pages_voice_publication as reviewed


class UseNewAdapter:
    def setUp(self):
        self.binding = patch.object(original_tests, "p", reviewed)
        self.binding.start()
        self.addCleanup(self.binding.stop)


class BindingTests(UseNewAdapter, original_tests.BindingTests):
    pass


class InspectionTests(UseNewAdapter, original_tests.InspectionTests):
    pass


class DeployTests(UseNewAdapter, original_tests.DeployTests):
    def test_reviewed_content_with_ops_followup_is_allowed(self):
        with patch.object(reviewed, "git", side_effect=[next(iter(reviewed.ORIGINS)), "", original_tests.CANDIDATE, "", "ops/PUBLICATION.md"]):
            self.assertEqual(reviewed.candidate(), original_tests.CANDIDATE)

    def test_wrong_repository_refuses(self):
        with patch.object(reviewed, "git", return_value="https://github.com/other/repo.git"):
            with self.assertRaisesRegex(reviewed.Refusal, "repository_mismatch"):
                reviewed.candidate()


if __name__ == "__main__":
    unittest.main()
