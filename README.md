# dapla-cli

The Dapla CLI is a command-line application users can use to interract with the da(ta)pla(form). The command 
has several sub-commands.

[![CI](https://github.com/statisticsnorway/dapla-cli/actions/workflows/main.yml/badge.svg)](https://github.com/statisticsnorway/dapla-cli/actions/workflows/main.yml)
[![Release](https://img.shields.io/github/release/statisticsnorway/dapla-cli.svg?style=flat-square)](https://github.com/statisticsnorway/dapla-cli/releases/latest)
[![Go Report Card](https://goreportcard.com/badge/github.com/statisticsnorway/dapla-cli?style=flat-square)](https://goreportcard.com/report/github.com/statisticsnorway/dapla-cli)

```
The dapla command is a collection of utilities you can use with the Dapla platform.

Usage:
  dapla [command]

Available Commands:
  completion  Generate completion script
  doctor      Print diagnostics and check the system for potential problems
  export      Export a dataset
  help        Help about any command
  ls          List the datasets and folders under a PATH
  rm          Delete dataset(s)

Flags:
      --apis stringToString   override API URIs (default [])
      --authtoken string      explicit user auth token (if running outside of jupyter)
      --config string         config file (default is $HOME/.dapla-cli.yml)
  -d, --debug                 print debug information
  -h, --help                  help for dapla
      --jupyter               set this flag to fetch user auth token from jupyter
  -v, --version               version for dapla

Use "dapla [command] --help" for more information about a command.
```


## Installation

**NOTE**: The command is already installed in the Dapla JupyterLab environement.

### Running locally

There are primarily four ways to run the Dapla CLI locally:

1. From [published binary](https://github.com/statisticsnorway/dapla-cli/releases). Extract and alias the `dapla-cli` executable to `dapla`.
2. Via Docker
3. Run in dev mode - without a build
4. From locally built binary

The `Makefile` provides some useful aliases for the latter options, which you can apply to you local environment like so:
```sh
eval $(make alias-XXX)
```

Option 3 and 4 requires that you have a Go development environment.


## Commands

### ls (list)

The list command lists the datasets and folders under the PATH.

```
$ dapla ls --help 
Usage:
  dapla ls [PATH]... [flags]

Flags:
  -l, --       use a long listing format
  -h, --help   help for ls

$ dapla ls /
/felles/
/kilde/
/produkt/
/raw/
/skatt/
/tmp/
/user/
```

### rm (remove)

The rm command deletes **all** the versions of a dataset for a particular path.

```
$ dapla rm --help

Usage:
  dapla rm [PATH]... [flags]

Flags:
      --dry-run   dry run
  -h, --help      help for rm
```

### export

The export command exports (and optionally depseudonymizes) a dataset from Dapla to GCS.

```
The export command exports (and optionally depseudonymizes) a specified dataset

Usage:
  dapla export [PATH] [flags]

Flags:
  -c, --cols stringArray              optional list of glob patterns that can be used to specify a subset of fields to export
      --depseudo                      depseudonymize data during export
  -h, --help                          help for export
  -n, --name string                   optional descriptive name of the contents, used as baseline for the target archive name
  -p, --password string               password used to protect target archive
      --pseudo-rules stringToString   explicit pseudo rules to use (default [])
      --pseudo-rules-path string      path to retrieve pseudo rules from
  -t, --target-filetype string        the export filetype (json or csv) (default "json")
```

### completion

The completion command can be used to setup autocompletion. Refer to the [cobra documentation](https://github.com/spf13/cobra/blob/master/shell_completions.md) for more details.

### doctor

The doctor command checks the system for potential problems and prints environmental stuff useful for debugging purposes.
Exits with a non-zero status if any potential problems are found. This command is only used for Dapla developers to help
pinpoint problems with the Dapla CLI and the evironment in which it is installed.


## Configuration

Although most config can be provided directly to the CLI, an alternative configuration source is the `.dapla-cli.yml`
config file. dapla-cli will look for config in the following location by default: `$HOME/.dapla-cli.yml`. The location
is configurable by specifying the `--config` flag. The following is an example of a configuration file:

```yml
jupyter: false
authtoken: eyJh...TqV2Q
apis:
  data-maintenance: $DATA_MAINTENANCE_URL # Will be substituted by env variable during runtime
  dapla-pseudo-service: http://localhost:30950
```

You can also populate config options via environment variables. E.g. if the `$AUTHTOKEN` env variable is configured then
this will take precedence over the configuration file.

Have a look at the [examples](/examples) folder for more config file examples.

### API URLs

You will need to configure the locations of the APIs that Dapla CLI communicates with. It is recommended
that you provide this configuration in the `.dapla-cli.yml` file (see example above). For API URLs you can either
specify a URL directly in config, or as an environment variable that will be resolved during runtime.

It is also possible to provide the API urls directly to the Dapla CLI, like so:

`# dapla --jupyter --apis data-maintenance="http://data-mainenance-server",dapla-pseudo-service="http://dapla-pseudo-service-server"`


## Authentication

In order to be able to communicate with the API servers you need to provide an authentication methods and the API server URI. 

The flags `--jupyter` can be used when the dapla command runs inside the container. In this case the application will try to retrieve the authentication token by itself: 

`# dapla --jupyter`

Alternatively one can provide an authentication token manually using the `--authtoken` flag, like so:

`# dapla --authtoken "my.jwt.token"`

... or by specifying the token in the `.dapla-cli.yml` file. Also, a third option is to specify the `$AUTHTOKEN` env variable.


## Development

Refer to the `Makefile` for misc development related tasks
```
build-local                    Build dapla-cli
build-docker                   Build dapla-cli with docker
changelog                      Generate CHANGELOG.md
alias-dev                      Print dapla alias for local development (no build) - apply with eval $(make alias-dev)
alias-localbuild               Print dapla alias for local build - apply with eval $(make alias-localbuild)
alias-docker                   Print dapla alias for running dapla-cli within docker - apply with eval $(make alias-docker)
```

### Releasing a new version

Releasing a new version is currently handled by [creating a release via github](https://github.com/statisticsnorway/dapla-cli/releases/new).
This will in turn trigger the Github Workflow that builds the binaries.