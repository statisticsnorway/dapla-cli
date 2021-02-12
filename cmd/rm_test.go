package cmd

import (
	"bytes"
	"fmt"
	"github.com/andreyvit/diff"
	"github.com/statisticsnorway/dapla-cli/rest"
	"strings"
	"testing"
	"time"
)

func TestExecuteRM(t *testing.T) {

	tests := []struct {
		response                     rest.DeleteDatasetResponse
		expectedOutput               string
		expectedOutputDebug          string
		expectedOutputDryRun         string
		expectedOutputDebugAndDryRun string
	}{
		{response: rest.DeleteDatasetResponse{
			DatasetPath: "/foo/bar",
			TotalSize:   15,
			DatasetVersion: []rest.DatasetVersion{
				{
					Timestamp: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
					DeletedFiles: []rest.DatasetFile{
						{Uri: "gs://bucket/prefix/foo/bar/v1/file1", Size: 1},
						{Uri: "gs://bucket/prefix/foo/bar/v1/file2", Size: 2},
					},
				},
				{
					Timestamp: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
					DeletedFiles: []rest.DatasetFile{
						{Uri: "gs://bucket/prefix/foo/bar/v2/file1", Size: 4},
						{Uri: "gs://bucket/prefix/foo/bar/v2/file2", Size: 8},
					},
				},
			},
		},

			expectedOutput: "Dataset /foo/bar (2 versions) successfully deleted",
			expectedOutputDebug: "Version: 2000-01-01 00:00:00.123456 +0000 UTC\n" +
				"\tgs://bucket/prefix/foo/bar/v1/file1\n" +
				"\tgs://bucket/prefix/foo/bar/v1/file2\n" +
				"Version: 3000-01-01 00:00:00.123456 +0000 UTC\n" +
				"\tgs://bucket/prefix/foo/bar/v2/file1\n" +
				"\tgs://bucket/prefix/foo/bar/v2/file2\n\n" +
				"number of deleted files: 4\n" +
				"total size of deleted files: 15\n" +
				"Dataset /foo/bar (2 versions) successfully deleted",
			expectedOutputDryRun: "Dataset /foo/bar (2 versions) successfully deleted\n\r" +
				"The dry-run flag was set. NO FILES WERE DELETED.",
			expectedOutputDebugAndDryRun: "Version: 2000-01-01 00:00:00.123456 +0000 UTC\n" +
				"\tgs://bucket/prefix/foo/bar/v1/file1\n" +
				"\tgs://bucket/prefix/foo/bar/v1/file2\n" +
				"Version: 3000-01-01 00:00:00.123456 +0000 UTC\n" +
				"\tgs://bucket/prefix/foo/bar/v2/file1\n" +
				"\tgs://bucket/prefix/foo/bar/v2/file2\n\n" +
				"number of deleted files: 4\n" +
				"total size of deleted files: 15\n" +
				"Dataset /foo/bar (2 versions) successfully deleted\n\r" +
				"The dry-run flag was set. NO FILES WERE DELETED.",
		},
	}

	for _, values := range tests {
		var output bytes.Buffer

		// Test rm without flags
		printDeleteResponse(&values.response, &output, false, false)
		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutput); actual != expected {
			fmt.Println("***** <rm> WITHOUT FLAGS *****")
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
		output.Reset()

		// Test rm with debug flag
		printDeleteResponse(&values.response, &output, true, false)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutputDebug); actual != expected {
			fmt.Println("***** <rm> WITH DEBUG FLAG *****")
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
		output.Reset()

		// Test rm with dry-run flag
		printDeleteResponse(&values.response, &output, false, true)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutputDryRun); actual != expected {
			fmt.Println("***** <rm> WITH DRY-RUN FLAG *****")
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
		output.Reset()

		// Test rm with both debug and dry-run flags
		printDeleteResponse(&values.response, &output, true, true)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutputDebugAndDryRun); actual != expected {
			fmt.Println("***** <rm> WITH DEBUG AND DRY-RUN FLAG *****")
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
		output.Reset()

	}
}
