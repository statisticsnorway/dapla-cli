# dapla-cli 

The dapla cli is a command-line application users can use to interract with the da(ta)pla(form). The command 
has several sub-commands.

[![CI](https://github.com/statisticsnorway/dapla-cli/actions/workflows/main.yml/badge.svg)](https://github.com/statisticsnorway/dapla-cli/actions/workflows/main.yml)
[![Go Report Card](https://goreportcard.com/badge/github.com/statisticsnorway/dapla-cli?style=flat-square)](https://goreportcard.com/report/github.com/statisticsnorway/dapla-cli)
[![Release](https://img.shields.io/github/release/statisticsnorway/dapla-cli.svg?style=flat-square)](https://github.com/statisticsnorway/dapla-cli/releases/latest)
[![Go Doc](https://img.shields.io/badge/godoc-reference-blue.svg?style=flat-square)](http://godoc.org/github.com/statisticsnorway/dapla-cli)

```
# dapla --help
The dapla command is a collection of utilities you can use with the dapla platform.

Usage:
  dapla [command]

Available Commands:
  completion  Generate completion script
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

Use "dapla [command] --help" for more information about a command.
```

## Installation

**NOTE**: The command is already installed in the dapla jupyterlab environement.

To install the command locally [download](https://github.com/statisticsnorway/dapla-cli/releases) the latest release archive and extract its content on your computer.
Alias the `dapla-cli` executable to `dapla`.

## .dapla-cli.yml config file

Although most config can be provided directly to the cli, an alternative configuration source is the `.dapla-cli.yml`
config file. By default the dapla-cli will look for config in the following location: `$HOME/.dapla-cli.yml`. This is also
configurable by specifying the `--config` flag. The following is an example of a `.dapla-cli.yml`:

```yml
jupyter: false
authtoken: eyJh...TqV2Q
apis:
  data-maintenance: http://localhost:10200
  dapla-pseudo-service: http://localhost:30950
```

## Authentication

In order to be able to communicate with the API servers you need to provide an authentication methods and the API server URI. 

The flags `--jupyter` can be used when the dapla command runs inside the container. In this case the application will try to retrieve the authentication token by itself: 

`# dapla --jupyter`

Alternatively one can provide an authentication token manually using the `--authtoken` flag, like so:

`# dapla --authtoken "my.jwt.token"`

... or by specifying the token in the `.dapla-cli.yml` file. Also, a third option is to specify the `$AUTHTOKEN` env variable.

## API URLs

You will need to configure the locations of the APIs that the dapla-cli communicates with. It is recommended
that you provide this configuration in the `.dapla-cli.yml` file (see example above).

It is also possible to provide the API urls directly to the dapla-cli, like so:

`# dapla --jupyter --apis data-maintenance="http://data-mainenance-server",dapla-pseudo-service="http://dapla-pseudo-service-server"`

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
$ dapla export --help

The export command exports (and optionally depseudonymizes) a specified dataset

Usage:
  dapla export [PATH]... [flags]

Flags:
      --depseudo                      depseudonymize data during export
  -h, --help                          help for export
  -n, --name string                   descriptive name of the contents, used as baseline for the target archive name
  -p, --password string               password used to protect target archive
      --pseudo-rules stringToString   password used to protect target archive (default [])
      --target-path string            path to where the exported dataset archive will be stored
  -t, --timestamp int                 optional timestamp of dataset, resolved against the closest matching version (default 1618599695335)
```

### completion

The completion command can be used to setup autocompletion. Refer to the [cobra documentation](https://github.com/spf13/cobra/blob/master/shell_completions.md) for more details.
