# Bump Docker image tags in a JupyterHub config file

[![CI Tests](https://github.com/sgibson91/bump-jhub-image-action/actions/workflows/ci.yaml/badge.svg)](https://github.com/sgibson91/bump-jhub-image-action/actions/workflows/ci.yaml) [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sgibson91/bump-jhub-image-action/main.svg)](https://results.pre-commit.ci/latest/github/sgibson91/bump-jhub-image-action/main) [![codecov](https://codecov.io/gh/sgibson91/bump-jhub-image-action/branch/main/graph/badge.svg?token=01VEBJ62LA)](https://codecov.io/gh/sgibson91/bump-jhub-image-action) [![GitHub](https://img.shields.io/github/license/sgibson91/bump-jhub-image-action)](LICENSE) [![badge](https://img.shields.io/static/v1?label=Code%20of&message=Conduct&color=blueviolet)](CODE_OF_CONDUCT.md) [![badge](https://img.shields.io/static/v1?label=Contributing&message=Guidelines&color=blueviolet)](CONTRIBUTING.md)

This is a GitHub Action that will check the tags of Docker images referenced in a JupyterHub configuration file are up-to-date with their sources in a container registry.
If more recent image tags are available, the action will open a Pull Request to the host repository inserting the new image tags into the JupyterHub configuration file.

**Table of Contents:**

- [:mag: Overview](#mag-overview)
- [🤔 Assumptions `bump-jhub-image-action` Makes](#-assumptions-bump-jhub-image-action-makes)
- [:inbox_tray: Inputs](#inbox_tray-inputs)
- [:lock: Permissions](#lock-permissions)
  - [:wrench: Configuring `GITHUB_TOKEN`](#wrench-configuring-github_token)
- [:recycle: Example Usage](#recycle-example-usage)
  - [:wrench: Configuring the Action to push to a fork](#wrench-configuring-the-action-to-push-to-a-fork)
- [:sparkles: Contributing](#sparkles-contributing)

---

## :mag: Overview

This is an overview of the steps the Action executes.

- This Action consumes a list of [JMESPath expressions](https://jmespath.org/) that describes where Docker image are referenced in a JupyterHub configuration file.
- It will then will read the config file from the host repository and extract the names and tags of the images located at the provided paths.
- The Action will then check the most recent image tags pushed to a container registry (extracted from the image name) for these images.
- If there are more recent image tags available, the Action will open a Pull Request to the host repository with the updated image tags added into the JupyterHub configuration file

A moderator should review the Pull Request before merging it and/or deploying to the JupyterHub.

## 🤔 Assumptions `bump-jhub-image-action` Makes

Here is a list detailing the assumptions that the Action makes.

1. You have a GitHub token with enough permissions to access the GitHub API and create branches, commits and Pull Requests.
   The token stored in `${{ secrets.GITHUB_TOKEN }}` will be used by default.
2. The JupyterHub configuration file is available in a **public** GitHub repository, or you have a token with sufficient permissions to read/write to a **private** repository
3. The Docker images are publicly available on one of the following container registries (other container registries may be supported in the future):
   - [Docker Hub](https://hub.docker.com)
   - [quay.io](https://quay.io)

## :inbox_tray: Inputs

| Variable | Description | Required? | Default value |
| :--- | :--- | :---: | :--- |
| `config_path` | Path to the JupyterHub configuration file, relative to the repository root. | :white_check_mark: | - |
| `values_paths` | A _space-delimited_ list of valid [JMESPath expressions](https://jmespath.org/) identifying the location of images in the config to check for updates. An example is: `.singleuser.profileList[0].kubespawner_override.image`. If the image name and tag are in separate fields, you can provide the path to the parent key, e.g., `.singleuser.image` will know how to parse `.singleuser.image.name` and `.singleuser.image.tag`. | :white_check_mark: | - |
| `github_token` | A GitHub token to make requests to the API with. Requires write permissions to: create new branches, make commits, and open Pull Requests. | :x: | `${{github.token}}` |
| `repository` | A GitHub repository containing the config for a JupyterHub deployment. | :x: | `${{github.repository}}` |
| `base_branch` | The name of the base branch Pull Requests will be merged into. | :x: | `main` |
| `head_branch` | The name of the branch changes will be pushed to and the Pull Request will be opened from. | :x: | `bump-image-tags/{{ config path }}/WXYZ` where `WXYZ` will be a randomly generated ascii string (to avoid clashes) |
| `labels` | A comma-separated list of labels to apply to the opened Pull Request. Labels must already exist in the repository. | :x: | `[]` |
| `reviewers` | A comma-separated list of GitHub users (without the leading `@`) to request reviews from. | :x: | `[]` |
| `team_reviewers` | A comma-separated list of GitHub teams to request reviews from. | :x: | `[]` |
| `push_to_users_fork` | A GitHub account username (without the leading `@`) to fork the repository to and open a Pull Request from. If provided, then `github_token` must also be provided, and it should be a PAT owned by the account named here. | :x: | `None` |
| `dry_run` | Perform a dry-run of the action. A Pull Request will not be opened, but a log message will indicate if any image tags can be bumped. | :x: | `False` |

## :lock: Permissions

This Action will need permission to read the contents of a file stored in your repository, create a new branch, commit to a branch, and open a Pull Request.
The permission is granted by a token passed using the `github_token` input parameter.
You can choose to provide a specific token if you wish, otherwise the Action will default to using the inbuilt `GITHUB_TOKEN` in the GitHub Actions Runner.

### :wrench: Configuring `GITHUB_TOKEN`

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
        values_paths: .singleuser.image .singleuser.profileList[0].kubespawner_override.image
```

### :wrench: Configuring the Action to push to a fork

Some people prefer not to have tokens with write permissions acting upon the parent repository.
Using the token to fork a repository and open Pull Requests from the fork is considered a more secure option, since the token does not require write access to the parent repo (especially if it is public).

This Action can be configured to push to a fork by using the `push_to_users_fork` input and providing a valid GitHub account name (without the leading `@`).

:warning: Note that when using this feature, you must also provide a token to `github_token`, and this should be a Personal Access Token (PAT) that belongs to the account named in `push_to_users_fork` :warning:

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
        values_paths: .singleuser.image
        push_to_users_fork: octocat
        github_token: <PROVIDE A TOKEN OWNED BY OCTOCAT HERE>
```

## :sparkles: Contributing

Thank you for wanting to contribute to the project! :tada:
Please read our [Code of Conduct](CODE_OF_CONDUCT.md) :purple_heart: and [Contributing Guidelines](CONTRIBUTING.md) :space_invader: to get you started.
