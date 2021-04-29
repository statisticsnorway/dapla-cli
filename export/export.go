package export

import (
	"errors"
	"fmt"

	"github.com/go-resty/resty/v2"
)

// PseudoRule represents a single pseudonymization rule
type PseudoRule struct {
	Name    string `json:"name"`
	Pattern string `json:"pattern"`
	Func    string `json:"func"`
}

// Request holds parameters used to invoke the dapla-pseudo-service export endpoint
type Request struct {
	DatasetPath            string       `json:"datasetPath"`
	ColumnSelectors        []string     `json:"columnSelectors"`
	TargetContentName      string       `json:"targetContentName"`
	TargetContentType      string       `json:"targetContentType"`
	TargetPassword         string       `json:"targetPassword"`
	Depseudonymize         bool         `json:"depseudonymize"`
	PseudoRules            []PseudoRule `json:"pseudoRules"`
	PseudoRulesDatasetPath string       `json:"pseudoRulesDatasetPath"`
}

// Response holds results after exporting a dataset
type Response struct {
	TargetURI string `json:"targetUri"`
}

// Client is a facade against the dapla-pseudo-service API
type Client struct {
	baseURL    string
	RestClient resty.Client
	authToken  string
}

// NewClient creates a new client that talks with the dapla-pseudo-service API
func NewClient(baseURL string, token string, debug bool) *Client {
	return &Client{
		RestClient: *resty.New().SetDebug(debug),
		baseURL:    baseURL,
		authToken:  token,
	}
}

// Export client method triggers dataset export in the dapla-pseudo-service
func (c *Client) Export(req Request) (*Response, error) {
	resp, err := c.RestClient.R().
		SetBody(req).
		SetAuthToken(c.authToken).
		SetResult(&Response{}). // or SetResult(AuthSuccess{}).
		Post(fmt.Sprintf("%s/export", c.baseURL))

	if err != nil {
		return nil, err
	}

	if resp.StatusCode() >= 400 {
		return nil, errors.New(resp.Status())
	}

	return resp.Result().(*Response), nil
}
