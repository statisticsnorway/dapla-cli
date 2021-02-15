package rest

import (
	"github.com/google/go-cmp/cmp"
	"gopkg.in/h2non/gock.v1"
	"net/http"
	"testing"
	"time"
)

func TestClient_fetchJupyterToken(t *testing.T) {
	defer gock.Off()

	gock.New("http://server.com").
		Get("/foo/bar/token").
		MatchHeader("Authorization", "^token the api token$").
		Reply(http.StatusOK).
		BodyString(`{ "access_token": "the access token"}`)

	gock.New("http://server.com").
		Reply(http.StatusForbidden)

	token, err := fetchJupyterToken("http://server.com/foo/bar/token", "the api token")
	if err != nil {
		t.Fatal(err)
	}

	if token != "the access token" {
		t.Errorf("expected %s but got %s", "the access token", token)
	}
}

func TestClient_ListDatasets(t *testing.T) {
	defer gock.Off()

	gock.New("http://server.com").
		Get("/api/v1/list/foo").
		MatchHeader("Authorization", "^Bearer a secret secret$").
		Reply(http.StatusOK).BodyString(`
[{
	"createdBy": "Ola Nordmann",
	"createdDate": "2000-01-01T00:00:00.123456Z",
    "path": "foo/file1",
	"type": "BOUNDED",
	"valuation": "INTERNAL",
	"state": "INPUT",
	"depth": 1
},{
    "createdBy": "Kari Nordmann",
    "createdDate": "3000-01-01T00:00:00.123456Z",
    "path": "foo/bar/file2",
	"type": "UNBOUNDED",
	"valuation": "SENSITIVE",
	"state": "RAW",
	"depth": 1
},{
    "createdBy": "Kari Nordmann",
    "createdDate": "3000-01-01T00:00:00.123456Z",
    "path": "foo/bar",
	"type": "",
	"valuation": "",
	"state": "",
	"depth": 2
}]
`)

	gock.New("http://server.com").
		Reply(http.StatusForbidden)

	var client = NewClient("http://server.com", "a secret secret")

	var expectedDataset = ListDatasetElement{
		CreatedAt: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
		CreatedBy: "Ola Nordmann",
		Path:      "foo/file1",
		Type:      "BOUNDED",
		Valuation: "INTERNAL",
		State:     "INPUT",
		Depth:     1,
	}

	var expectedFolder = ListDatasetElement{
		CreatedAt: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
		CreatedBy: "Kari Nordmann",
		Path:      "foo/bar",
		Type:      "",
		Valuation: "",
		State:     "",
		Depth:     2,
	}

	datasets, err := client.ListDatasets("foo")
	if err != nil {
		t.Errorf("Got error %v", err)
	}

	if len(*datasets) != 3 {
		t.Errorf("Invalid response")
	}
	var datasetElement = (*datasets)[0]
	if !cmp.Equal(expectedDataset, datasetElement) {
		t.Errorf("Expected %v, but got %v", expectedDataset, datasetElement)
	}

	var folderElement = (*datasets)[2]
	if !cmp.Equal(expectedFolder, folderElement) {
		t.Errorf("Expected %v, but got %v", expectedFolder, folderElement)
	}
}

func TestClient_DeleteDatasets(t *testing.T) {
	defer gock.Off()

	gock.New("http://server.com").
		Delete("/api/v1/delete/foo/bar").
		MatchHeader("Authorization", "^Bearer a secret secret$").
		Reply(http.StatusOK).BodyString(`{
	"datasetPath": "/foo/bar",
	"totalSize": 15,
	"deletedVersions":[{
		"timestamp": "2000-01-01T00:00:00.123456Z",
		"deletedFiles":[{
			"uri": "gs://bucket/prefix/foo/bar/v1/file1",
			"size": 1
		},{
			"uri": "gs://bucket/prefix/foo/bar/v1/file2",
			"size": 2
		}]
	},{
		"timestamp": "3000-01-01T00:00:00.123456Z",
		"deletedFiles":[{
			"uri": "gs://bucket/prefix/foo/bar/v2/file1",
			"size": 4
		},{
			"uri": "gs://bucket/prefix/foo/bar/v2/file2",
			"size": 8
		}]
	}]
}`)

	expectedResponse := DeleteDatasetResponse{
		DatasetPath: "/foo/bar",
		TotalSize:   15,
		DatasetVersion: []DatasetVersion{
			{
				Timestamp: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v1/file1", Size: 1},
					{Uri: "gs://bucket/prefix/foo/bar/v1/file2", Size: 2},
				},
			},
			{
				Timestamp: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v2/file1", Size: 4},
					{Uri: "gs://bucket/prefix/foo/bar/v2/file2", Size: 8},
				},
			},
		},
	}

	gock.New("http://server.com").
		Reply(http.StatusForbidden)

	var client = NewClient("http://server.com", "a secret secret")

	response, err := client.DeleteDatasets("foo/bar", false)
	if err != nil {
		t.Errorf("Got error %v", err)
	}

	if !cmp.Equal(expectedResponse, *response) {
		t.Errorf("Expected %v, but got %v", expectedResponse, response)
	}
}

func TestClient_DeleteDatasetsDryRun(t *testing.T) {
	gock.New("http://server.com").
		Delete("/api/v1/delete/foo/bar").
		MatchParam("dry-run", "true").
		MatchHeader("Authorization", "^Bearer a secret secret$").
		Reply(http.StatusOK).BodyString(`{
	"datasetPath": "/foo/bar",
	"totalSize": 15,
	"deletedVersions":[{
		"timestamp": "2000-01-01T00:00:00.123456Z",
		"deletedFiles":[{
			"uri": "gs://bucket/prefix/foo/bar/v1/file1",
			"size": 1
		},{
			"uri": "gs://bucket/prefix/foo/bar/v1/file2",
			"size": 2
		}]
	},{
		"timestamp": "3000-01-01T00:00:00.123456Z",
		"deletedFiles":[{
			"uri": "gs://bucket/prefix/foo/bar/v2/file1",
			"size": 4
		},{
			"uri": "gs://bucket/prefix/foo/bar/v2/file2",
			"size": 8
		}]
	}]
}`)

	expectedResponse := DeleteDatasetResponse{
		DatasetPath: "/foo/bar",
		TotalSize:   15,
		DatasetVersion: []DatasetVersion{
			{
				Timestamp: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v1/file1", Size: 1},
					{Uri: "gs://bucket/prefix/foo/bar/v1/file2", Size: 2},
				},
			},
			{
				Timestamp: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v2/file1", Size: 4},
					{Uri: "gs://bucket/prefix/foo/bar/v2/file2", Size: 8},
				},
			},
		},
	}

	gock.New("http://server.com").
		Reply(http.StatusForbidden)

	var client = NewClient("http://server.com", "a secret secret")

	response, err := client.DeleteDatasets("foo/bar", true)
	if err != nil {
		t.Errorf("Got error %v", err)
	}

	if !cmp.Equal(expectedResponse, *response) {
		t.Errorf("Expected %v, but got %v", expectedResponse, response)
	}
}

func TestClient_DeleteDatasetResponseMethods(t *testing.T) {
	deleteDatasetResponse := DeleteDatasetResponse{
		DatasetPath: "/foo/bar",
		TotalSize:   15,
		DatasetVersion: []DatasetVersion{
			{
				Timestamp: time.Date(2000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v1/file1", Size: 1},
					{Uri: "gs://bucket/prefix/foo/bar/v1/file2", Size: 2},
				},
			},
			{
				Timestamp: time.Date(3000, 1, 1, 0, 0, 0, 123456000, time.UTC),
				DeletedFiles: []DatasetFile{
					{Uri: "gs://bucket/prefix/foo/bar/v2/file1", Size: 4},
					{Uri: "gs://bucket/prefix/foo/bar/v2/file2", Size: 8},
				},
			},
		},
	}
	expectedNumberOfFiles := 4

	numberOfFiles := deleteDatasetResponse.GetNumberOfFiles()

	if expectedNumberOfFiles != numberOfFiles {
		t.Errorf("Expected total number of files to be %v, but got %v", expectedNumberOfFiles, numberOfFiles)
	}

}
