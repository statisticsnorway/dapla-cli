package cmd

import (
	"bufio"
	"fmt"
	"github.com/spf13/cobra"
	"github.com/statisticsnorway/dapla-cli/rest"
	"io"
	"os"
)

var (
	rmDebug  bool
	rmDryRun bool
)

func init() {
	rmCommand := newRmCommand()
	rmCommand.Flags().BoolVarP(&rmDebug, "debug", "d", false, "print debug information")
	rmCommand.Flags().BoolVarP(&rmDryRun, "dry-run", "", false, "dry run")
	rootCmd.AddCommand(rmCommand)
}

func newRmCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "rm [PATH]...",
		Short: "Remove the dataset(s) under PATH",
		Long:  `TODO`,
		Args:  cobra.MinimumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {

			var client, err = initClient()
			if err != nil {
				panic(err) // TODO don't panic!
			}

			// Send delete request
			// Display spinner (only on terminals!)
			// Handle timeout
			// Handle no access to one version
			// Handle no access at all
			// Handle invalid path

			// Format output with debug/dry-run

			path := args[0]
			res, err := client.DeleteDatasets(path, rmDryRun)
			printDeleteResponse(res, os.Stdout, rmDebug, rmDryRun)

		},
		ValidArgsFunction: func(cmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {

			return doAutoComplete(toComplete)

		},
	}
}

// Output:
// > dapla rm /foo/bar
//  Dataset /foo/bar (42 versions) successfully deleted
//
// > dapla rm --debug /foo/bar
//  /foo/bar [versiontimestamp]
//  	gs://bucket/random/prefix/file1 123
//  	gs://bucket/random/prefix/file2 123
//  	gs://bucket/random/prefix/file3 123
//  	gs://bucket/random/prefix/file4 123
//  /foo/bar [versiontimestamp2]
//  	gs://bucket2/some/other/path/prefix/file1 123
//  	gs://bucket2/some/other/path/prefix/file2 123
//  	gs://bucket2/some/other/path/prefix/file2 123
//  	gs://bucket2/some/other/path/prefix/file2 123
//  Number of deleted files: 1234
//  Total size: 123456789 KiB
//  Dataset /foo/bar (42 versions) successfully deleted
//
// > dapla rm --dry-run /foo/bar
//  Dataset /foo/bar (42 versions) successfully deleted
// The dry-run flag was set. NO FILES WERE DELETED.
func printDeleteResponse(deleteResponse *rest.DeleteDatasetResponse, output io.Writer, debug bool, dryRun bool) {
	writer := bufio.NewWriter(output)
	defer writer.Flush()

	if debug {
		for _, datasetVersion := range deleteResponse.DatasetVersion {
			fmt.Fprintf(writer, "Version: %s\n", datasetVersion.Timestamp)
			for _, deletedFile := range datasetVersion.DeletedFiles {
				fmt.Fprintf(writer, "\t%s\n", deletedFile.Uri)
			}
		}
		fmt.Fprintf(writer, "\nnumber of deleted files: %d\n", deleteResponse.GetNumberOfFiles())
		fmt.Fprintf(writer, "total size of deleted files: %d\n", deleteResponse.TotalSize)
	}
	fmt.Fprintf(writer, "Dataset %s (%d %s) successfully deleted\n\r",
		deleteResponse.DatasetPath,
		len(deleteResponse.DatasetVersion),
		pluralize("version", len(deleteResponse.DatasetVersion)))

	if dryRun {
		fmt.Fprintf(writer, "The dry-run flag was set. NO FILES WERE DELETED.")
	}
}

func pluralize(text string, n int) string {
	if n > 1 {
		return text + "s"
	}
	return text
}
