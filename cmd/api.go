package cmd

import (
	"fmt"

	"github.com/spf13/viper"
)

// Name of APIs that the dapla-cli communicates with
const (
	APINameDataMaintenanceSvc = "data-maintenance"
	APINamePseudoSvc          = "dapla-pseudo-service"
)

func apiURLOf(apiName string) string {

	if apiURL := viper.GetStringMapString(CFGAPIs)[apiName]; apiURL != "" {
		return apiURL
	}

	// TODO: Don't panic
	panic(fmt.Errorf("missing api base url for %s (specify in config file or via --apis flag)", apiName))
}
