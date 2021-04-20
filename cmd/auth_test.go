package cmd

import (
	"net/http"
	"testing"

	"gopkg.in/h2non/gock.v1"
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
