# 🐳 Docker Security Book Template

> *An open-source book template for the community, based on the book "Docker and Kubernetes Security" by Mohammad-Ali A'râbi.*

---

This book is written using Markdown and Pandoc. The source files are in the `chapters` directory.
The book is built using the `Makefile` and `pandoc` command:

```bash
make pdf
```

or

```bash
make epub
```

The book is built in the `build` directory.

## Sandbox templates

Chapters 1 and 2 use the same [Dockerfile](sbx-template/Dockerfile) and
[Fontconfig configuration](sbx-template/texlive-fonts.conf). The default base
provides a shell; override `BASE_IMAGE` with a compatible Debian-based Codex
sandbox image to add the book toolchain to Codex:

```bash
docker build -t christmas-tools:2 ./sbx-template
docker build --build-arg BASE_IMAGE=dhi.io/codex:0.169.0 \
  -t christmas-codex-tools:1 ./sbx-template
docker image save christmas-codex-tools:1 -o /tmp/christmas-codex-tools-1.tar
sbx template load /tmp/christmas-codex-tools-1.tar
```

Use the Codex image reference for your sbx release; record its digest and use
that digest for subsequent builds. The Dockerfile assumes apt and an `agent`
user, and preserves the base entrypoint. Its TeX Live font bundle is large.
See Chapter 2 for sandbox creation, font verification, PDF compilation, and
copying the artifact back from clone mode. Credentials and runtime network
policy must be configured separately.

## Install Pandoc

On Ubuntu, install Pandoc and Tex Live:

```bash
sudo apt install pandoc texlive texlive-xetex latexmk
```

On macOS, install Pandoc using Homebrew:

```bash
brew install pandoc
```

But to install Tex Live, you need to download the installer from the [Tex Live website](https://www.tug.org/mactex/mactex-download.html).
Then install `latexmk` using Tex Live's package manager:

```bash
sudo tlmgr update --self
sudo tlmgr install latexmk
```

Make sure to have the fonts installed:

```bash
brew install --cask font-fira-code
brew install --cask font-libertinus
brew install --cask font-latin-modern
```

## License

This project is licensed under **CC BY-SA 4.0**. See [LICENSE](LICENSE) for details.
