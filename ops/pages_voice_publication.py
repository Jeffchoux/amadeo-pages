#!/usr/bin/env python3
"""Reviewed voice/privacy update adapter, 2026-10-29; predecessor remains unchanged.

Only invoke deploy through control.py deploy (lock, Git ancestry and budget).
Publication is a non-forced push to the configured Pages source branch, main.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
REPO = "jeffchoux/amadeo-pages"
URL = "https://jeffchoux.github.io/amadeo-pages/"
PATCH = "ef0ce196798dc1fb51a0e0f1f48f7e43ebf21f76"
FILES = ("index.html", "confidentialite.html")
SHA = re.compile(r"[0-9a-f]{40}\Z")
ORIGINS = {"https://github.com/Jeffchoux/amadeo-pages.git", "git@github.com:Jeffchoux/amadeo-pages.git"}


class Refusal(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise Refusal(reason)


def command(args, timeout=8):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise Refusal("command_unavailable:" + args[0]) from None
    require(result.returncode == 0, "command_failed:" + args[0])
    return result.stdout


def git(*args):
    return command(["git", *args]).decode().strip()


def api(path):
    try:
        value = json.loads(command(["gh", "api", "repos/" + REPO + path]))
    except (ValueError, UnicodeDecodeError):
        raise Refusal("github_response_malformed") from None
    require(isinstance(value, dict), "github_response_malformed")
    return value


def remote_main():
    lines = git("ls-remote", "--refs", "origin", "refs/heads/main").splitlines()
    require(len(lines) == 1, "remote_main_missing_or_ambiguous")
    fields = lines[0].split()
    require(len(fields) == 2 and SHA.fullmatch(fields[0])
            and fields[1] == "refs/heads/main", "remote_main_malformed")
    return fields[0]


def public_file(name):
    try:
        with urllib.request.urlopen(URL + name, timeout=6) as response:
            require(response.status == 200 and response.url == URL + name, "public_page_redirect_or_status")
            value = response.read(1024 * 1024 + 1)
    except (OSError, urllib.error.URLError):
        raise Refusal("public_page_unavailable") from None
    require(len(value) <= 1024 * 1024, "public_page_oversized")
    return value


def validate_binding(pages, build, head):
    require(pages.get("html_url") == URL and pages.get("build_type") == "legacy"
            and pages.get("status") == "built" and pages.get("source") == {"branch": "main", "path": "/"},
            "pages_binding_or_status_mismatch")
    require(build.get("status") == "built" and isinstance(build.get("commit"), str)
            and SHA.fullmatch(build["commit"]), "pages_build_unknown")
    require(isinstance(build.get("error"), dict) and "message" in build["error"]
            and build["error"]["message"] is None,
            "pages_build_error_unknown")
    require(build["commit"] == head, "remote_head_not_current_deployment")


def inspect():
    require(git("remote", "get-url", "origin") in ORIGINS, "repository_mismatch")
    head = remote_main()
    pages, build = api("/pages"), api("/pages/builds/latest")
    validate_binding(pages, build, head)
    git("fetch", "--no-tags", "--no-write-fetch-head", "origin", head)
    hashes = {}
    for name in FILES:
        source = command(["git", "show", head + ":" + name])
        served = public_file(name)
        require(source == served, "public_html_source_mismatch:" + name)
        hashes[name] = hashlib.sha256(served).hexdigest()
    require(remote_main() == head, "remote_changed_during_inspection")
    return {"id": "github-pages:" + REPO, "name": "Amadeo public pages",
            "kind": "github-pages", "repo": REPO, "state": "READY", "head": head,
            "url": URL, "aliases": [URL], "deployment": build.get("updated_at"),
            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(), "html_sha256": hashes}


def candidate():
    require(git("remote", "get-url", "origin") in ORIGINS, "repository_mismatch")
    require(not git("status", "--porcelain"), "working_tree_dirty")
    head = git("rev-parse", "HEAD")
    require(SHA.fullmatch(head), "candidate_sha_malformed")
    git("merge-base", "--is-ancestor", PATCH, head)
    changed = git("diff", "--name-only", PATCH, head).splitlines()
    require(all(name.startswith("ops/") for name in changed), "candidate_exceeds_reviewed_privacy_patch")
    return head


def deploy():
    head = candidate()
    production = inspect()  # Fresh binding, build SHA and public bytes, not cached evidence.
    git("merge-base", "--is-ancestor", production["head"], head)
    require(candidate() == head, "candidate_changed_during_preflight")
    require(remote_main() == production["head"], "remote_changed_before_push")
    print(json.dumps({"publication": "github-pages", "candidate": head,
                      "previous_production": production["head"]}), flush=True)
    # No force or bypass option; server-side protections and fast-forward checks apply.
    try:
        result = subprocess.run(["git", "push", "origin", head + ":refs/heads/main"],
                                cwd=ROOT, timeout=90)
    except subprocess.TimeoutExpired:
        raise Refusal("push_timeout_outcome_unknown_reconcile_before_retry") from None
    require(result.returncode == 0, "push_failed_reconcile_remote")
    require(remote_main() == head, "remote_changed_after_push")
    print(json.dumps({"push_succeeded": True, "candidate": head,
                      "pages_deployment_verified": False}), flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inspect", "deploy"])
    args = parser.parse_args()
    try:
        if args.action == "inspect":
            print(json.dumps(inspect()))
            return 0
        return deploy()
    except (Refusal, OSError, ValueError, KeyError) as error:
        reason = str(error) if isinstance(error, Refusal) else "verification_failed"
        print(json.dumps({"allowed": False, "reason": reason}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
