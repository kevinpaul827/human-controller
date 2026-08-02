import os
import plistlib
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

from scripts import build_macos_app


class MacOSHelperPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app_bundle = Path(self.temp_dir.name) / "Human Controller.app"
        self.source_executable = (
            self.app_bundle / "Contents" / "MacOS" / "Human Controller"
        )
        self.helper_bundle = (
            self.app_bundle
            / "Contents"
            / "Helpers"
            / "Human Controller PiP.app"
        )
        self.helper_executable = (
            self.helper_bundle
            / "Contents"
            / "MacOS"
            / "Human Controller PiP"
        )
        self.source_executable.parent.mkdir(parents=True)
        (self.app_bundle / "Contents" / "Frameworks").mkdir()
        (self.app_bundle / "Contents" / "Resources").mkdir()
        self.source_executable.write_bytes(b"frozen executable")
        self.source_executable.chmod(0o755)
        self.path_patches = (
            patch.object(
                build_macos_app,
                "APP_BUNDLE_PATH",
                self.app_bundle,
            ),
            patch.object(
                build_macos_app,
                "PIP_HELPER_APP_PATH",
                self.helper_bundle,
            ),
            patch.object(
                build_macos_app,
                "PIP_HELPER_EXECUTABLE_PATH",
                self.helper_executable,
            ),
        )
        for path_patch in self.path_patches:
            path_patch.start()

    def tearDown(self):
        for path_patch in reversed(self.path_patches):
            path_patch.stop()
        self.temp_dir.cleanup()

    @patch.object(build_macos_app.subprocess, "run")
    def test_helper_bundle_has_agent_identity_and_shared_runtime(self, run):
        run.return_value = SimpleNamespace(returncode=0)
        stale_file = self.helper_bundle / "stale"
        stale_file.parent.mkdir(parents=True)
        stale_file.write_text("old", encoding="utf-8")

        created = build_macos_app.create_pip_helper_bundle()

        self.assertTrue(created)
        self.assertFalse(stale_file.exists())
        self.assertEqual(
            self.helper_executable.read_bytes(),
            self.source_executable.read_bytes(),
        )
        self.assertTrue(
            self.helper_executable.stat().st_mode & stat.S_IXUSR
        )
        helper_contents = self.helper_bundle / "Contents"
        self.assertEqual(
            os.readlink(helper_contents / "Frameworks"),
            "../../../Frameworks",
        )
        self.assertEqual(
            os.readlink(helper_contents / "Resources"),
            "../../../Resources",
        )
        with (helper_contents / "Info.plist").open("rb") as plist_file:
            info = plistlib.load(plist_file)
        self.assertEqual(info["CFBundleExecutable"], "Human Controller PiP")
        self.assertEqual(
            info["CFBundleIdentifier"],
            "au.edu.unsw.capstone.date.human-controller.pip",
        )
        self.assertEqual(info["CFBundlePackageType"], "APPL")
        self.assertIs(info["LSUIElement"], True)
        self.assertNotIn("NSCameraUsageDescription", info)

    @patch.object(build_macos_app.subprocess, "run")
    def test_helper_is_signed_before_outer_bundle_and_strictly_verified(
        self,
        run,
    ):
        run.return_value = SimpleNamespace(returncode=0)

        created = build_macos_app.create_pip_helper_bundle()

        self.assertTrue(created)
        self.assertEqual(
            run.call_args_list,
            [
                call(
                    [
                        "codesign",
                        "--force",
                        "--sign",
                        "-",
                        str(self.helper_bundle),
                    ],
                    check=False,
                ),
                call(
                    [
                        "codesign",
                        "--force",
                        "--sign",
                        "-",
                        str(self.app_bundle),
                    ],
                    check=False,
                ),
                call(
                    [
                        "codesign",
                        "--verify",
                        "--deep",
                        "--strict",
                        str(self.app_bundle),
                    ],
                    check=False,
                ),
            ],
        )

    @patch.object(build_macos_app.subprocess, "run")
    def test_missing_main_executable_fails_before_signing(self, run):
        self.source_executable.unlink()

        created = build_macos_app.create_pip_helper_bundle()

        self.assertFalse(created)
        run.assert_not_called()

    @patch.object(build_macos_app.subprocess, "run")
    def test_signing_failure_stops_packaging(self, run):
        run.return_value = SimpleNamespace(returncode=1)

        created = build_macos_app.create_pip_helper_bundle()

        self.assertFalse(created)
        self.assertEqual(run.call_count, 1)

    @patch.object(build_macos_app.subprocess, "run")
    def test_strict_verification_failure_stops_packaging(self, run):
        run.side_effect = (
            SimpleNamespace(returncode=0),
            SimpleNamespace(returncode=0),
            SimpleNamespace(returncode=1),
        )

        created = build_macos_app.create_pip_helper_bundle()

        self.assertFalse(created)
        self.assertEqual(run.call_count, 3)

    def test_main_bundle_remains_a_regular_application(self):
        self.assertNotIn("LSUIElement", build_macos_app.SPEC_TEMPLATE)
        self.assertIn(
            'bundle_identifier="au.edu.unsw.capstone.date.human-controller"',
            build_macos_app.SPEC_TEMPLATE,
        )


if __name__ == "__main__":
    unittest.main()
