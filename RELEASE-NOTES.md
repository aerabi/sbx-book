# Docker Sandboxes in Action release notes

This upcoming early-access release revises Chapter 2 and adds an appendix
for tracking changes to the Docker Sandboxes CLI.

## What’s new

- Chapter 2 walks through running Codex in a private clone, then introduces
  workload kits, templates, and mixins. The examples start with a small
  network-policy mixin and finish with the book’s GitHub mixin for proposing
  release notes on a working branch.
- The SBX Release Watch appendix records the CLI version used for the
  exercises, sbx v0.51.0. It provides a place to track later CLI changes that
  could affect the walkthroughs. The repository also includes the scheduled
  task instructions for proposing updates to the appendix.

## Build the book

The [README](README.md) walks through building the book in a Docker Sandbox
with the supplied toolchain image. Run `make pdf` or `make epub` from the
repository root inside the sandbox. The PDF and EPUB are written to
`build/pdf/book.pdf` and `build/epub/book.epub`. HTML and DOCX builds are also
available.
