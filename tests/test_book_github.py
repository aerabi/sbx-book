"""Offline descriptor checks. These do not test Docker Sandboxes enforcement."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_book_codex", ROOT / "scripts/prepare-book-codex.py")
prepare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare_module)
MIXIN = yaml.safe_load((ROOT / "kits/book-github/kit.yaml").read_text())

# Representative grants from the installed Codex 0.169.0 descriptor.
WORKLOAD = {
    "schemaVersion": "3", "kind": "workload", "version": "0.169.0",
    "args": {"version": {"required": True}},
    "capabilities": [{
        "type": "com.docker.sandbox/network-policy@1",
        "config": {"runtime": {"allow": [
            "api.openai.com:443", "chatgpt.com:443", "api.github.com:443",
            "github.com:443", "release-assets.githubusercontent.com:443",
        ]}},
    }],
}


def matches(entry, method, url):
    """Project only the literal hosts and exact or trailing-/** paths in our cases.

    Not a general policy engine: query/path normalization and proxy enforcement
    belong to the runtime and must be verified by the host-side checks.
    """
    parsed = urlsplit(url)
    if isinstance(entry, str):
        return entry.split(":", 1)[0] == parsed.hostname
    if parsed.hostname not in [h.split(":", 1)[0] for h in entry["hosts"]]:
        return False
    methods = entry.get("methods")
    if methods and "ANY" not in methods and method not in methods:
        return False
    paths = entry.get("paths")
    return not paths or any(
        parsed.path == path or (path.endswith("/**") and parsed.path.startswith(path[:-2]))
        for path in paths
    )


def project(descriptors, method, url):
    entries = {"allow": [], "deny": []}
    for descriptor in descriptors:
        for cap in descriptor["capabilities"]:
            if cap["type"].startswith("com.docker.sandbox/network-policy@"):
                rules = cap.get("config", {}).get("runtime", {})
                for decision in entries:
                    entries[decision].extend(rules.get(decision, []))
    if any(matches(e, method, url) for e in entries["deny"]):
        return "deny"
    return "allow" if any(matches(e, method, url) for e in entries["allow"]) else "deny"


class BookGitHubTests(unittest.TestCase):
    def test_matrix_after_removing_workload_github_grants(self):
        workload, _ = prepare_module.prepare(WORKLOAD)
        for line in (ROOT / "kits/book-github/policy-cases.tsv").read_text().splitlines():
            expected, method, url = line.split("\t")
            with self.subTest(method=method, url=url):
                self.assertEqual(project([workload, MIXIN], method, url), expected)

    def test_original_workload_widens_mixin_and_exposes_merge(self):
        url = "https://api.github.com/repos/aerabi/sbx-book/pulls/1/merge"
        self.assertEqual(project([MIXIN], "PUT", url), "deny")
        self.assertEqual(project([WORKLOAD, MIXIN], "PUT", url), "allow")

    def test_prepare_preserves_source_and_non_github_access(self):
        before = deepcopy(WORKLOAD)
        result, version = prepare_module.prepare(WORKLOAD)
        self.assertEqual(WORKLOAD, before)
        self.assertEqual(version, "0.169.0")
        self.assertEqual(project([result], "POST", "https://api.openai.com/v1/responses"), "allow")
        self.assertEqual(project([result], "POST", "https://api.github.com/graphql"), "deny")

    def test_wildcard_source_grants_require_manual_review(self):
        source = deepcopy(WORKLOAD)
        source["capabilities"][0]["config"]["runtime"]["allow"].append("**")
        with self.assertRaises(ValueError):
            prepare_module.prepare(source)

    def test_credential_injection_is_only_for_allowed_api(self):
        creds = next(c for c in MIXIN["capabilities"] if c["type"].endswith("/credential@1"))
        api_key = creds["config"]["apiKey"]
        self.assertTrue(api_key["proxyManaged"])
        self.assertEqual([e["domain"] for e in api_key["inject"]], ["api.github.com"])
        self.assertEqual(project([MIXIN], "GET", "https://api.github.com/repos/aerabi/sbx-book"), "allow")

    def test_agent_context_is_available(self):
        context = next(c for c in MIXIN["capabilities"] if c["type"].endswith("/agent-context@1"))
        self.assertTrue((ROOT / "kits/book-github" / context["config"]["contentFile"]).is_file())


if __name__ == "__main__":
    unittest.main()
