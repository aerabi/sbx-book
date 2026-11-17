# Pending host tests

Run these from the **host**, in the `aerabi/sbx-book` checkout on
`complete-chapter-2`. These checks need the host `sbx` CLI and daemon.
The writing guest cannot run them. See [HOST-TEST-RESULTS.md](HOST-TEST-RESULTS.md)
for the 2026-11-17 host run, including the helper failure, diagnostic policy
results, and remaining authentication blockers. Checkboxes below retain the
original acceptance sequence; diagnostic workarounds do not mark it passed.

Already passed in the writing guest: Official Kit schema validation, six
offline tests covering twenty request cases, and PDF/HTML/EPUB/DOCX builds.
Those results do not verify a freshly built template or composed sandbox.

## Record the environment

- [ ] Pull the PR branch and record the source revision and host tool versions.

```bash
git switch complete-chapter-2
git pull --ff-only
mkdir -p build/host-tests
book_test_dir=$(mktemp -d "$PWD/build/host-tests/run.XXXXXX")
git rev-parse HEAD > "$book_test_dir/source-commit.txt"
sbx --version > "$book_test_dir/sbx-version.txt"
docker version > "$book_test_dir/docker-version.txt"
sbx diagnose
```

Use the same host terminal for subsequent commands using `book_test_dir`.
Record OS and architecture in that directory too. Do not log token values.
If a sandbox name below already exists, choose a new name consistently;
do not replace an existing writing sandbox.

## Build and start the Codex PDF template

- [ ] Resolve the base image and record its digest. The example version is
  from the installed guest descriptor; confirm it suits the host sbx release.

```bash
docker version  # Must include a reachable server
docker login dhi.io
docker pull dhi.io/codex:0.169.0
docker image inspect dhi.io/codex:0.169.0 --format '{{json .RepoDigests}}' \
  > "$book_test_dir/codex-base-digests.txt"
```

If Docker reports a missing daemon socket, start Docker Desktop or the host
Docker Engine service and verify the selected context. On Linux with Docker
Desktop installed, use `systemctl --user start docker-desktop`. An sbx login
is separate from host Docker's registry login. A registry 401 must be resolved
before continuing.

Registry requests from the writing guest previously required host network
approval. If a request is blocked, retain its explanation and resolve that
specific access requirement before continuing.

- [ ] Build the template, export it, and load it into sbx.

```bash
docker build --build-arg BASE_IMAGE=dhi.io/codex:0.169.0 \
  -t christmas-codex-tools:1 ./sbx-template
docker image save christmas-codex-tools:1 \
  -o "$book_test_dir/christmas-codex-tools-1.tar"
sbx template load "$book_test_dir/christmas-codex-tools-1.tar"
```

Expected: All three commands complete. Keep the image digest and build output.
For subsequent reproducible base selection, use the reviewed digest instead
of the tag in `BASE_IMAGE`.

- [ ] Configure OpenAI authentication as described in Chapter 2 before
  creation, then create and start a fresh PDF-writing sandbox.

```bash
sbx create --name book-pdf-check --clone \
  --template christmas-codex-tools:1 --pull never codex .
sbx policy ls book-pdf-check --wide
sbx run --name book-pdf-check
```

Review and authorize the intended credential destinations in the interactive
creation/startup prompts. If output says "no binding authorizes" a service,
its stored secret was not injected. Re-run interactively to review the prompt;
do not use `--no-input` for this authentication acceptance test.

Expected: Codex starts without needing copied guest credential files.
Use another host terminal for `sbx exec` while it is running.

- [ ] Verify the tools and fonts in that **new** sandbox.

```bash
sbx exec book-pdf-check -- codex --version
sbx exec book-pdf-check -- pandoc --version
sbx exec book-pdf-check -- xelatex --version
sbx exec book-pdf-check -- latexmk --version
sbx exec book-pdf-check -- fc-match 'Libertinus Serif'
sbx exec book-pdf-check -- fc-match 'Fira Code Retina'
```

Expected: Tools are present and font matches identify the requested families
and styles. A successful `fc-match` exit alone does not rule out substitution.

- [ ] In the sandbox's book checkout, run `make pdf`. Inspect the resulting
  title sequence, subtitle, code listings, and bibliography.
- [ ] Copy `build/pdf/book.pdf` from that guest checkout to the host using
  `sbx cp`, as shown in Chapter 2. Record the guest path and host artifact path.

Expected: PDF compilation succeeds in the fresh template without manually
installing missing tools or copying fonts. There is one half-title,
frontispiece, and full-title sequence; the subtitle appears once.

## Prepare the repository-specific GitHub composition

- [ ] Prepare a Python environment for the workload helper.

```bash
python3 -m venv "$book_test_dir/venv"
. "$book_test_dir/venv/bin/activate"
python3 -m pip install PyYAML jsonschema
```

If `venv` reports missing `ensurepip`, install the distribution's venv package
(for example, `python3-venv` on Debian/Ubuntu), then retry environment creation.

- [ ] Export and review the installed workload descriptor. The example
  source sandbox is the author's current writing sandbox; substitute an
  existing Codex sandbox if necessary.

```bash
sbx exec christmas-codex-fixed -- cat /usr/share/sandbox/kit/codex/kit.yaml \
  > "$book_test_dir/codex-source.yaml"
python3 scripts/prepare-book-codex.py \
  "$book_test_dir/codex-source.yaml" "$book_test_dir/book-codex"
cat "$book_test_dir/book-codex/kit.yaml"
cat "$book_test_dir/book-codex/codex.dockerfile"
```

Expected: GitHub host allow grants are removed from the derived workload.
OpenAI authentication, other capabilities, and startup hooks are preserved.
Generated `deb/` entries in `provides` are removed so the builder can derive
package metadata from the image; other provides remain intact.
Review the generated base reference and its digest. The helper deliberately
refuses to overwrite an existing output directory or guess at wildcard grants.

- [ ] Inspect existing host credential bindings before creation. Do not
  assume a missing sandbox-scoped token means there is no global binding.
  Use a repository-scoped read-only credential for the read test below.
- [ ] Create the sandbox with the derived workload, rather than the built-in
  workload whose broad GitHub grant would widen the policy.

```bash
sbx create --name book-github-check --clone \
  --kit ./kits/book-github "$book_test_dir/book-codex" .
sbx policy ls book-github-check --wide \
  > "$book_test_dir/github-effective-policy.txt"
```

Expected: The local workload and declaration-only mixin compose successfully.
No unrelated global grant restores unrestricted API access.

## Evaluate the effective policy

- [ ] Run the complete policy matrix and retain the output.

```bash
sh scripts/check-book-github-policy.sh book-github-check \
  > "$book_test_dir/github-policy-checks.txt" 2>&1
cat "$book_test_dir/github-policy-checks.txt"
```

Compare **every** actual decision with the expectation printed beside it.
The script does not automatically interpret decisions or infer them from
exit codes. CLI errors leave a case unverified.

Expected: Repository reads, PUT for `RELEASE-NOTES.md`, and POST for PR creation
are allowed. The following are denied:

- [ ] Repository, file, and branch DELETE requests.
- [ ] Repository PATCH, issue creation, PR merge, and ref creation.
- [ ] Writes to README and chapter files, and access to other repositories.
- [ ] GraphQL POST, HTTPS Git push, and uploads.
- [ ] The unrelated destination `example.com:443`.

All these are **policy evaluations**, not HTTP requests. Never send a real
DELETE, merge, or other destructive request to test denial. Stop on any
unexpected decision and inspect workload, mixin, global, and organization rules.

## Verify a real authenticated read

- [ ] Bind a fine-grained read-only token for `aerabi/sbx-book` on the host.
  It needs repository metadata and issue reads for these checks.

```bash
sbx secret set github --sandbox book-github-check
sbx run --name book-github-check
```

Review the interactive binding prompt and authorize only the intended REST API
destination. `sbx secret ls` confirms storage, not permission to inject a secret.
Do not substitute a broad `gh auth token` credential for the required
repository-scoped read-only token.

In another host terminal:

```bash
sbx exec book-github-check -- gh --version
sbx exec book-github-check -- gh api --method GET repos/aerabi/sbx-book
sbx exec book-github-check -- gh api --method GET \
  'repos/aerabi/sbx-book/issues?state=closed&per_page=10'
```

Expected: The CLI is available and both authenticated reads return GitHub
responses. Preserve error bodies if they fail; a GitHub permissions error
does not prove that the proxy enforced a denial. Do not print the token.

## Test publication — currently blocked

The writing-session checks reported `main` as unprotected. GitHub's rulesets
and branch-protection APIs returned an account-plan limitation for this private
repository. The PUT policy cannot inspect the branch named in the request
body. **Do not bind a write token or run this publication test until an
enforceable review boundary exists.** This checklist does not authorize
changing repository visibility, an account plan, or protection settings.

- [ ] Verify protection of all base/release branches without bypass by the
  credential identity, or verify a broker enforcing branch and content limits.
  Record the control and evidence. If unavailable, leave the rest blocked.
- [ ] Have the author prepare a dedicated working branch on the host and
  record the base branch SHA before the test.
- [ ] Bind a fine-grained token limited to this repository with Contents write,
  Pull requests write, and Issues read.
- [ ] Through the new sandbox, PUT only `RELEASE-NOTES.md` to that existing
  working branch using its branch-specific file SHA when updating.
- [ ] POST a PR through the REST API and record its URL. Do not merge it.
- [ ] Inspect the PR diff, confirm only the intended file changed, and confirm
  the base branch SHA did not move during the test.

Expected: The agent can submit the intended proposal for review. A successful
PR alone does not prove branch enforcement, and a denied DELETE endpoint does
not prevent an allowed file update from replacing its contents incorrectly.

## Record results and clean up

- [ ] For each section, record date, source commit, command output, actual
  result, and any remaining blocker. Mark a test passed only after observing
  its result on the host.
- [ ] Preserve the PDFs, policy records, and any PR needed for review.
- [ ] Exit sessions and remove only the test sandboxes created above.

```bash
sbx rm book-pdf-check book-github-check
```

Omit a name if you did not create that sandbox. Templates, image archives,
builder caches, generated workloads, and the Python environment have separate
lifecycles; retain them until the results have been reviewed.
