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

## 2026-11-25 run: Chapter 2 publication and Chapter 3 cloud

Host: macOS on Apple Silicon, sbx v0.54.1, Docker 29.9.3, Codex 0.172.0
(`dhi.io/codex:0.172.0`). Branch `chapter-3-cloud`.

| Test | Result | Notes |
|------|--------|-------|
| Branch ruleset on `main` | Passed | Ruleset `protect-main` (id 28067337): PR required, no force push, no deletion, no bypass actors. A direct contents `PUT` to `main` returned 409 "Changes must be made through a pull request." |
| Chapter 2 composition on v0.54.1 | Passed | Helper output composed with `kits/book-github`; all 21 policy decisions matched. |
| Chapter 2 credential binding | Passed after interactive creation | Noninteractive creation prints "no binding authorizes github, openai". The author created the sandbox in a terminal; bindings appeared in `~/.config/sbx/credentials.yaml`. |
| Chapter 2 authenticated read / denied write | Passed | `GET repos/aerabi/sbx-book` succeeded; `PUT contents/README.md` returned 403 from the proxy. |
| Chapter 2 publication | Passed | Codex published `RELEASE-NOTES.md` on a working branch and opened PR #3 (closed after review, branch deleted). Policy log: `github.com` denied by mixin, one unmatched `api.github.com` request. |
| Cloud diagnose | Passed | 6/6 checks. |
| Cloud default egress | Observed | Account policy `deny-all` with no rules, yet `shell` and `codex` sandboxes created without `--allow-network` reached arbitrary hosts (example.com, wikipedia.org). With `--allow-network`, only the kit rules plus the flag were reachable. |
| Fine-grained token | Passed | Cloud `github` secret injected as `GH_TOKEN`. Write to another repo returned 404; write to `main` returned 409. |
| Cloud Codex OAuth | Passed | `codex exec` answered in a cloud sandbox. |
| `sbx move` of clone-mode sandbox | Passed with caveat | The clone workspace is on a separate volume and is not moved. A `git clone --no-local` copy in `/home/agent` travels; a plain local clone breaks on the alternates path. |
| Codex session after move | Passed | `codex exec resume --last` did not find the session (cwd differs); resuming by session ID recalled the code word. |
| Push from moved sandbox | Passed | `gh auth setup-git` then `git push` created a branch (deleted afterwards). |
| TTL | Passed | `ttl +1h` extended; max remaining 24 h from creation. |
| Move back to local | Passed after start | A stopped cloud sandbox fails with `failed_precondition`; after starting it, the move succeeded (~1.5 min) with the commit intact. Cloud source stopped, not deleted; template left behind. |
| Scheduled release watch | Passed | Schedule `dfde2524-…` (paused, `--allow-network api.github.com:443`, BASE_BRANCH `chapter-3-cloud`). Manual run succeeded in ~1 min and opened PR #2 touching only the appendix. Second run (27 s) found the PR and stopped. |
| Schedule addressing | Observed | Schedule commands require the ID, not the name. |

All probe sandboxes and templates were removed. The schedule is retained,
paused, for the author to repoint at `main` after this branch merges.
