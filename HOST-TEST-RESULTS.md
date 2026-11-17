# Host test results — 2026-11-17

Source: `f8024bc02a766fedcbd08d5b03570bc2633ac606` on `complete-chapter-2`.
The branch was already current after `git pull --ff-only`.
Evidence directory: `build/host-tests/run.6PARXL/` (ignored build artifacts).

## Results

| Check | Result | Evidence / limitation |
|---|---|---|
| Host environment | Passed | sbx v0.51.0; diagnostics: 15 passed, 1 update warning, 4 skipped. OS and Docker versions recorded. |
| Host Docker availability | Recovered | Both contexts initially lacked a running daemon. Started the installed Docker Desktop user service. |
| Pull Codex base | Blocked | `docker pull dhi.io/codex:0.169.0` and a retry returned registry 401 while fetching an anonymous token. Host Docker needs `docker login dhi.io`. No base digest could be recorded through Docker. |
| PDF template build/export/load | Blocked | Required base pull unavailable. No PDF test sandbox created. |
| Fresh PDF tools/fonts/build/render/copy | Unverified | Depends on the fresh template. Existing writing-sandbox builds are not substituted for this test. |
| Python environment | Passed with deviation | Standard venv creation failed because ensurepip is unavailable. Used `--without-pip --system-site-packages`; host PyYAML and jsonschema are available. |
| Export installed descriptor | Passed | Exported from `christmas-codex-fixed`; concrete Codex version is 0.169.0. |
| Derive workload | Helper ran; composition failed | GitHub API/Git host grants removed and all non-network capabilities preserved, but helper retained 207 `deb/` entries in `provides`. Builder rejects these as publishing-generated metadata. See `github-create.txt`. |
| Diagnostic composition | Passed with modification | A separate `book-codex-diagnostic` copy removes only the 207 `deb/` provides. Created `book-github-check` with the book mixin. Original helper and original generated output remain unchanged. See `github-create-diagnostic.txt`. |
| Effective policy | Passed on diagnostic composition | All 20 HTTP cases and the example.com:443 network case match expectations. Inspected actual Allowed/Denied results, not exit codes. See `github-policy-checks.txt` and `policy-summary.txt`. |
| GitHub CLI | Passed | Fresh diagnostic sandbox has gh 2.104.0. |
| Authenticated repository/issue reads | Pending credential | No verified repository-scoped read-only token supplied for the test sandbox. Existing token in the writing sandbox was not reused. |
| Publication | Blocked by checklist | No verified enforceable review boundary. No write token bound and no publication request sent. |

## Additional observations

- Global credential listing initially showed OpenAI OAuth and one GitHub secret
  scoped to `christmas-codex-fixed`; no global GitHub secret was listed.
- Noninteractive diagnostic creation reported that no binding authorized
  GitHub or OpenAI injection. Stored credentials and permission to inject them
  are separate requirements. Codex authentication has not passed this run.
- Global network grants include Ubuntu mirrors, download.docker.com, and
  cli.github.com. They did not widen any of the tested GitHub decisions.
- The policy checks sent no real destructive or publication requests.

## Remaining work

1. Authenticate host Docker to dhi.io, then perform the fresh PDF-template tests.
2. Helper correction completed and verified; see the follow-up below.
3. Supply the checklist's fine-grained read-only token, authorize its injection,
   and execute the two real reads.
4. Remove only test sandboxes after the remaining checks. `book-github-check`
   is retained for the pending credential test; `book-pdf-check` was not created.
   Existing writing sandboxes were not removed. Docker Desktop remains running.

Raw logs, generated workloads, and the Python environment are retained in the
evidence directory for review. No credentials were written to those logs.

## Follow-up: helper and documentation fixes

The working-tree helper now removes generated `deb/` provides while preserving
other provides. A regression test covers installed-descriptor package metadata,
retention of agent/tool declarations, and source immutability. All seven offline
tests pass, including the twenty policy cases.

Generated `book-codex-fixed` from the original exported descriptor with the
corrected helper. Its unmodified output successfully composed with the book
mixin in a new `book-github-fixed-check` sandbox. All 21 observed policy decisions
matched the expected results again. Evidence: `github-create-fixed.txt` and
`github-policy-checks-fixed.txt` in the original evidence directory. Removed
this fresh test-only sandbox afterward; the earlier `book-github-check` remains
available for the pending read test.

Chapter 2 and the host checklist now distinguish secret storage from interactive
injection authorization and document host Docker startup, dhi.io login, and
Python venv prerequisites. The chapter's introductory token command now uses a
prompt instead of putting a token in command arguments.

These checks do not resolve the PDF-template registry-login blocker or verify
real authenticated reads. The manuscript was updated; the PDF was not rebuilt
as part of this follow-up.
