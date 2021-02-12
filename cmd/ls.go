package cmd

import (
	"bufio"
	"errors"
	"fmt"
	"github.com/juju/ansiterm"
	"github.com/spf13/cobra"
	"github.com/statisticsnorway/dapla-cli/rest"
	"io"
	"os"
	"strings"
	"time"
)

var (
	lsLong bool
)

func newLsCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "ls [PATH]...",
		Short: "List information about the dataset(s) under PATH",
		Long:  `TODO`,
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {

			var client, err = initClient()
			if err != nil {
				panic(err) // TODO don't panic!
			}

			// Use newline when not in terminal (piped)
			var printFunction func(datasets *rest.ListDatasetResponse, output io.Writer)
			if fileInfo, _ := os.Stdout.Stat(); (fileInfo.Mode() & os.ModeCharDevice) != 0 {
				if lsLong {
					printFunction = printTabularDetails
				} else {
					printFunction = printTabular
				}
			} else {
				printFunction = printNewLine
			}

			for _, path := range args {
				res, err := client.ListDatasets(path)
				if err != nil {
					if strings.HasSuffix(err.Error(), "404") {
						fmt.Printf("Cannot access %s: No such dataset or folder", path)
					} else {
						panic(err) //TODO don't panic
					}
				} else {
					printFunction(res, os.Stdout)
				}
			}
		},
		ValidArgsFunction: func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {

			// TODO make test(s)!

			return doAutoComplete(toComplete)
		},
	}
}

func initClient() (*rest.Client, error) {
	if jupyter && bearerToken != "" {
		panic(errors.New("cannot use both --jupyter and --token"))
	}

	switch {

	case jupyter:
		return rest.NewClientWithJupyter(serverUrl)

	case bearerToken != "":
		return rest.NewClient(serverUrl, bearerToken), nil
	default:
		return nil, errors.New("use --jupyter or define the --token")
	}
}

func init() {
	lsCommand := newLsCommand()
	lsCommand.Flags().BoolVarP(&lsLong, "", "l", false, "use a long listing format")
	rootCmd.AddCommand(lsCommand)
}

// Prints the dataset names
func printNewLine(datasets *rest.ListDatasetResponse, output io.Writer) {
	writer := bufio.NewWriter(output)
	defer writer.Flush()
	for _, dataset := range *datasets {
		fmt.Fprintln(writer, dataset.Path)
	}
}

func printTabular(datasets *rest.ListDatasetResponse, output io.Writer) {
	folderContext := ansiterm.Foreground(ansiterm.Blue)
	folderContext.SetStyle(ansiterm.Bold)
	datasetContext := ansiterm.Foreground(ansiterm.Default)

	writer := ansiterm.NewTabWriter(output, 15, 0, 2, ' ', 0)
	defer writer.Flush()

	// Print the folders first.
	for _, dataset := range *datasets {
		if dataset.IsFolder() {
			folderContext.Fprintf(writer, "%s", dataset.Path)
			datasetContext.Fprint(writer, "/\t")
		}
	}
	for _, dataset := range *datasets {
		if dataset.IsDataset() {
			datasetContext.Fprintf(writer, "%s\t", dataset.Path)
		}
	}
	_, _ = fmt.Fprintln(writer)
}

// Prints the datasets in tabular format. Datasets are white and folders blue and with a trailing '/'
func printTabularDetails(datasets *rest.ListDatasetResponse, output io.Writer) {
	writer := ansiterm.NewTabWriter(output, 32, 0, 2, ' ', 0)
	headerContext := ansiterm.Foreground(ansiterm.BrightCyan)
	headerContext.SetStyle(ansiterm.Bold)
	datasetContext := ansiterm.Foreground(ansiterm.White)
	folderContext := ansiterm.Foreground(ansiterm.Blue)
	folderContext.SetStyle(ansiterm.Italic)
	defer writer.Flush()
	headerContext.Fprint(writer, "Name\tAuthor\tCreated\tType\tValuation\tState\n")
	for _, dataset := range *datasets {
		if dataset.IsFolder() {
			folderContext.Fprintf(writer, "%s\t%s\t%s\t%s\t%s\t%s\n",
				dataset.Path+"/",
				dataset.CreatedBy,
				dataset.CreatedAt.Format(time.RFC3339),
				dataset.Type,
				dataset.Valuation,
				dataset.State)
		} else {
			datasetContext.Fprintf(writer, "%s\t%s\t%s\t%s\t%s\t%s\n",
				dataset.Path,
				dataset.CreatedBy,
				dataset.CreatedAt.Format(time.RFC3339),
				dataset.Type,
				dataset.Valuation,
				dataset.State)
		}
	}
}
