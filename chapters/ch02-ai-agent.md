\newpage

# Sandboxes, AI Agents, and Kits

Couldn't we have built that PDF inside a regular Docker container?

Yes! A container with Pandoc and XeLaTeX is perfectly useful for a book build. We already know how to package the tools and mount a directory for the output. The difference becomes more interesting when an AI agent chooses the commands, installs unfamiliar dependencies, and needs Docker itself.

## Sandboxes vs. Containers

If you run Docker natively, there is a thin layer of isolation between the container and the host. The barrier is good enough for a static application. But it's probably too thin for a juggernaut AI agent that can install new tools, run arbitrary commands, and find zero-day exploits. With Docker Desktop, Linux containers already run in a VM. They still share that Docker Engine VM's kernel. See my earlier book, *Docker and Kubernetes Security*, for more on container security.

| Property | Ordinary Docker container | Local Docker Sandbox |
|----------|---------------------------|----------------------|
| Kernel | Shares the kernel of the machine or VM running Docker Engine. | Has a separate guest kernel inside a microVM. |
| Isolation | Namespaces, cgroups, capabilities, seccomp, and other host controls. | A microVM boundary plus controls over shared resources. |
| Files | Writable bind mounts allow changes to host files. | Direct workspace mounts allow changes; clone mode provides a private Git copy. |
| Docker access | Mounting the host socket grants access to that daemon; Docker-in-Docker needs careful configuration. | An engine inside the microVM is separate from the host daemon. |
| Network | Destination and HTTP restrictions require additional configuration. | `sbx` provides network and HTTP policies. |
| Credentials | Processes can read environment variables or secret files they have access to. | Supported proxy-managed credentials authenticate requests without exposing raw tokens to the guest. |
| Reuse | Images package software; runtime configuration is supplied separately. | Templates package the filesystem; Kits also declare runtime requirements. |
| Our example | Run a known PDF build command. | Let an agent choose commands within defined boundaries. |
Table: Containers and local Docker Sandboxes for development tasks.

There is another limit: A Docker container is not built to prevent an authorized GitHub API request from deleting a repository. But a Docker Sandbox built for containing AI agents might!

Let's give an agent a useful job, then deal with that problem.

## Put Codex to Work

So, I want to ask my AI agent to build a references section into the book. In your case, you can ask it to draft release notes for your own Git repo. And we're going to use the clone mode, to suffer! So, we need a Git-based project.

From a disposable Git checkout containing a README, run on the **host**:

```bash
% sbx secret set openai --oauth
% sbx create --name christmas-codex --clone codex .
% sbx policy ls christmas-codex --wide
% sbx run --name christmas-codex
```

This creates a new Codex environment, rather than reusing the Pandoc shell template. The task is writing Markdown, so it does not need our PDF tools yet. Clone mode keeps the agent's changes in a private working copy. Which means the edits stay inside the sandbox until we move them back to the host.

The OAuth command authenticates on the host. In v0.51.0, this OAuth credential is global. Authenticate **before creating the sandbox**, so its initial Codex configuration can use the stored credential. An API-key alternative is `sbx secret set openai`, also before creation. Use the method appropriate to your account, without copying credential files into the workspace.

If you created the sandbox before authenticating and Codex still asks you to sign in, try removing the sandbox and creating it again:

```bash
% sbx rm christmas-codex
```

One point about the credentials and authentication: The secret is stored on the host, not in the sandbox. The secret is injected to requests leaving the sandbox, but the sandbox cannot read the secret directly. That's yet another security boundary to keep the secrets out, in case the sandbox is compromised with a Shai-Hulud worm or a prompt injection.

In the Codex session, enter:

```text
Read the project README and draft RELEASE-NOTES.md for the upcoming release. Create a pull request on GitHub for my review.
```

The sandbox can draft the file, but it cannot create the PR yet. We'll add GitHub access with a mixin below.

## From Templates to Kits

Chapter 1 gave us a template: A reusable filesystem with the tools we installed. Now Codex needs GitHub access. A Kit lets us describe the environment and the capabilities it needs; a mixin lets us add one piece at a time.

### Kits, Mixins, and Templates

A **template** is the filesystem image a sandbox starts from. It contains the operating system and installed tools.

A **Kit** is a descriptor and any files it uses, such as a Dockerfile or agent instructions. Its `kind` says whether it defines a workload or is a mixin.

A **workload Kit** describes the main environment and agent, such as Codex. It can include a template, startup details, and declared capabilities.

A **mixin** is an add-on to a workload Kit. It can add software, network rules, credentials, or instructions for the agent. It does not replace the agent or start a separate sandbox.

In short: The template supplies files; the workload Kit says what runs; mixins add task-specific pieces. A Kit can be used on its own as a workload or attached to another workload as a mixin.

### Create a Tiny Mixin

Let's allow one harmless destination before adding GitHub. The example is in `kits/hello-mixin/kit.yaml`:

```yaml {.numberLines caption="A minimal network-policy mixin"}
# syntax=docker/sandbox-kit:3
schemaVersion: "3"
kind: mixin
displayName: Hello network
description: Allow a sandbox to reach example.com

capabilities:
  - type: com.docker.sandbox/network-policy@2
    config:
      runtime:
        allow:
          - hosts: [example.com]
            methods: [GET, HEAD]
        deny:
          - example.org
```

This descriptor does not install anything. It adds one capability: Allow GET and HEAD requests to `example.com`. Compose it with the Codex workload:

```bash
% sbx create --name christmas-mixin --kit ./kits/hello-mixin codex .
% sbx policy ls christmas-mixin --wide
% sbx policy check http --sandbox christmas-mixin --method GET https://example.com/
% sbx policy check http --sandbox christmas-mixin --method GET https://example.org/
```

The first check should be allowed and the second denied. The command evaluates policy; it does not send either request. We have now seen a mixin added to a workload, and how its declared capability changes the sandbox policy.

### Inspect the Book's GitHub Mixin

The small example added one network rule. Now inspect the mixin for this book, in `kits/book-github/`:

```bash
% cat kits/book-github/kit.yaml
% cat kits/book-github/github-context.md
% cat kits/book-github/policy-cases.tsv
```

The file `kit.yaml` is the mixin descriptor. Its network capability allows repository reads, one `PUT` endpoint for `RELEASE-NOTES.md`, and `POST` to create a pull request. It denies other GitHub hosts, `DELETE` and `PATCH` requests, and GraphQL. For example, the file update is allowed while a README update is not:

```yaml
allow:
  - hosts: [api.github.com]
    methods: [PUT]
    paths: [/repos/aerabi/sbx-book/contents/RELEASE-NOTES.md]
deny:
  - hosts: [api.github.com]
    methods: [DELETE, PATCH]
```

The credential capability asks the host to inject `GH_TOKEN` into requests to `api.github.com`. The `agent-context` capability points to `github-context.md`, which gives Codex instructions for using the API. Those instructions guide the agent; the network rules control which requests can pass. The Codex workload already includes `gh`, so this mixin does not install it.

The file `policy-cases.tsv` is a test matrix, not part of the policy. Each row gives the expected decision, HTTP method, and URL. For example:

```tsv
allow	PUT	https://api.github.com/repos/aerabi/sbx-book/contents/RELEASE-NOTES.md
deny	PUT	https://api.github.com/repos/aerabi/sbx-book/contents/README.md
deny	DELETE	https://api.github.com/repos/aerabi/sbx-book
```

One detail matters when kits are combined: Allow rules can accumulate. The built-in Codex workload grants broad GitHub access, so this mixin alone would not narrow it. The helper in `scripts/prepare-book-codex.py` removes those GitHub grants while preserving the rest of the inspected workload; the next section composes and tests that result.

### Test the GitHub Mixin

From the host, prepare the compatible workload from the Codex sandbox created earlier in this chapter, then create a fresh sandbox with the book mixin. The helper uses PyYAML; if needed, install it with `python3 -m pip install PyYAML`:


```bash
% sbx exec christmas-codex -- cat /usr/share/sandbox/kit/codex/kit.yaml \
  > /tmp/book-codex-source.yaml
% python3 scripts/prepare-book-codex.py \
  /tmp/book-codex-source.yaml build/book-codex
% sbx create --name christmas-codex-gh --clone \
  --kit ./kits/book-github ./build/book-codex .
```

Inspect the effective policy and run the test matrix:

```bash
% sbx policy ls christmas-codex-gh --wide
% sh scripts/check-book-github-policy.sh christmas-codex-gh
```

Compare each result with its expected allow or deny in `kits/book-github/policy-cases.tsv`. These checks do not send requests to GitHub. If the decisions match, store the host token for this sandbox and make one harmless authenticated read:

```bash
% sbx secret set github --sandbox christmas-codex-gh -t "$(gh auth token)"
% sbx run --name christmas-codex-gh
```

In another host terminal, check the CLI and make one harmless authenticated read:

```bash
% sbx exec christmas-codex-gh -- gh --version
% sbx exec christmas-codex-gh -- gh api --method GET repos/aerabi/sbx-book
```

A successful GET tests the mixin's credential and network path. The policy matrix tests the allowed and denied requests without carrying them out. This command reuses your host token and its permissions. For a more limited test, create a fine-grained token restricted to the repository and permissions needed, then supply that token instead. The mixin is meant to let Codex propose a change for review, not to merge it.

Storing a secret and letting a sandbox use it are two separate things. When you create a sandbox interactively, sbx asks whether the GitHub and OpenAI credentials may be injected for the declared domains, and records your answer in `~/.config/sbx/credentials.yaml`. In a script without a terminal, nobody answers, so creation prints `no binding authorizes github, openai` and the requests go out unauthenticated. Create the sandbox once from a real terminal.

### Lock the Front Door

The mixin can allow a `PUT` to `RELEASE-NOTES.md`, but it cannot read the request body. The branch name sits in that body. So, the policy alone cannot stop Codex from writing the file straight to `main`.

That job belongs to GitHub. Protect the default branch with a ruleset: Changes only through a pull request, no force pushes, no deletion, and **no bypass actors**. The last point matters. A token acts as the person who created it, and if you are an admin with bypass rights, so is your agent. I created mine with:

```bash
% gh api -X POST repos/aerabi/sbx-book/rulesets --input ruleset.json
```

The file contains the three rules above with an empty `bypass_actors` list. To test it, try a direct write to `main` from the sandbox:

```bash
% sbx exec christmas-codex-gh -- gh api -X PUT \
  repos/aerabi/sbx-book/contents/RELEASE-NOTES.md \
  -f message=probe -f content=cHJvYmUK -f branch=main
```

GitHub answers `409` with "Changes must be made through a pull request." Now two independent controls guard the repository: The sandbox decides which requests may leave, and GitHub decides what an authenticated request may change.

### Publish the Release Notes

Create a working branch on the host and push it, then return to the Codex session:

```bash
% git push origin HEAD:refs/heads/release-notes-draft
```

```text
Read the project README and draft RELEASE-NOTES.md for the upcoming release. Publish it on the existing working branch release-notes-draft and create a pull request into main on GitHub for my review.
```

In my run with sbx v0.54.1 and Codex 0.172.0, Codex read the README, wrote the file to the branch through the contents API, and opened a pull request in about two minutes. Then it reported the URL and stopped. The sandbox's policy log shows what it tried along the way:

```bash
% sbx policy log christmas-codex-gh
```

The log listed `github.com:443` as denied by the mixin and one `api.github.com` request with no matching allow rule. Codex worked around both without asking for more access. Review the pull request like any other contribution. Merging is your job.

## Summary

We moved from a sandbox that runs commands to one that runs an agent. The agent got exactly three things: A workload with its tools, a credential it cannot read, and a network policy that decides which GitHub requests can leave. The mixin carried the GitHub piece, and a test matrix proved the policy before any real request was sent. Where the policy could not see, a branch ruleset took over.

There is one thing this sandbox still can't do: Keep working when I close my laptop. Codex stops with the microVM. And while I wrote this chapter, sbx moved from v0.51.0 to v0.54.1, so the book is already out of date. In Chapter 3, we move a running Codex sandbox to Docker's cloud, and then schedule a daily cloud job that checks for new sbx releases and opens a pull request on this book. Clone mode will matter again, though not the way you might expect.

## Exercises

1. Add a row to `kits/book-github/policy-cases.tsv` that should be denied, such as `PUT` to `chapters/ch02-ai-agent.md`. Run the check script and confirm the decision. Then add a row the mixin should allow but doesn't, and decide whether the mixin or the row is wrong.
2. Compose `kits/hello-mixin` and `kits/book-github` with the same workload. Which rules does `sbx policy ls --wide` show, and does either mixin weaken the other?
3. Ask Codex to update `README.md` instead of `RELEASE-NOTES.md`. Read the policy log afterwards. What did it try, and what did it tell you?
4. Create a sandbox from a script with no terminal and look for the binding message. Then find the entry interactive creation adds to `~/.config/sbx/credentials.yaml`.
