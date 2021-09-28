import os

from typing import List

from .app import run

API_ROOT = "https://api.github.com"


def split_str_to_list(input_str: str) -> List[str]:
    # Remove all whitespace
    input_str = input_str.replace(" ", "")
    # Return a list split from a string using `,` char
    return input_str.split(",")


def main():
    # Retrieve environment variables
    config_path = (
        os.environ["INPUT_CONFIG_PATH"] if "INPUT_CONFIG_PATH" in os.environ else None
    )
    github_token = (
        os.environ["INPUT_GITHUB_TOKEN"] if "INPUT_GITHUB_TOKEN" in os.environ else None
    )
    repository = (
        os.environ["INPUT_REPOSITORY"] if "INPUT_REPOSITORY" in os.environ else None
    )
    base_branch = (
        os.environ["INPUT_BASE_BRANCH"] if "INPUT_BASE_BRANCH" in os.environ else None
    )
    head_branch = (
        os.environ["INPUT_HEAD_BRANCH"] if "INPUT_HEAD_BRANCH" in os.environ else None
    )
    labels = os.environ["INPUT_LABELS"] if "INPUT_LABELS" in os.environ else []
    reviewers = os.environ["INPUT_REVIEWERS"] if "INPUT_REVIEWERS" in os.environ else []
    dry_run = os.environ["INPUT_DRY_RUN"] if "INPUT_DRY_RUN" in os.environ else False

    # Reference dict for required inputs
    required_vars = {
        "CONFIG_PATH": config_path,
        "GITHUB_TOKEN": github_token,
        "REPOSITORY": repository,
        "BASE_BRANCH": base_branch,
        "HEAD_BRANCH": head_branch,
    }

    # Check all the required inputs are properly set
    for k, v in required_vars.items():
        if v is None:
            raise ValueError(f"{k} must be set!")

    # If labels/reviewers have been provided, transform from string into a list
    if len(labels) > 0:
        labels = split_str_to_list(labels)
    if len(reviewers) > 0:
        reviewers = split_str_to_list(reviewers)

    # Check the dry_run variable is properly set
    if isinstance(dry_run, str) and (dry_run == "true"):
        dry_run = True
    elif isinstance(dry_run, bool) and not dry_run:
        pass
    else:
        raise ValueError("DRY_RUN variable can only take values 'true' or 'false'")

    # Set API_URLs
    repo_api = "/".join([API_ROOT, "repos", repository])

    # Create header for API requests
    header = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}",
    }

    run(
        repo_api,
        header,
        config_path,
        base_branch,
        head_branch,
        labels=labels,
        reviewers=reviewers,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    main()
