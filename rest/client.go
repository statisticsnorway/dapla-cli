package rest

import (
	"encoding/json"
	"fmt"
	errors2 "github.com/pkg/errors"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"
)

type Client struct {
	BaseURL    string
	Client     *http.Client
	authBearer string
}

const jupyterHUBTokenURL = "JUPYTERHUB_HANDLER_CUSTOM_AUTH_URL"
const jupyterAPIToken = "JUPYTERHUB_API_TOKEN"

type ListDatasetElement struct {
	Path      string    `json:"path"`
	CreatedBy string    `json:"createdBy"`
	CreatedAt time.Time `json:"createdDate"`
	Type      string    `json:"type"`
	Valuation string    `json:"valuation"`
	State     string    `json:"state"`
	Depth     int       `json:"depth"`
}

type ListDatasetResponse []ListDatasetElement

type DeleteDatasetResponse struct {
	DatasetPath    string           `json:"datasetPath"`
	TotalSize      uint64           `json:"totalSize"`
	DatasetVersion []DatasetVersion `json:"deletedVersions"`
}

type DatasetVersion struct {
	Timestamp    time.Time     `json:"timestamp"`
	DeletedFiles []DatasetFile `json:"deletedFiles"`
}

func (r DeleteDatasetResponse) GetNumberOfFiles() int {
	noOfFiles := 0
	for _, datasetVersion := range r.DatasetVersion {
		noOfFiles = noOfFiles + len(datasetVersion.DeletedFiles)
	}
	return noOfFiles
}

type DatasetFile struct {
	Uri  string `json:"uri"`
	Size uint64 `json:"size"`
}

func (e ListDatasetElement) IsFolder() bool {
	return e.Depth > 0
}

func (e ListDatasetElement) IsDataset() bool {
	return !e.IsFolder()
}

func NewClient(baseURL string, authBearer string) *Client {
	return &Client{
		BaseURL:    baseURL,
		Client:     http.DefaultClient,
		authBearer: authBearer,
	}
}

func NewClientWithJupyter(baseURL string) (*Client, error) {

	apiURL := os.Getenv(jupyterHUBTokenURL)
	apiToken := os.Getenv(jupyterAPIToken)
	if apiToken == "" || apiURL == "" {
		return nil, errors2.Errorf("missing environment %s or %s", jupyterHUBTokenURL, jupyterAPIToken)
	}

	token, err := fetchJupyterToken(apiURL, apiToken)
	if err != nil {
		return nil, err
	}
	return &Client{
		BaseURL:    baseURL,
		Client:     http.DefaultClient,
		authBearer: token,
	}, nil
}

// Fetch the JTW token from jupyter environment
func fetchJupyterToken(apiURL, apiToken string) (string, error) {
	parsedURL, err := url.Parse(apiURL)
	if err != nil {
		return "", err
	}

	client := http.DefaultClient
	req, err := http.NewRequest(http.MethodGet, parsedURL.String(), nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", fmt.Sprintf("token %s", apiToken))
	res, err := client.Do(req)
	if err != nil {
		return "", err
	}

	if res.StatusCode < http.StatusOK || res.StatusCode >= http.StatusBadRequest {
		return "", fmt.Errorf("unknown error, status code: %d", res.StatusCode)
	}

	var data map[string]interface{}
	err = json.NewDecoder(res.Body).Decode(&data)
	if err != nil {
		return "", nil
	}

	return data["access_token"].(string), nil
}

func (c *Client) createRequest(method, url string, queryParams map[string]string) (*http.Request, error) {
	req, err := http.NewRequest(method, url, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", c.authBearer))
	req.Header.Set("Accept", "application/json; charset=utf-8")
	req.Header.Set("Content-Type", "application/json; charset=utf-8")

	if queryParams != nil && len(queryParams) > 0 {
		query := req.URL.Query()
		for paramName, paramValue := range queryParams {
			query.Add(paramName, paramValue)
		}
		req.URL.RawQuery = query.Encode()

	}
	return req, nil
}

func (c *Client) DeleteDatasets(path string, dryRun bool) (*DeleteDatasetResponse, error) {

	var req *http.Request
	var err error

	if dryRun {
		req, err = c.createRequest("DELETE", fmt.Sprintf("%s/api/v1/delete/%s", c.BaseURL, path),
			map[string]string{"dry-run": strconv.FormatBool(dryRun)})
	} else {
		req, err = c.createRequest("DELETE", fmt.Sprintf("%s/api/v1/delete/%s", c.BaseURL, path), nil)
	}

	if err != nil {
		return nil, err
	}

	res, err := c.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode < http.StatusOK || res.StatusCode >= http.StatusBadRequest {
		return nil, fmt.Errorf("unknown error, status code: %d", res.StatusCode)
	}

	resp := DeleteDatasetResponse{}
	err = json.NewDecoder(res.Body).Decode(&resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}

func (c *Client) ListDatasets(path string) (*ListDatasetResponse, error) {
	req, err2 := c.createRequest("GET", fmt.Sprintf("%s/api/v1/list/%s", c.BaseURL, path), nil)
	if err2 != nil {
		return nil, err2
	}

	res, err := c.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode < http.StatusOK || res.StatusCode >= http.StatusBadRequest {
		return nil, fmt.Errorf("unknown error, status code: %d", res.StatusCode)
	}

	resp := ListDatasetResponse{}
	err = json.NewDecoder(res.Body).Decode(&resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}
