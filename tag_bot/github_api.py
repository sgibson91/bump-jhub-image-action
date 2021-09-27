import time
import jmespath

from .utils import delete_request, get_request, post_request

API_ROOT = "https://api.github.com"


def add_labels(labels: list, pr_url: str, header: dict) -> None:
    """Assign labels to an open Pull Request. The labels must already exist in
    the repository.

    Args:
        labels (list): The list of labels to apply
        pr_url (str): The API URL of the Pull Request (issues endpoint) to
            send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain an authorisation token.
    """
    post_request(pr_url, headers=header, json={"labels": labels})


def assign_reviewers(reviewers: list, pr_url: str, header: dict) -> None:
    """Request reviews from GitHub users on a Pull Request

    Args:
        reviewers (list): A list of GitHub user to request reviews from
            (**excluding** the leading `@` symbol)
        pr_url (str): The API URL of the Pull Request (pulls endpoint) to send
            the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain an authorisation token.
    """
    url = "/".join([pr_url, "requested_reviewers"])
    post_request(url, headers=header, json={"reviewers": reviewers})


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


def create_pr(
    api_url: str,
    header: dict,
    base_branch: str,
    head_branch: str,
    labels: list,
    reviewers: list,
) -> None:
    """Create a Pull Request via the GitHub API

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        base_branch (str): The name of the branch to open the PR against
        head_branch (str): The name of the PR to open the PR from
        labels (list): A list of labels to apply to the Pull Request
        reviewers (list): A list of GitHub users to request reviews from
    """
    url = "/".join([api_url, "pulls"])
    pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": base_branch,
        "head": f"HelmUpgradeBot:{head_branch}",
    }
    resp = post_request(url, headers=header, json=pr, return_json=True)

    if len(labels) > 0:
        add_labels(labels, resp["issue_url"], header)

    if len(reviewers) > 0:
        assign_reviewers(reviewers, resp["url"], header)


def find_existing_pr(api_url: str, header: dict) -> [bool, str]:
    """Check if the bot already has an open Pull Request

    Args:
        api_url (str): The API URL of the GitHub repository to send requests to
        header (dict): A dictionary of headers to send with the GET request

    Returns:
        pr_exists (bool): True if HelmUpgradeBot already has an open PR. False otherwise.
        head_branch (str): The name of the branch to send commits to
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
