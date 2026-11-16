\newpage

# Sandboxes and AI Agents


Couldn't we have built that PDF inside a regular Docker container?

Yes! A container with Pandoc and XeLaTeX is perfectly useful for a book build. We already know how to package the tools and mount a directory for the output. The difference becomes more interesting when an AI agent chooses the commands, installs unfamiliar dependencies, and needs Docker itself.

## Sandboxes vs. Containers

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

With Docker Desktop, Linux containers already run in a VM. They still share that Docker Engine VM's kernel; this differs from a sandbox's microVM boundary. Neither protects files deliberately mounted read-write from being overwritten. See the book *Docker and Kubernetes Security* for more on container security.

There is another limit: A microVM cannot stop an authorized GitHub API request from deleting a repository. That happens on GitHub, not on your laptop.

Let's give an agent a useful job, then deal with that problem.

## Put Codex to Work

We have been typing every command ourselves. Now we will ask Codex to draft release notes for the Christmas Edition.

From a disposable Git checkout containing a README, run on the **host**:

```bash
$ sbx secret set openai --oauth
$ sbx create --name christmas-codex --clone codex .
$ sbx policy ls christmas-codex --wide
$ sbx run --name christmas-codex
```

This creates a new Codex environment, rather than reusing the Pandoc shell template. The task is writing Markdown, so it does not need our PDF tools yet. Clone mode keeps the agent's changes in a private working copy.

The OAuth command authenticates on the host. In v0.51.0, this OAuth credential is global. Authenticate **before creating the sandbox**, so its initial Codex configuration can use the stored credential. An API-key alternative is `sbx secret set openai`, also before creation. Use the method appropriate to your account, without copying credential files into the workspace.

If you created the sandbox before authenticating and Codex still asks you to sign in, try removing the sandbox and creating it again:

```bash
$ sbx rm christmas-codex
```

In the Codex session, enter:

```text
Read the project README and draft RELEASE-NOTES.md for version 1.1.0,
Christmas Edition. Describe only features supported by the files here.
Do not commit or push. Leave the draft for my review.
```

Review the result in the sandbox before accepting changes through the clone-mode Git workflow. The host working tree remains unchanged.

But the README does not tell the whole release story. We also want Codex to read our closed GitHub issues and use them to improve the draft.

Now it needs a GitHub client, API access, and perhaps a credential for a private repository. We want it to read issues. We do not want it to delete the repository while tidying things up!

“Please don't delete my repository” belongs in the conversation. It is not an access control.
