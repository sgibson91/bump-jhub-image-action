import sys
import argparse
from .UpdateDockerTags import UpdateDockerTags

DESCRIPTION = "Update the Docker image tags governing the computational environments available on a JupyterHub"
parser = argparse.ArgumentParser(description=DESCRIPTION)

parser.add_argument("repo_owner", type=str, help="The GitHub repository owner")
parser.add_argument(
    "repo_name", type=str, help="The JupyterHub deployment repo name"
)

parser.add_argument(
    "--branch",
    type=str,
    default="bump-image-tags",
    help="The git branch to commit to",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Perform a dry-run. Pull Request will not be opened.",
)
parser.add_argument(
    "--identity",
    action="store_true",
    help="Login to Azure with a Managed System Identity",
)

parser.add_argument(
    "-t", "--token-name", default=None, help="Name of GitHub API token"
)
parser.add_argument(
    "-k",
    "--keyvault",
    default=None,
    help="Name of Azure Keyvault where GitHub API is stored",
)


def main():
    """Main function"""
    args = parser.parse_args(sys.argv[1:])

    cond1 = (args.token_name is None) and (args.keyvault is not None)
    cond2 = (args.token_name is not None) and (args.keyvault is None)

    if cond1 or cond2:
        raise Exception(
            "--token-name and --keyvault options must both be provided."
        )

    obj = UpdateDockerTags(vars(args))
    obj.check_image_tags()


if __name__ == "__main__":
    main()
