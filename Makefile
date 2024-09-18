.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: default
default: | help

.PHONY: pipx-install
pipx-install: ## Install with pipx from PyPI
	pipx install dapla-cli

.PHONY: pipx-install-editable
pipx-install-editable: ## Install with pipx from the source code in editable mode
	pipx install --editable .

.PHONY: build-docker
build-docker: ## Build local Docker image for testing in an isolated environment
	docker build -f ./dev/Dockerfile -t dapla-cli  ./dev

.PHONY: run-isolated
run-isolated: build-docker ## Run Dapla CLI in isolated environment (Docker container) using latest release from PyPI
	docker run -it dapla-cli -c bash

.PHONY: run-isolated-dev
run-isolated-dev: build-docker ## Run Dapla CLI in isolated environment (Docker container) using latest release from local source (in editable mode)
	docker run -v $(PWD)/:/mnt/dapla-cli -it dapla-cli -c bash

