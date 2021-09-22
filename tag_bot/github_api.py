import time
import jmespath

from .utils import delete_request, get_request, post_request

API_ROOT = "https://api.github.com"


def check_fork_exists(repo_name: str, header: dict = {}) -> bool:
    """Check if a fork of a GitHub repo already exists

    Args:
        repo_name (str): The name of the repo to check for
        header (dict, optional): A dictionary of headers to send with the
            request. Defaults to {}

    Returns:
        bool: True if a fork exists. False if not.
    """
    url = "/".join([API_ROOT, "users", "HelmUpgradeBot", "repos"])
    resp = get_request(url, headers=header, output="json")
    return bool([x for x in resp if x["name"] == repo_name])


def create_pr(api_url: str, header: dict, base_branch: str, target_branch: str):
    """Create a Pull Request via the GitHub API

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        base_branch (str): The name of the branch to open the PR against
        target_branch (str): The name of the PR to open the PR from
    """
    url = "/".join([api_url, "pulls"])
    pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": base_branch,
        "head": target_branch,
    }
    post_request(url, headers=header, json=pr)


def find_existing_pr(api_url: str, header: dict) -> [bool, str]:
    """Check if the bot already has an open Pull Request

    Args:
        api_url (str): The API URL of the GitHub repository to send requests to
        header (dict): A dictionary of headers to send with the GET request

    Returns:
        pr_exists (bool): True if HelmUpgradeBot already has an open PR. False otherwise.
        target_branch (str): The name of the branch to send commits to
    """
    url = "/".join([api_url, "pulls"])
    params = {"state": "open", "sort": "created", "direction": "desc"}
    resp = get_request(url, headers=header, params=params, output="json")

    # Expression to match the head ref
    head_label_exp = jmespath.compile("[*].head.label")
    matching_labels = head_label_exp.search(resp)

    # Create list of labels of matching PRs
    matching_prs = [label for label in matching_labels if "HelmUpgradeBot" in label]

    if len(matching_prs) >= 1:
        print(
            "More than one Pull Request by HelmUpgradeBot open. Will push new commits to the most recent PR."
        )

        ref = matching_prs[0].split(":")[-1]

        return True, ref

    elif len(matching_prs) == 1:
        print(
            "One Pull Request by HelmUpgradeBot open. Will push new commits to that PR."
        )

        ref = matching_prs[0].split(":")[-1]

        return True, ref

    else:
        print("No Pull Requests by HelmUpgradeBot found. A new PR will be opened.")
        return False, None


def make_fork(api_url: str, header: dict) -> bool:
    """Create a fork of a repository

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.

    Returns:
        bool: True once the fork has been created
    """
    url = "/".join([api_url, "forks"])
    post_request(url, headers=header)
    time.sleep(5)
    return True


def remove_fork(repo_name: str, header: dict) -> bool:
    """Delete a fork of a repository

    Args:
        repo_name (str): The name of the forked repo to delete
        header (dict): A dictionary of headers to send with the request. Must
            contain an authorisation token.

    Returns:
        bool: False once the fork has been deleted
    """
    url = "/".join([API_ROOT, "repos", "HelmUpgradeBot", repo_name])
    delete_request(url, headers=header)
    time.sleep(5)
    return False
