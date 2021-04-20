package export

import (
	"net/http"
	"testing"

	"gopkg.in/h2non/gock.v1"
)

func TestClient_Export(t *testing.T) {
	defer gock.Off()

	gock.New("http://server.com").
		Post("export").
		MatchHeader("Authorization", "^Bearer a secret secret$").
		Reply(http.StatusOK).BodyString(`
{
   "targetUri": "gs://some-export-bucket/export/path/to/target/20210416-testexport.zip"
}
`)
	gock.New("http://server.com").
		Reply(http.StatusForbidden)

	client := NewClient("http://server.com", "a secret secret", true)
	gock.InterceptClient(client.RestClient.GetClient())

	var req = Request{
		DatasetPath:       "/path/to/dataset",
		TargetPath:        "/path/to/target",
		TargetContentName: "testexport",
		TargetPassword:    "kensentme",
		Depseudonymize:    true,
		PseudoRules: []PseudoRule{
			{Pattern: "**/SomeField", Func: "fpe-anychar(somesecret1)"},
		},
	}

	_, err := client.Export(req)
	if err != nil {
		t.Errorf("Got error %v", err)
	}
}
