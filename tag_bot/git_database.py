from requests import put
from loguru import logger

from .utils import get_request, post_request


def create_commit(
    api_url: str,
    header: dict,
    path: str,
    branch: str,
    sha: str,
    commit_msg: str,
    content: str,
) -> None:
    """Create a commit over the GitHub API by creating or updating a file

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        path (str): The path to the file that is to be created or updated,
            relative to the repo root
        branch (str): The branch the commit should be made on
        sha (str): The SHA of the blob to be updated.
        commit_msg (str): A message describing the changes the commit applies
        content (str): The content of the file to be updated, encoded in base64
    """
    logger.info("Committing changes to file: {}", path)
    url = "/".join([api_url, "contents", path])
    body = {"message": commit_msg, "content": content, "sha": sha, "branch": branch}
    put(url, json=body, headers=header)


def create_ref(api_url: str, header: dict, ref: str, sha: str) -> None:
    """Create a new git reference (specifically, a branch) with GitHub's git database API
    endpoint

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        ref (str): The reference or branch name to create
        sha (str): The SHA of the parent commit to point the new reference to
    """
    logger.info("Creating new branch: {}", ref)
    url = "/".join([api_url, "git", "refs"])
    body = {
        "ref": f"refs/heads/{ref}",
        "sha": sha,
    }
    post_request(url, headers=header, json=body)


def get_contents(api_url: str, header: dict, path: str, ref: str) -> dict:
    """Get the contents of a file in a GitHub repo over the API

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            include an authorisation token.
        path (str): The path to the file that is to be created or updated,
            relative to the repo root
        ref (str): The reference (branch) the file is stored on

    Returns:
        dict: The JSON payload response of the request
    """
    logger.info("Downloading JupyterHub config from url: {}", api_url)
    url = "/".join([api_url, "contents", path])
    query = {"ref": ref}
    return get_request(url, headers=header, params=query, output="json")


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
    logger.info("Pulling info for ref: {}", ref)
    url = "/".join([api_url, "git", "ref", "heads", ref])
    return get_request(url, headers=header, output="json")
