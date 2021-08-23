# UpdateDockerTags

[![GitHub](https://img.shields.io/github/license/HelmUpgradeBot/UpdateDockerTags)](LICENSE) [![badge](https://img.shields.io/static/v1?label=Code%20of&message=Conduct&color=blueviolet)](CODE_OF_CONDUCT.md) [![badge](https://img.shields.io/static/v1?label=Contributing&message=Guidelines&color=blueviolet)](CONTRIBUTING.md) [![good first issue](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/good%20first%20issue)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/good%20first%20issue) [![help wanted](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/help%20wanted)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/help%20wanted)

This is an automatable bot that will check the tags of Docker images providing the computational environments for a JupyterHub are up-to-date with their sources on Docker Hub.
If more recent image tags are available, the bot will open a Pull Request to the [`alan-turing-institute/bridge-data-platform` repository](https://github.com/alan-turing-institute/bridge-data-platform) inserting the new image tags into the JupyterHub configuration file.

**Table of Contents:**

- [:mag: Overview](#mag-overview)
- [🤔 Assumptions UpdateDockerTags Makes](#-assumptions-helmupgradebot-makes)
- [:pushpin: Requirements](#pushpin-installation-and-requirements)
- [:children_crossing: Usage](#children_crossing-usage)
  - [:clock2: CRON Expression](#clock2-cron-expression)
- [:leftwards_arrow_with_hook: Pre-commit Hook](#leftwards_arrow_with_hook-pre-commit-hook)
- [:sparkles: Contributing](#sparkles-contributing)

---

## :mag: Overview

This is an overview of the steps the bot executes.

- It requires a GitHub [Personal Access Token](https://github.blog/2013-05-16-personal-api-tokens/) (PAT) to be parsed on the command line
- The bot will read a JupyterHub config file from the [`bridge-data-platform` repository](https://github.com/alan-turing-instute/bridge-data-platform) and look for the tags of the Docker images describing the computational environments (`minimal-notebook`, `datascience-notebook` and `turinginst/bridge-data-env`)
- The bot will then check the most recent image tags pushed to [Docker Hub](https://hub.docker.com) for these images
- If there are more recent image tags available, the bot will open a Pull Request to the `bridge-data-platform` repository with the updated image tags

A moderator should review the Pull Request before merging it.

## 🤔 Assumptions UpdateDockerTags Makes

Here is a list detailing the assumptions that the bot makes.

1. The bot has access to a GitHub PAT to authenticate to the API.
2. The JupyterHub configuration file is available in a **public** GitHub repository under `config/config-template.yaml`
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
API_TOKEN="GITHUB_PAT" UpdateDockerTags REPO_OWNER REPO_NAME \
    --branch BRANCH_NAME \
    --dry-run
```

where `GITHUB_PAT` is the raw token string.

where:

- `REPO_OWNER` is the owner of the deployment repository;
- `REPO_NAME` is the name of the deployment repository;
- `BRANCH_NAME` os the git branch to commit changes to; and
- `-dry-run` performs a dry-run of the check and does not open a Pull Request.

### :clock2: CRON expression

To run this script at midnight nightly, use the following cron expression:

```bash
0 0 * * * cd /path/to/UpdateDockerTags && /path/to/python setup.py install && /path/to/UpdateDockerTags [--flags]
```

## :leftwards_arrow_with_hook: Pre-commit Hook

For developing this bot, there is a pre-commit hook that will format the Python code using [black](https://github.com/psf/black) and [flake8](http://flake8.pycqa.org/en/latest/).
To install the hook, run the following:

```bash
pip install -r dev-requirements.txt
pre-commit install
```

## :sparkles: Contributing

Thank you for wanting to contribute to the project! :tada:
Please read our [Code of Conduct](CODE_OF_CONDUCT.md) :purple_heart: and [Contributing Guidelines](CONTRIBUTING.md) :space_invader: to get you started.
