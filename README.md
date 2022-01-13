# Bump Docker image tags in a JupyterHub config file

[![CI Tests](https://github.com/sgibson91/bump-jhub-image-action/actions/workflows/ci.yaml/badge.svg)](https://github.com/sgibson91/bump-jhub-image-action/actions/workflows/ci.yaml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sgibson91/bump-jhub-image-action/main.svg)](https://results.pre-commit.ci/latest/github/sgibson91/bump-jhub-image-action/main) [![GitHub](https://img.shields.io/github/license/sgibson91/bump-jhub-image-action)](LICENSE) [![badge](https://img.shields.io/static/v1?label=Code%20of&message=Conduct&color=blueviolet)](CODE_OF_CONDUCT.md) [![badge](https://img.shields.io/static/v1?label=Contributing&message=Guidelines&color=blueviolet)](CONTRIBUTING.md)

This is a GitHub Action that will check the tags of Docker images providing the computational environments for a JupyterHub are up-to-date with their sources on Docker Hub.
If more recent image tags are available, the bot will open a Pull Request to the host repository inserting the new image tags into the JupyterHub configuration file.

**Table of Contents:**

- [:mag: Overview](#mag-overview)
- [🤔 Assumptions `bump-jhub-image-action` Makes](#-assumptions-bump-jhub-image-action-makes)
- [:inbox_tray: Inputs](#inbox_tray-inputs)
- [:lock: Permissions](#lock-permissions)
- [:recycle: Example Usage](#recycle-example-usage)
- [:sparkles: Contributing](#sparkles-contributing)

---

## :mag: Overview

This is an overview of the steps the Action executes.

- The Action will read a JupyterHub config file from the host repository and look for the tags of the Docker images describing the computational environments.
  The Action currently recognises images under the `singleuser` and `singleuser.profileList` keys.
- The Action will then check the most recent image tags pushed to [Docker Hub](https://hub.docker.com) for these images.
  (Other container registries may be supported in the future.)
- If there are more recent image tags available, the Action will open a Pull Request to the host repository with the updated image tags added into the JupyterHub configuration file

A moderator should review the Pull Request before merging it and/or deploying to the JupyterHub.

## 🤔 Assumptions `bump-jhub-image-action` Makes

Here is a list detailing the assumptions that the Action makes.

1. You have a GitHub token with enough permissions to access the GitHub API and create branches, commits and Pull Requests
2. The JupyterHub configuration file is available in a **public** GitHub repository, or you have a token with sufficient permissions to read/write to a **private** repository
3. The Docker images are publicly available on Docker Hub.
   (Other container registries may be supported in the future.)

## :inbox_tray: Inputs

| Variable | Description | Required? | Default value |
| :--- | :--- | :--- | :--- |
| `config_path` | Path to the JupyterHub configuration file, relative to the repository root. | :white_check_mark: | - |
| `github_token` | A GitHub token to make requests to the API with. Requires write permissions to: create new branches, make commits, and open Pull Requests. | :x: | `${{github.token}}` |
| `repository` | A GitHub repository containing the config for a JupyterHub deployment. | :x: | `${{github.repository}}` |
| `base_branch` | The name of the base branch Pull Requests will be merged into. | :x: | `main` |
| `head_branch` | The name of the branch changes will be pushed to and the Pull Request will be opened from. | :x: | `bump_image_tags-WXYZ` where `WXYZ` will be a randomly generated ascii string (to avoid clashes) |
| `labels` | A comma-separated list of labels to apply to the opened Pull Request. Labels must already exist in the repository. | :x: | `[]` |
| `reviewers` | A comma-separated list of GitHub users (without the leading `@`) to request reviews from. | :x: | `[]` |
| `dry_run` | Perform a dry-run of the action. A Pull Request will not be opened, but a log message will indicate if any image tags can be bumped. | :x: | `False` |

## :lock: Permissions

This Action will need permission to read the contents of a file stored in your repository, create a new branch, commit to a branch, and open a Pull Request.
The [default permissive settings of `GITHUB_TOKEN`](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token) should provide the relevant permissions.

If instead your repository is using the default restricted settings of `GITHUB_TOKEN`, you could grant just enough permissions to the Action using a [`permissions`](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions#jobsjob_idpermissions) config, such as the one below:

```yaml
permissions:
  contents: write
  pull-requests: write
```

## :recycle: Example Usage

The simplest way to use this Action is documented below.
This config features a `workflow_dispatch` trigger to allow manual running whenever the maintainers desire, and a cron job trigger scheduled to run at 10am every weekday.

```yaml
name: Check and Bump image tags in a JupyterHub config

on:
  workflow_dispatch:
  schedule:
    - cron: "0 10 * * 1-5"

jobs:
  bump-image-tags:
    runs-on: ubuntu-latest
    steps:
    - uses: sgibson91/bump-jhub-image-action@main
      with:
        config_path: path/to/config.yaml
```

## :sparkles: Contributing

Thank you for wanting to contribute to the project! :tada:
Please read our [Code of Conduct](CODE_OF_CONDUCT.md) :purple_heart: and [Contributing Guidelines](CONTRIBUTING.md) :space_invader: to get you started.
