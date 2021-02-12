package cmd

import (
	"bytes"
	"github.com/andreyvit/diff"
	"github.com/statisticsnorway/dapla-cli/rest"
	"strings"
	"testing"
)

func TestExecute(t *testing.T) {
	cmd := newLsCommand()
	b := bytes.NewBufferString("")
	cmd.SetOut(b)
	cmd.SetArgs([]string{"/path"})
	cmd.Execute()

	out := b.String()
	if out != "rm" {
		t.Fatalf("expected \"%s\" got \"%s\"", "hi", string(out))
	}
}

func Test(t *testing.T) {

	tests := []struct {
		response       rest.ListDatasetResponse
		expectedOutput string
	}{
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{Path: "/foo/bar"},
			rest.ListDatasetElement{Path: "/foo/baz"},
		},
			"/foo/bar\n/foo/baz",
		},
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{Path: "/foo2/bar"},
			rest.ListDatasetElement{Path: "/foo2/baz"},
		},
			"/foo2/bar\n/foo2/baz",
		},
	}

	for _, values := range tests {
		var output bytes.Buffer
		printNewLine(&values.response, &output)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutput); actual != expected {
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
	}
	// TODO test the other print functions
}
