from requests import put

from .utils import get_request, post_request


def create_commit(
    api_url: str, header: dict, tree_sha: str, commit_sha: str, commit_msg: str
) -> dict:
    """Create a new commit using GitHub's git database API endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        tree_sha (str): The SHA of the new tree containing the information to be
            captured in the commit.
        commit_sha (str): The SHA of the parent commit
        commit_msg (str): A message to provide with the commit

    Returns:
        dict: The JSON payload response of the request
    """
    url = "/".join([api_url, "git", "commits"])
    body = {
        "message": commit_msg,
        "tree": tree_sha,
        "parents": [commit_sha],
    }

    return post_request(url, header, json=body, return_json=True)


def create_ref(api_url: str, header: dict, ref: str, sha: str) -> dict:
    """Create a new git reference (specifically, a branch) with GitHub's git database API
    endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        ref (str): The reference or branch name to create
        sha (str): The SHA of the parent commit to point the new reference to

    Returns:
        dict: The JSON payload response of the request
    """
    url = "/".join([api_url, "git", "refs"])
    body = {
        "ref": f"heads/{ref}",
        "sha": sha,
    }

    return post_request(url, headers=header, json=body, return_json=True)


def create_tree(
    api_url: str, header: dict, filepath: str, tree_sha: str, blob_sha: str
) -> dict:
    """Create a new tree using GitHub's git database API endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        filepath (str): The path to the file to be included in the tree,
            relative to the project's root.
        tree_sha (str): The SHA of the parent tree
        blob_sha (str): The SHA of the blob to be included in the new tree

    Returns:
        dict: The JSON payload response of the request
    """
    url = "/".join([api_url, "git", "trees"])
    body = {
        "base_tree": tree_sha,
        "tree": [
            {
                "path": filepath,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            },
        ],
    }

    return post_request(url, headers=header, json=body, return_json=True)


def get_ref(api_url: str, header: dict, ref: str) -> dict:
    """Get a git reference (specifically, a HEAD ref) using GitHub's git
    database API endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        ref (str): The reference for which to return information for

    Returns:
        dict: The JSON payload response of the request
    """
    url = "/".join([api_url, "refs", ref])
    return get_request(url, headers=header, output="json")


def update_ref(api_url: str, header: dict, branch: str, commit_sha: str) -> None:
    """Update an existing reference (specifically, the HEAD reference of a
    branch) using GitHub's git database API endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): [A dictionary of headers to send with the request. Must
            include an authorisation token.
        branch (str): The branch reference to be updated
        commit_sha (str): The SHA of the commit that the HEAD of the branch
            should now point to
    """
    url = "/".join([api_url, "git", "refs", "heads", branch])
    body = {
        "sha": commit_sha,
        "force": True,
    }
    patch_request(url, headers=header, json=body)
