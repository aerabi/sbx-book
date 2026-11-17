# GitHub access for the SBX book

This is a real v3 declaration-only mixin for `aerabi/sbx-book`. It binds a
proxy-managed credential, adds agent context, and requests REST repository
reads, PUT for `RELEASE-NOTES.md`, and POST for PR creation. The compatible
Codex image already installs `gh`; this mixin does not install another CLI.

DELETE and PATCH are denied on the API. `github.com` and `uploads.github.com`
are denied entirely; POST to GraphQL is denied explicitly. The token is
injected only into `api.github.com`.

## The workload matters

The installed Codex 0.169.0 workload grants `api.github.com` unbounded access.
Kit allow entries combine by union. Composing this mixin directly with that
workload would still allow unlisted API writes, including PR merges.
`scripts/prepare-book-codex.py` derives a local workload from a reviewed
installed descriptor, removing the GitHub host grants while preserving its
other capabilities. It rejects wildcard grants for manual review. It writes
an image recipe for that descriptor's DHI Codex version; inspect and pin the
base digest before use. Different versions/image families need a new review.

## Prepare and check on the host

Run from the book checkout. Install PyYAML for the helper and test suite;
JSON Schema validation additionally uses jsonschema. Prefer an isolated
Python environment, for example:

```bash
python3 -m venv /tmp/book-kit-venv
. /tmp/book-kit-venv/bin/activate
python3 -m pip install PyYAML jsonschema
```

Export the reviewed descriptor from the writing sandbox. In the book's earlier
exercise this sandbox is `christmas-codex`; in the author's current session it
is `christmas-codex-fixed`. Choose the name that exists on your host:

```bash
sbx exec christmas-codex-fixed -- cat /usr/share/sandbox/kit/codex/kit.yaml \
  > /tmp/book-codex-source.yaml
python3 scripts/prepare-book-codex.py /tmp/book-codex-source.yaml build/book-codex
cat build/book-codex/kit.yaml
cat build/book-codex/codex.dockerfile
sbx create --name book-github-check --clone \
  --kit ./kits/book-github ./build/book-codex .
sh scripts/check-book-github-policy.sh book-github-check
```

The helper refuses to overwrite its output directory. Choose a new output
path when regenerating, and pass that same path to `sbx create`.

The script evaluates each row in `policy-cases.tsv` using the real host policy
engine. It prints expected decisions beside CLI output for human comparison;
it does not infer authorization from process exit codes. It sends **no HTTP
requests**, including no DELETE requests. Unexpected results or CLI errors
mean stop and inspect active rules. Global policies and other mixins can widen
access too. Inspect existing global credential bindings before creation; the
absence of a sandbox-scoped binding does not establish that none is available.

After the decisions match, start the sandbox in another terminal and check:

```bash
sbx run --name book-github-check
```

From a host terminal:

```bash
sbx exec book-github-check -- gh --version
sbx exec book-github-check -- gh api --method GET repos/aerabi/sbx-book
```

The repository is private, so that read requires a suitable credential. A
read-only token is sufficient for this read test. It is separate from the
write credential discussed below. Keep the HTTP status/error body when a
request fails; a GitHub permission error is not proof of proxy enforcement.

## Publication boundary

The PUT endpoint accepts a branch in the request body. The policy cannot
restrict that value. A Contents-write token can also overwrite or empty the
allowed file; denying DELETE does not prevent every destructive edit.

Require base/release branches to enforce PR review without bypass by the
credential identity, or use a broker that validates branch and content.
GitHub reports `main` as unprotected; both the rulesets and branch-protection
APIs report that this private repository needs an upgraded plan or public
visibility for those features. Do not delegate
writes with this setup until the review boundary is actually enforced.
Do not change repository visibility or account plans as part of a test.

Once the boundary is enforced, the author can prepare `chore/release-notes`
on the host. Use a fine-grained token limited to this repository with
Contents write, Pull requests write, and Issues read. Publish only the notes
to that branch with the REST contents API, then POST a PR for review.
This is the chapter's intended positive write test; it has **not** been run
under a newly composed sandbox. Never test denial by trying a real deletion.

## Reproduce offline checks

```bash
python3 -m unittest discover -s tests -v
```

These check descriptor intent, including twenty HTTP request cases and the
unmodified workload's broader grant. The small projection in the tests is
not a proxy or a general implementation of the policy specification.

For official schema validation, obtain a local checkout of
`docker/sandbox-kit-spec` at commit
`06ac386a1b5d570daff36bba4232fb9e71e45d50`, then run:

```bash
python3 scripts/validate-book-kits.py \
  /path/to/sandbox-kit-spec/schema/kit.schema.json \
  kits/book-github/kit.yaml build/book-codex/kit.yaml
```

The original GitHub mixin used for comparison was reviewed at
`ContainerSecurity-dev/sbx-examples` commit
`ec61a221285ee7fb6e6596a280ce303c69e9cc6f`. The policy composition rules
are documented in `docs/spec/capabilities/com.docker.sandbox/network-policy@2.md`
in the Kit specification checkout.

## Results in the writing sandbox

- Official JSON Schema validation passed for the mixin and a workload derived
  from the installed Codex 0.169.0 descriptor.
- Six offline tests passed, including all twenty request cases.
- The current writing sandbox's authenticated repository GET succeeded.
  This is an existing-transport check, **not** a test of the new mixin.
- GitHub reported main as unprotected. Rulesets and branch-protection GETs
  returned 403 with an account-plan limitation.
- The host test script reported that `sbx` is unavailable in this guest.
  The guest also has no `/dev/kvm`; a fresh sandbox, effective host policy,
  and an end-to-end PR under that policy remain unverified.

After preserving the test sandbox's work, remove only `book-github-check`
when you no longer need it. Generated workload files, Python environments,
and builder caches have separate lifecycles.
