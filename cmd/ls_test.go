package cmd

import (
	"bytes"
	"strings"
	"testing"
	"time"

	"github.com/acarl005/stripansi"
	"github.com/andreyvit/diff"
	"github.com/statisticsnorway/dapla-cli/maintenance"
)

func TestPrintNewLine(t *testing.T) {

	tests := []struct {
		response       maintenance.ListDatasetResponse
		expectedOutput string
	}{
		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{Path: "/foo/bar"},
			maintenance.ListDatasetElement{Path: "/foo/baz"},
		},
			"/foo/bar\n/foo/baz",
		},
		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{Path: "/foo2/bar"},
			maintenance.ListDatasetElement{Path: "/foo2/baz"},
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
}

func TestPrintTabular(t *testing.T) {

	tests := []struct {
		response       maintenance.ListDatasetResponse
		expectedOutput string
	}{
		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{Path: "/foo/bar"},
			maintenance.ListDatasetElement{Path: "/foo/baz"},
		},
			"/foo/bar       /foo/baz", // TODO how to create expected output without adding correct number of whitespaces manually?
		},
		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{Path: "/foo2/bar"},
			maintenance.ListDatasetElement{Path: "/foo2/baz"},
		},
			"/foo2/bar      /foo2/baz", // TODO how to create expected output without adding correct number of whitespaces manually?
		},
	}

	for _, values := range tests {
		var output bytes.Buffer
		printTabular(&values.response, &output)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutput); actual != expected {
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
	}
}

func TestPrintTabularDetails(t *testing.T) {

	tests := []struct {
		response       maintenance.ListDatasetResponse
		expectedOutput string
	}{
		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{
				Path:      "/foo/bar2",
				CreatedBy: "Hadrien Kohl",
				CreatedAt: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     0,
			},
			maintenance.ListDatasetElement{
				Path:      "/foo/baz",
				CreatedBy: "Bjørn-André Skaar",
				CreatedAt: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     1,
			},
		}, `
Name           Author              Created                 Type           Valuation      State
/foo/bar2       Hadrien Kohl        2000-01-01T00:00:00Z    BOUNDED        INTERNAL       INPUT
/foo/baz/       Bjørn-André Skaar   3000-01-01T00:00:00Z    BOUNDED        INTERNAL       INPUT
`,
		},

		{maintenance.ListDatasetResponse{
			maintenance.ListDatasetElement{
				Path:      "/foo2/bar",
				CreatedBy: "Hadrien Kohl",
				CreatedAt: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     0,
			},
			maintenance.ListDatasetElement{
				Path:      "/foo2/baz",
				CreatedBy: "Bjørn-André Skaar",
				CreatedAt: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     1,
			},
		}, `
Name           Author              Created                 Type           Valuation      State
/foo2/bar       Hadrien Kohl        2000-01-01T00:00:00Z    BOUNDED        INTERNAL       INPUT
/foo2/baz/      Bjørn-André Skaar   3000-01-01T00:00:00Z    BOUNDED        INTERNAL       INPUT
`,
		},
	}

	for _, values := range tests {
		var output bytes.Buffer
		printTabularDetails(&values.response, &output)
		if actual, expected :=
			diff.TrimLinesInString(stripansi.Strip(output.String())), // actual
			diff.TrimLinesInString(values.expectedOutput); // expected
		actual != expected {

			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
	}
}
