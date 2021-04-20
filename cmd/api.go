package cmd

import (
	"errors"
	"fmt"

	"github.com/spf13/viper"
)

const (
	APINameDataMaintenanceSvc = "data-maintenance"
	APINamePseudoSvc          = "dapla-pseudo-service"
)

func apiUrlOf(apiName string) string {

	if apiUrl := viper.GetStringMapString(CFGAPIs)[apiName]; apiUrl != "" {
		return apiUrl
	}

	// TODO: Don't panic
	panic(errors.New(fmt.Sprintf("missing api base url for %s (specify in config file or via --apis flag)", apiName)))
}
