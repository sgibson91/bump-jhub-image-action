import os
import sys
import argparse

from loguru import logger

from .main import run

logger.add(level="DEBUG")

DESCRIPTION = "Update the Docker image tags governing the computational environments available on a JupyterHub"
parser = argparse.ArgumentParser(description=DESCRIPTION)

parser.add_argument("repo_owner", type=str, help="The GitHub repository owner")
parser.add_argument("repo_name", type=str, help="The JupyterHub deployment repo name")
parser.add_argument(
    "config_path",
    type=str,
    help="Path to the JupyterHub config file relative to the repo root",
)
parser.add_argument(
    "-b",
    "--base-branch",
    type=str,
    default="main",
    help="The name of the default branch of the repo, or the branch where PRs should be merged into. Default: main.",
)
parser.add_argument(
    "-t",
    "--head-branch",
    type=str,
    default="bump_image_tags",
    help="The name of the branch to push changes to and open PRs from. Default: bump_image_tags.",
)
parser.add_argument(
    "-l",
    "--labels",
    nargs="+",
    default=[],
    help="List of labels to assign to the Pull Request. Must already exist in the repository.",
)
parser.add_argument(
    "-r",
    "--reviewers",
    nargs="+",
    default=[],
    help="List of GitHub handles to request reviews for the Pull Request from. No leading `@` symbol.",
)
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Perform a dry-run. Pull Request will not be opened.",
)


def main():
    args = parser.parse_args(sys.argv[1:])

    # Get token from env
    token = os.environ["GITHUB_TOKEN"] if "GITHUB_TOKEN" in os.environ else None
    if token is None:
        raise ValueError(
            "You must provide a value for the environment variable GITHUB_TOKEN"
        )

    run(
        args.repo_owner,
        args.repo_name,
        args.config_path,
        args.base_branch,
        args.head_branch,
        args.labels,
        args.reviewers,
        token,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
