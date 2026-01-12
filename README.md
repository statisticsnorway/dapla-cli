# Dapla CLI

[![PyPI](https://img.shields.io/pypi/v/dapla-cli.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/dapla-cli.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/dapla-cli)][pypi status]
[![License](https://img.shields.io/pypi/l/dapla-cli)][license]

[![Documentation](https://github.com/statisticsnorway/dapla-cli/actions/workflows/docs.yml/badge.svg)][documentation]
[![Tests](https://github.com/statisticsnorway/dapla-cli/actions/workflows/tests.yml/badge.svg)][tests]
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_dapla-cli&metric=coverage)][sonarcov]
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=statisticsnorway_dapla-cli&metric=alert_status)][sonarquality]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry]

[pypi status]: https://pypi.org/project/dapla-cli/
[documentation]: https://statisticsnorway.github.io/dapla-cli
[tests]: https://github.com/statisticsnorway/dapla-cli/actions?workflow=Tests

[sonarcov]: https://sonarcloud.io/summary/overall?id=statisticsnorway_dapla-cli
[sonarquality]: https://sonarcloud.io/summary/overall?id=statisticsnorway_dapla-cli
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black
[poetry]: https://python-poetry.org/



## Installation

Install with [pipx] from [pypi]:

```console
pipx install dapla-cli
```

Alternatively you can build `dapla-cli` using the provided nix flake:

```console
$ nix build .#dapla-cli
$ ./result/bin/dp --version
```

or open the provided nix shell:

```console
$ nix develop .#
$ dp --version
```

## Usage

Starting point: `dp --help`

### Auth

This tool uses a device flow to authenticate against a Keycloak client.

#### Keycloak clients

By default it will use a client called `dapla-cli`, but this may be customized by providing a value `--client my-client`.

Any client used by this tool needs to have the `device` flow activated. [Refer here for an example client configuration](https://github.com/statisticsnorway/keycloak-iac/blob/21f694d74acbdadad0b9cacd4e967a7af624d4fd/clients/prod/dapla-stat/dapla-cli.pkl#L7).

#### Login

Run the command and then follow the instructions to

```shell
dp auth login
```

```shell
dp auth login --client my-client --env test
```

#### Show token

Once logged in, the access token can be accessed.

```shell
dp auth show-access-token
```

```shell
dp auth show-access-token --client my-client --env test --to-clipboard
```

#### Logout

```shell
dp auth logout
```

### API reference

Please see the [Reference Guide] for details.

## Development

Install a local development edition with [pipx] from the source code:

```console
pipx install --editable .
```

Alternatively, use `make help` for other options, such as running Dapla CLI in an isolated environment:

```console
run-isolated       Run Dapla CLI in isolated environment (Docker container) using latest release from PyPI
run-isolated-dev   Run Dapla CLI in isolated environment (Docker container) using latest release from local source (in editable mode)
pipx-install       Install with pipx from PyPI
pipx-install-dev   Install with pipx from the source code in editable mode
build-docker       Build local Docker image for testing in an isolated environment
```

## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide].

## License

Distributed under the terms of the [MIT license][license],
_Dapla CLI_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue] along with a detailed description.

## Credits

This project was generated from [Statistics Norway]'s [SSB PyPI Template].

[statistics norway]: https://www.ssb.no/en
[pypi]: https://pypi.org/project/dapla-cli/
[ssb pypi template]: https://github.com/statisticsnorway/ssb-pypitemplate
[file an issue]: https://github.com/statisticsnorway/dapla-cli/issues
[pipx]: https://pipx.pypa.io/

<!-- github-only -->

[license]: https://github.com/statisticsnorway/dapla-cli/blob/main/LICENSE
[contributor guide]: https://github.com/statisticsnorway/dapla-cli/blob/main/CONTRIBUTING.md
[reference guide]: https://statisticsnorway.github.io/dapla-cli/reference.html
