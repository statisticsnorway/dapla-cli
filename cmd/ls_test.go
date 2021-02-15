package cmd

import (
	"bytes"
	"github.com/andreyvit/diff"
	"github.com/statisticsnorway/dapla-cli/rest"
	"strings"
	"testing"
	"time"
)

func TestPrintNewLine(t *testing.T) {

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
}

func TestPrintTabular(t *testing.T) {

	tests := []struct {
		response       rest.ListDatasetResponse
		expectedOutput string
	}{
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{Path: "/foo/bar"},
			rest.ListDatasetElement{Path: "/foo/baz"},
		},
			"/foo/bar       /foo/baz", // TODO how to create expected output without adding correct number of whitespaces manually?
		},
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{Path: "/foo2/bar"},
			rest.ListDatasetElement{Path: "/foo2/baz"},
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
		response       rest.ListDatasetResponse
		expectedOutput string
	}{
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{
				Path:      "/foo/bar",
				CreatedBy: "Hadrien Kohl",
				CreatedAt: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     0,
			},
			rest.ListDatasetElement{
				Path:      "/foo/baz",
				CreatedBy: "Bjørn-André Skaar",
				CreatedAt: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     1,
			},
		}, // TODO how to create expected output without adding correct number of whitespaces manually?
			"Name                            Author                          Created                         Type                            Valuation                       State\n" +
				"/foo/bar                        Hadrien Kohl                    2000-01-01T00:00:00Z            BOUNDED                         INTERNAL                        INPUT\n" +
				"/foo/baz/                       Bjørn-André Skaar               3000-01-01T00:00:00Z            BOUNDED                         INTERNAL                        INPUT",
		},
		{rest.ListDatasetResponse{
			rest.ListDatasetElement{
				Path:      "/foo2/bar",
				CreatedBy: "Hadrien Kohl",
				CreatedAt: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     0,
			},
			rest.ListDatasetElement{
				Path:      "/foo2/baz",
				CreatedBy: "Bjørn-André Skaar",
				CreatedAt: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				Type:      "BOUNDED",
				Valuation: "INTERNAL",
				State:     "INPUT",
				Depth:     1,
			},
		}, // TODO how to create expected output without adding correct number of whitespaces manually?
			"Name                            Author                          Created                         Type                            Valuation                       State\n" +
				"/foo2/bar                       Hadrien Kohl                    2000-01-01T00:00:00Z            BOUNDED                         INTERNAL                        INPUT\n" +
				"/foo2/baz/                      Bjørn-André Skaar               3000-01-01T00:00:00Z            BOUNDED                         INTERNAL                        INPUT",
		},
	}

	for _, values := range tests {
		var output bytes.Buffer
		printTabularDetails(&values.response, &output)

		if actual, expected := strings.TrimSpace(output.String()),
			strings.TrimSpace(values.expectedOutput); actual != expected {
			t.Errorf("Result not as expected:\n%v", diff.LineDiff(expected, actual))
		}
	}
}
