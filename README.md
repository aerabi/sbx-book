# Docker Sandboxes in Action

> *Secure AI Agents with SBX, Kits, and Cloud, by Mohammad-Ali A'RÂBI.*

This is the open-source manuscript and build tooling for the book.
ISBN: **978-3-9828298-4-5**. Copyright © 2026 Mohammad-Ali A'RÂBI.

Chapters are in `chapters/`; layout files are in `templates/`. Run build
commands from the repository root. In the examples below, `%` marks a host
command and `$` a command inside a sandbox. Do not type those prompt characters.

## Build in a sandbox

You need Git, Docker Engine or Docker Desktop with a running daemon, and the
`sbx` CLI configured for your host. Chapter 1 covers sandbox setup and network
policy. The host Docker builder needs network access to the base image and
package repositories. The TeX Live font bundle is large; allow time and disk
space for the initial build.

On the **host**:

```bash
% git clone https://github.com/aerabi/sbx-book.git
% cd sbx-book
% docker version
% sbx login
% sbx diagnose
% docker build -t sbx-book-tools:2026 ./sbx-template
% docker image save sbx-book-tools:2026 -o /tmp/sbx-book-tools-2026.tar
% sbx template load /tmp/sbx-book-tools-2026.tar
% sbx create --name sbx-book-build --template sbx-book-tools:2026 --pull never shell .
% sbx run --name sbx-book-build
```

`docker version` must show both a client and a server. Use a new sandbox name
if `sbx-book-build` already exists. The final `.` shares this checkout
read-write, including your uncommitted edits.

Inside the **sandbox**, from the shared repository root:

```bash
$ fc-match 'Libertinus Serif'
$ fc-match 'Fira Code Retina'
$ make pdf
$ make epub
```

The font matches should identify Libertinus Serif and Fira Code, rather than
substitutes. The [Dockerfile](sbx-template/Dockerfile) installs the complete
PDF toolchain and [Fontconfig configuration](sbx-template/texlive-fonts.conf);
no personal font files are needed.

Open `build/pdf/book.pdf` or `build/epub/book.epub` on the **host**. The direct
mount makes the output available immediately. After source edits, rerun
`make pdf`; use `make -B pdf` to force a rebuild after changing tools or fonts.
To stop the sandbox, exit its shell and run on the **host**:

```bash
% sbx stop sbx-book-build
```

To resume it later, use `sbx run --name sbx-book-build` on the host. Rebuilding
the image does not update an existing sandbox: export/load the new image and
create a new sandbox to use it. Record the base-image digest if you need to
reproduce a particular environment; the default tag and apt packages can change.

## Other output formats

Run these inside the **sandbox**:

```bash
$ make html
$ make docx
```

Outputs are `build/html/book.html` and `build/docx/book.docx`. EPUB uses the
book metadata for its title page. To supply a cover for this book:

```bash
$ make epub COVER_IMAGE=/path/inside/sandbox/to/sbx-cover.png
```

The cover path must be accessible inside the sandbox. `make clean` deletes
the generated `build/` directory, including any other work stored there.

## Build directly on Debian or Ubuntu

If you prefer installing the toolchain on the **host**, use the same packages
and font configuration as the sandbox image:

```bash
% sudo apt-get update
% sudo apt-get install -y --no-install-recommends make pandoc \
  texlive-xetex texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended texlive-fonts-extra lmodern latexmk \
  fontconfig fonts-firacode
% sudo cp sbx-template/texlive-fonts.conf /etc/fonts/conf.d/99-book-texlive.conf
% fc-cache -f
% fc-match 'Libertinus Serif'
% fc-match 'Fira Code Retina'
% make pdf
```

For macOS, the sandbox workflow above avoids maintaining a separate host TeX
and font installation. EPUB alone requires Make and Pandoc, without TeX Live.

## Codex template

Chapters 1 and 2 share the Dockerfile. Override `BASE_IMAGE` with a compatible
Debian-based Codex sandbox image to add the book toolchain to Codex. On the
**host**, using the image version from the Chapter 2 walkthrough:

```bash
% docker login dhi.io
% docker build --build-arg BASE_IMAGE=dhi.io/codex:0.169.0 \
  -t christmas-codex-tools:1 ./sbx-template
% docker image save christmas-codex-tools:1 -o /tmp/christmas-codex-tools-1.tar
% sbx template load /tmp/christmas-codex-tools-1.tar
```

Check the Codex image reference for your sbx release and record its digest.
The Dockerfile assumes apt and an `agent` user, and preserves the base
entrypoint. Chapter 2 covers clone mode, authentication, network policy, and
copying the resulting PDF back to the host. These require separate setup;
the image only supplies the tools.

## Repository GitHub mixin

The [book GitHub mixin](kits/book-github/README.md) includes the repository
policy, credential binding, agent context, and host test matrix. Follow its
workload preparation step: the built-in Codex workload's broader GitHub
grant would otherwise widen the mixin's permissions.

## License

This project is licensed under **CC BY-SA 4.0**. See [LICENSE](LICENSE) for
details and the inherited book-template attribution.
