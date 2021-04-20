package cmd

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"

	errors2 "github.com/pkg/errors"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

const (
	jupyterHUBTokenURL = "JUPYTERHUB_HANDLER_CUSTOM_AUTH_URL"
	jupyterAPIToken    = "JUPYTERHUB_API_TOKEN"
)

// TODO: We don't need any jupyter environment variable, either the token is explicitly provided, or we should try to retrieve it from jupyter

// authToken returns the users JWT token either by using the provided bearer token
// or retrieving it from the jupyter environment
func authTokenOrError() (string, error) {
	if viper.GetBool(CFGJupyter) && viper.GetString(CFGAuthToken) != "" {
		return "", errors2.New("cannot use both --jupyter and --authtoken")
	}

	switch {

	case viper.GetBool(CFGJupyter):
		apiURL := os.Getenv(jupyterHUBTokenURL)
		apiToken := os.Getenv(jupyterAPIToken)
		if apiToken == "" || apiURL == "" {
			return "", errors2.Errorf("missing environment %s or %s", jupyterHUBTokenURL, jupyterAPIToken)
		}
		return fetchJupyterToken(apiURL, apiToken)

	case viper.GetString(CFGAuthToken) != "":
		return viper.GetString(CFGAuthToken), nil

	default:
		return "", errors2.New("Unable to find auth token. Either retrieve this from jupyter (--jupyter) or provide an auth token via --authtoken, $AUTHTOKEN (env) or in the .dapla-cli.yml config file")
	}
}

// requiredAuthToken returns the users JWT token or panics if it could not be retrieved
func authToken() string {
	var authToken, err = authTokenOrError()
	cobra.CheckErr(err)

	return authToken
}

// fetchJupyterToken retrieves the users JWT token from the jupyter environment
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
