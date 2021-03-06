package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"time"

	"github.com/briandowns/spinner"
	"github.com/mitchellh/go-homedir"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

// Viper configuration keys
const (
	CFGDebug     = "debug"
	CFGJupyter   = "jupyter"
	CFGAPIs      = "apis"
	CFGAuthToken = "authtoken"
)

var cfgFile string
var rootCmd = &cobra.Command{
	Use:     "dapla",
	Version: versionInfo(),
	Short:   "dapla command line utility",
	Long:    `The dapla command is a collection of utilities you can use with the dapla platform.`,
}

// Execute uses the command line args  and run through the command tree finding appropriate matches
// for commands and then corresponding flags.
func Execute() error {
	return rootCmd.Execute()
}

func versionInfo() string {
	info := fmt.Sprintf("%v", Version)
	if GitSha1Hash != "" {
		info += fmt.Sprintf("\n  Rev:        %v", GitSha1Hash)
	}
	if BuildTime != "" {
		info += fmt.Sprintf("\n  Built:      %v", BuildTime)
	}
	info += fmt.Sprintf("\n  Go version: %v", runtime.Version())
	info += fmt.Sprintf("\n  OS/Arch:    %v/%v", runtime.GOOS, runtime.GOARCH)
	return info
}

func init() {
	cobra.OnInitialize(initConfig)

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "",
		"config file (default is $HOME/.dapla-cli.yml)")
	rootCmd.PersistentFlags().StringToString("apis", map[string]string{},
		"override API URIs")
	rootCmd.PersistentFlags().Bool("jupyter", false,
		"set this flag to fetch user auth token from jupyter")
	rootCmd.PersistentFlags().String("authtoken", "",
		"explicit user auth token (if running outside of jupyter)")
	rootCmd.PersistentFlags().BoolP("debug", "d", false,
		"print debug information")

	viper.BindPFlag("debug", rootCmd.PersistentFlags().Lookup("debug"))
	viper.BindPFlag("jupyter", rootCmd.PersistentFlags().Lookup("jupyter"))
	viper.BindPFlag("apis", rootCmd.PersistentFlags().Lookup("apis"))
	viper.BindPFlag("authtoken", rootCmd.PersistentFlags().Lookup("authtoken"))
}

// initConfig func locates and assembles dapla-cli configuration from file
func initConfig() {
	// Use config file from the flag
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		// Find home directory.
		home, err := homedir.Dir()
		cobra.CheckErr(err)

		// Search config in home directory with name ".dapla-cli" (without extension).
		viper.AddConfigPath(home)
		viper.SetConfigName(".dapla-cli")
	}

	// Retrieve any overridden config params from the env
	viper.AutomaticEnv()

	// Read config from file
	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// Config file not found; which is okay
		} else {
			panic(fmt.Errorf("configuration error: %s", err))
		}
	}
}

func effectiveConfig() string {
	cfg, _ := json.MarshalIndent(viper.AllSettings(), "", "\t")
	return string(cfg)
}

// newSpinner func creates and starts a new CLI spinner
func newSpinner(prefix string) *spinner.Spinner {
	s := spinner.New(spinner.CharSets[9], 100*time.Millisecond, spinner.WithWriter(os.Stderr))
	s.Color("reset")
	s.Prefix = prefix + " "
	s.Start()
	return s
}
