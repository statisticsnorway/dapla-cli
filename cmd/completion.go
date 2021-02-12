/*
Copyright © 2021 NAME HERE <EMAIL ADDRESS>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"fmt"
	"github.com/statisticsnorway/dapla-cli/rest"
	"os"
	"strings"

	"github.com/spf13/cobra"
)

var completionCmd = &cobra.Command{
	Use:   "completion [bash|zsh|fish|powershell]",
	Short: "Generate completion script",
	Long: `To load completions:
Bash:
$ source <(yourprogram completion bash)
# To load completions for each session, execute once:
Linux:
  $ yourprogram completion bash > /etc/bash_completion.d/yourprogram
MacOS:
  $ yourprogram completion bash > /usr/local/etc/bash_completion.d/yourprogram
Zsh:
# If shell completion is not already enabled in your environment you will need
# to enable it.  You can execute the following once:
$ echo "autoload -U compinit; compinit" >> ~/.zshrc
# To load completions for each session, execute once:
$ yourprogram completion zsh > "${fpath[1]}/_yourprogram"
# You will need to start a new shell for this setup to take effect.
Fish:
$ yourprogram completion fish | source
# To load completions for each session, execute once:
$ yourprogram completion fish > ~/.config/fish/completions/yourprogram.fish
Powershell:
PS> yourprogram completion powershell | Out-String | Invoke-Expression
# To load completions for every new session, run:
PS> yourprogram completion powershell > yourprogram.ps1
# and source this file from your powershell profile.
`,
	DisableFlagsInUseLine: true,
	ValidArgs:             []string{"bash", "zsh", "fish", "powershell"},
	Args:                  cobra.ExactValidArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		switch args[0] {
		case "bash":
			cmd.Root().GenBashCompletion(os.Stdout)
		case "zsh":
			cmd.Root().GenZshCompletion(os.Stdout)
		case "fish":
			cmd.Root().GenFishCompletion(os.Stdout, true)
		case "powershell":
			cmd.Root().GenPowerShellCompletion(os.Stdout)
		}
	},
}

func init() {
	rootCmd.AddCommand(completionCmd)

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// completionCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// completionCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}

// TODO: func doAutoComplete(toComplete string, client * rest.Client) ([]string, cobra.ShellCompDirective) {
// TODO: func (client * rest.Client) DoAutoComplete(toComplete string) ([]string, cobra.ShellCompDirective) {
func doAutoComplete(toComplete string) ([]string, cobra.ShellCompDirective) {
	var client, err = initClient()
	if err != nil {
		return handleCompleteError("could not initialize client: %s", err)
	}

	if toComplete == "" {
		return []string{"/"}, cobra.ShellCompDirectiveNoSpace | cobra.ShellCompDirectiveNoFileComp
	}

	var res *rest.ListDatasetResponse

	if toComplete == "/" {
		res, err = client.ListDatasets(toComplete)
		if err != nil {
			return handleCompleteError("could not fetch list: %s", err)
		} else {
			return formatCompleteResult(res)
		}
	}

	// Special case with missing root slash.
	if !strings.HasPrefix(toComplete, "/") {
		return []string{"/" + toComplete}, cobra.ShellCompDirectiveNoSpace | cobra.ShellCompDirectiveNoFileComp
	}

	// Ask for list without last element
	var parentPath = toComplete[0:strings.LastIndex(toComplete, "/")]
	res, err = client.ListDatasets(parentPath)
	if err != nil {
		return handleCompleteError("could not fetch list: ", err)
	}

	// Check if last element is a valid path / dataset
	var partialPath = toComplete[strings.LastIndex(toComplete, "/")+1:]
	for _, element := range *res {
		// We have a complete match, ask data-maintenance for elements on that path
		if toComplete == element.Path {
			res, err = client.ListDatasets(toComplete)
			if err != nil {
				return handleCompleteError("could not fetch list: ", err)
			} else {
				return formatCompleteResult(res)
			}
		}
	}

	var matches rest.ListDatasetResponse
	for _, element := range *res {
		// find all elements that matches the last element in the provided path
		var lastPart = element.Path[strings.LastIndex(element.Path, "/")+1 : len(element.Path)]
		if strings.HasPrefix(lastPart, partialPath) {
			matches = append(matches, element)
		}
	}
	return formatCompleteResult(&matches)
}

// Format and set the flags based on the given elements
func formatCompleteResult(elements *rest.ListDatasetResponse) ([]string, cobra.ShellCompDirective) {
	var suggestions []string
	var hasFolders = false
	var flags = cobra.ShellCompDirectiveNoFileComp

	for _, element := range *elements {
		if element.IsFolder() {
			hasFolders = true
		}
		suggestions = append(suggestions, normalizeCompleteElement(element))
	}

	// No space if folder or more than one element
	if hasFolders || len(*elements) > 1 {
		flags = flags | cobra.ShellCompDirectiveNoSpace
	}

	return suggestions, flags
}

// Handle the errors from the auto complete method.
func handleCompleteError(message string, err error) ([]string, cobra.ShellCompDirective) {
	_, _ = fmt.Fprintln(os.Stderr, message, err.Error())
	return nil, cobra.ShellCompDirectiveError | cobra.ShellCompDirectiveNoFileComp
}

// Normalize the result of auto completion.
func normalizeCompleteElement(element rest.ListDatasetElement) string {
	path := element.Path
	if strings.HasSuffix(element.Path, "/") {
		path = strings.TrimSuffix(path, "/")
	}
	if element.IsFolder() {
		path = path + "/"
	}
	return path
}
