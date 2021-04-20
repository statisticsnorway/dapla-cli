package maintenance

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"strconv"
	"time"
)

// Client struct is a facade against the data-maintenance API
type Client struct {
	BaseURL    string
	Client     *http.Client
	authBearer string
}

// HTTPError holds information returned from an erroneous HTTP request, such as status code and error message
type HTTPError struct {
	statusCode int
	message    string
}

func (httpError *HTTPError) Error() string {
	return httpError.message + " (" + strconv.Itoa(httpError.statusCode) + ")"
}

// ListDatasetElement struct holds one result item from the ListDatasets method
type ListDatasetElement struct {
	Path      string    `json:"path"`
	CreatedBy string    `json:"createdBy"`
	CreatedAt time.Time `json:"createdDate"`
	Type      string    `json:"type"`
	Valuation string    `json:"valuation"`
	State     string    `json:"state"`
	Depth     int       `json:"depth"`
}

// ListDatasetResponse holds an array of result item from the ListDatasets method
type ListDatasetResponse []ListDatasetElement

// DeleteDatasetResponse holds results from invoking the DeteDatasets method
type DeleteDatasetResponse struct {
	DatasetPath    string           `json:"datasetPath"`
	TotalSize      uint64           `json:"totalSize"`
	DatasetVersion []DatasetVersion `json:"deletedVersions"`
}

// DatasetVersion holds an array of deleted files for a specific version/timestamp of a dataset (after rm command)
type DatasetVersion struct {
	Timestamp    time.Time     `json:"timestamp"`
	DeletedFiles []DatasetFile `json:"deletedFiles"`
}

// GetNumberOfFiles returns the number of deleted files from a DeleteDatasetResponse
func (r DeleteDatasetResponse) GetNumberOfFiles() int {
	noOfFiles := 0
	for _, datasetVersion := range r.DatasetVersion {
		noOfFiles = noOfFiles + len(datasetVersion.DeletedFiles)
	}
	return noOfFiles
}

// DatasetFile holds information about a dataset file
type DatasetFile struct {
	URI  string `json:"uri"`
	Size uint64 `json:"size"`
}

// IsFolder returns true iff a ListDatasetElement represents a folder
func (e ListDatasetElement) IsFolder() bool {
	return e.Depth > 0
}

// IsDataset returns true iff a ListDatasetElement represents a dataset
func (e ListDatasetElement) IsDataset() bool {
	return !e.IsFolder()
}

// NewClient func creates a new client that talks with the data-maintenance API
func NewClient(baseURL string, authBearer string) *Client {
	return &Client{
		BaseURL:    baseURL,
		Client:     http.DefaultClient,
		authBearer: authBearer,
	}
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

// DeleteDatasets client method implements rm command for a specific path
func (c *Client) DeleteDatasets(path string, dryRun bool) (*DeleteDatasetResponse, error) {

	var req *http.Request
	var err error

	req, err = c.createRequest("DELETE", fmt.Sprintf("%s/api/v1/delete/%s", c.BaseURL, path),
		map[string]string{"dry-run": strconv.FormatBool(dryRun)})

	if err != nil {
		return nil, err
	}

	res, err := c.Client.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.StatusCode < http.StatusOK || res.StatusCode >= http.StatusBadRequest {
		bytes, _ := ioutil.ReadAll(res.Body)
		return nil, &HTTPError{
			statusCode: res.StatusCode,
			message:    string(bytes),
		}
	}

	resp := DeleteDatasetResponse{}
	err = json.NewDecoder(res.Body).Decode(&resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}

// ListDatasets client method implements ls command for a specific path
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
		bytes, _ := ioutil.ReadAll(res.Body)
		return nil, &HTTPError{
			statusCode: res.StatusCode,
			message:    string(bytes),
		}
	}

	resp := ListDatasetResponse{}
	err = json.NewDecoder(res.Body).Decode(&resp)
	if err != nil {
		return nil, err
	}

	return &resp, nil
}
