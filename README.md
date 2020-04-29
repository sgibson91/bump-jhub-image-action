# UpdateDockerTags

[![GitHub](https://img.shields.io/github/license/HelmUpgradeBot/UpdateDockerTags)](LICENSE) [![badge](https://img.shields.io/static/v1?label=Code%20of&message=Conduct&color=blueviolet)](CODE_OF_CONDUCT.md) [![badge](https://img.shields.io/static/v1?label=Contributing&message=Guidelines&color=blueviolet)](CONTRIBUTING.md) [![good first issue](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/good%20first%20issue)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/good%20first%20issue) [![help wanted](https://img.shields.io/github/labels/HelmUpgradeBot/UpdateDockerTags/help%20wanted)](https://github.com/HelmUpgradeBot/UpdateDockerTags/labels/help%20wanted)

An automatable bot that will update Docker image tags in a JupyterHub configuration file.

**Table of Contents:**

- [:mag: Overview](#mag-overview)
- [🤔 Assumptions UpdateDockerTags Makes](#-assumptions-helmupgradebot-makes)
- [:pushpin: Requirements](#pushpin-installation-and-requirements)
  - [:cloud: Install Azure CLI](#cloud-install-azure-cli)
- [:children_crossing: Usage](#children_crossing-usage)
  - [:lock: Permissions](#lock-permissions)
  - [:clock2: CRON Expression](#clock2-cron-expression)
- [:leftwards_arrow_with_hook: Pre-commit Hook](#leftwards_arrow_with_hook-pre-commit-hook)
- [:sparkles: Contributing](#sparkles-contributing)

---

## :mag: Overview

This is an overview of the steps the bot executes.

- If a GitHub [Personal Access Token](https://github.blog/2013-05-16-personal-api-tokens/) (PAT) has not been parsed on the command line, it will login to Azure and pull a PAT from an [Azure Key Vault](https://docs.microsoft.com/en-gb/azure/key-vault/)
- The bot will read a JupyterHub config file from the [`bridge-data-platform` repository](https://github.com/alan-turing-instute/bridge-data-platform) and look for the tags of the Docker images describing the computational environments (`minimal-notebook`, `datascience-notebook` and `turinginst/bridge-data-env`)
- The bot will then check the most recent image tags pushed to [Docker Hub](https://hub.docker.com) for these images
- If there are more recent image tags available, the bot will open a Pull Request to the `bridge-data-platform` repository with the updated image tags

A moderator should review the Pull Request before merging it.

## 🤔 Assumptions UpdateDockerTags Makes

Here is a list detailing the assumptions that the bot makes.

## :pushpin: Installation and Requirements

To install the bot, you will need to clone this repository and install the package.
It requires Python version >=3.7.

```bash
git clone https://github.com/HelmUpgradeBot/UpdateDockerTags.git
cd UpdateDockerTags
python setup.py install
```

You will also need to install the [Microsoft Azure command line interface](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

### :cloud: Install the Azure CLI

To install the Azure command line interface, run the following:

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

## :children_crossing: Usage

To run the bot, execute the following:

```bash

```

where:

### :lock: Permissions

The user (or machine) running this script will need _at least_ permission to get secrets from the Azure Key Vault (`Get` and `List`).

### :clock2: CRON expression

To run this script at 10am daily, use the following cron expression:

```bash
0 10 * * * cd /path/to/UpdateDockerTags && /path/to/python setup.py install && /path/to/UpdateDockerTags [--flags]
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
