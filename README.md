# UpdateDockerTags

[![GitHub](https://img.shields.io/github/license/HelmUpgradeBot/UpdateDockerTags)](LICENSE) [![badge](https://img.shields.io/static/v1?label=Code%20of&message=Conduct&color=blueviolet)](CODE_OF_CONDUCT.md) [![badge](https://img.shields.io/static/v1?label=Contributing&message=Guidelines&color=blueviolet)](CONTRIBUTING.md) [![good first issue](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/good%20first%20issue)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/good%20first%20issue) [![help wanted](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/help%20wanted)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/help%20wanted)

This is an automatable bot that will check the tags of Docker images providing the computational environments for a JupyterHub are up-to-date with their sources on Docker Hub.
If more recent image tags are available, the bot will open a Pull Request to the host repository inserting the new image tags into the JupyterHub configuration file.

**Table of Contents:**

- [:mag: Overview](#mag-overview)
- [🤔 Assumptions UpdateDockerTags Makes](#-assumptions-helmupgradebot-makes)
- [:pushpin: Requirements](#pushpin-installation-and-requirements)
- [:children_crossing: Usage](#children_crossing-usage)
- [:sparkles: Contributing](#sparkles-contributing)

---

## :mag: Overview

This is an overview of the steps the bot executes.

- It requires a GitHub [Personal Access Token](https://github.blog/2013-05-16-personal-api-tokens/) (PAT) to be parsed on the command line
- The bot will read a JupyterHub config file from the host repository and look for the tags of the Docker images describing the computational environments
- The bot will then check the most recent image tags pushed to [Docker Hub](https://hub.docker.com) for these images
- If there are more recent image tags available, the bot will open a Pull Request to the host repository with the updated image tags

A moderator should review the Pull Request before merging it.

## 🤔 Assumptions UpdateDockerTags Makes

Here is a list detailing the assumptions that the bot makes.

1. The bot has access to a GitHub PAT to authenticate to the API
2. The JupyterHub configuration file is available in a **public** GitHub repository
3. The Docker images are publicly available on Docker Hub

## :pushpin: Installation and Requirements

To install the bot, you will need to clone this repository and install the package.
It requires Python version >=3.7.

```bash
git clone https://github.com/HelmUpgradeBot/UpdateDockerTags.git
cd UpdateDockerTags
python setup.py install
```

## :children_crossing: Usage

When running the bot you can **either** provide the GitHub PAT on the command line as an environment variable, like so:

```bash
GITHUB_TOKEN="TOKEN" tag-bot [-h] [-c {singleuser,profileList}] [-b BASE_BRANCH] [-t HEAD_BRANCH] [--dry-run] repo_owner repo_name config_path

Update the Docker image tags governing the computational environments available on a JupyterHub

positional arguments:
  repo_owner            The GitHub repository owner
  repo_name             The JupyterHub deployment repo name
  config_path           Path to the JupyterHub config file relative to the repo root

optional arguments:
  -h, --help            show this help message and exit
  -c {singleuser,profileList}, --config-type {singleuser,profileList}
                        Whether the JupyterHub uses a singleuser image or has a profile list of multiple images.
  -b BASE_BRANCH, --base-branch BASE_BRANCH
                        The name of the default branch of the repo, or the branch where PRs should be merged into. Default: main.
  -t HEAD_BRANCH, --head-branch HEAD_BRANCH
                        The name of the branch to push changes to and open PRs from. Default: bump_image_tags.
  --dry-run             Perform a dry-run. Pull Request will not be opened.
```

where `TOKEN` is the raw token string.

## :sparkles: Contributing

Thank you for wanting to contribute to the project! :tada:
Please read our [Code of Conduct](CODE_OF_CONDUCT.md) :purple_heart: and [Contributing Guidelines](CONTRIBUTING.md) :space_invader: to get you started.
