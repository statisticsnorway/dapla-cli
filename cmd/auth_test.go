package cmd

import (
	"net/http"
	"testing"

	"github.com/stretchr/testify/assert"

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

	assert.Nil(t, err)
	assert.Equal(t, token, "the access token")
}
