FROM ubuntu:24.10

# Install python and pipx
RUN apt-get update -y && \
    apt-get install -y iputils-ping python3 python3-pip python3-venv pipx && \
    ln -s /usr/bin/python3 /usr/bin/python

# Include install script that handles how to install dapla-cli (from PyPI or local source)
COPY install-dapla-cli.sh /usr/local/bin/install-dapla-cli.sh

USER 1000
ENV PIPX_BIN_DIR=/home/ubuntu/.local/bin
ENV PATH="${PIPX_BIN_DIR}:${PATH}"

ENTRYPOINT ["install-dapla-cli.sh"]
