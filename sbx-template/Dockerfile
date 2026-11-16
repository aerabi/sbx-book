ARG BASE_IMAGE=docker.io/sbx/shell-image:latest
FROM ${BASE_IMAGE}

USER root

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      make \
      pandoc \
      texlive-xetex \
      texlive-latex-recommended \
      texlive-latex-extra \
      texlive-fonts-recommended \
      texlive-fonts-extra \
      lmodern \
      latexmk \
      fontconfig \
      fonts-firacode && \
    rm -rf /var/lib/apt/lists/*

COPY texlive-fonts.conf /etc/fonts/conf.d/99-book-texlive.conf
RUN fc-cache -f

USER agent
