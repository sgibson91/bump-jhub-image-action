import jmespath

from .utils import get_request, post_request


def check_fork_exists(repo_name: str, header: str) -> bool:
    url = "/".join(["https://api.github.com", "users", "HelmUpgradeBot", "repos"])
    resp = get_request(url, headers=header, output="json")
    return bool([x for x in resp if x["name"] == repo_name])


def create_branch(repo_api: str, target_branch: str, sha: str, header: dict):
    url = "/".join([repo_api, "git", "refs"])
    body = {
        "ref": f"heads/{target_branch}",
        "sha": sha,
    }

    return post_request(url, headers=header, json=body, return_json=True)


def find_existing_pr(repo_api: str, header: dict) -> [bool, str]:
    """Check if the bot already has an open Pull Request

    Args:
        repo_api (str): The API URL of the GitHub repository to send requests to
        header (dict): A dictionary of headers to send with the GET request

    Returns:
        bool: True if HelmUpgradeBot already has an open PR. False otherwise.
        target_branch: The name of the branch to send commits to
    """
    print("Finding Pull Requests opened by HelmUpgradeBot")

    url = "/".join([repo_api, "pulls"])
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


def get_a_reference(repo_api: str, ref: str, header: dict) -> dict:
    url = "/".join([repo_api, "refs", ref])
    return get_request(url, headers=header, output="json")


def make_fork(repo_api: str, header: dict) -> bool:
    url = "/".join([repo_api, "forks"])
    post_request(url, headers=header)
    return True
