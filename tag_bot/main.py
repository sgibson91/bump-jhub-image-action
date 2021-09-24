import yaml
import random
import string

from itertools import compress

from .utils import get_request
from .parse_image_tags import get_image_tags

from .github_api import (
    check_fork_exists,
    create_pr,
    find_existing_pr,
    make_fork,
    remove_fork,
)

from .git_database import (
    create_blob,
    create_commit,
    create_ref,
    create_tree,
    get_ref,
    update_ref,
)

API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"


def edit_config(
    download_url: str,
    header: dict,
    images_to_update: list,
    image_tags: dict,
    config_type: str,
) -> dict:
    """Update the JupyterHub config file with the new image tags

    Args:
        download_url (str): The URL where the config can be downloaded from
        header (dict): A dictionary of headers to with any requests. Must
            contain an authorisation token.
        images_to_update (list): A list of docker image names that can be updated
        image_tags (dict): A dictionary of docker images used by the JupyterHub,
            the tags that are currently deployed, and the most recent tags on
            the container registry.
        config_type (str): Whether the JupyterHub uses a singleuser image or
            has a profile list of multiple images. Accepted values are
            'singluser' or 'profileList' (case sensitive).

    Returns:
        dict: The updated JupyterHub config in YAML format
    """
    allowed_config_types = ["singleuser", "profileList"]
    if config_type not in allowed_config_types:
        raise NotImplementedError(
            "The config type you are trying to use is not supported. Currently accepted config types are: %s"
            % allowed_config_types
        )

    resp = get_request(download_url, headers=header, output="text")
    file_contents = yaml.safe_load(resp)

    if file_contents["singleuser"]["image"]["name"] in images_to_update:
        file_contents["singleuser"]["image"]["tag"] = image_tags[
            file_contents["singleuser"]["image"]["name"]
        ]["latest"]

    if config_type == "profileList":
        for i, image in enumerate(file_contents["singleuser"]["profileList"]):
            if ("kubespawner_override" in image.keys()) and (
                image["kubespawner_override"]["image"].split(":")[0] in images_to_update
            ):
                image_name = image["kubespawner_override"]["image"].split(":")[0]
                file_contents["singleuser"]["profileList"][i]["kubespawner_override"][
                    "image"
                ] = ":".join([image_name, image_tags[image_name]["latest"]])

    return file_contents


def update_image_tags(
    repo_owner: str,
    repo_name: str,
    base_branch: str,
    head_branch: str,
    filepath: str,
    images_to_update: list,
    image_tags: dict,
    header: dict,
    pr_exists: bool,
    config_type: str,
) -> None:
    """Function to update the Docker image tags in a JupyterHub config file.
    Makes a series of calls to the GitHub API to create a branch and commit the
    updated file to it.

    Args:
        repo_owner (str): The owner of the GitHub repo where the config is stored
        repo_name (str): The name of the GitHub repo where the config is stored
        base_branch (str): The default branch of the repo or the branch PRs
            should be merged into.
        head_branch (str): The name of a branch PRs should be opened from
        filepath (str): Path to the JupyterHub config file relative to the
            repo root
        images_to_update (list): A list of docker images that need updating
        image_tags (dict): A dictionary of all docker images in use by the
            JupyterHub, their currently deployed tags, and the most recent tags
            available on the container registry
        header (dict): A dictionary of headers to send with API requests. Must
            contain an authorisation token.
        pr_exists (bool): Whether or not the bot has previously opened a PR
            which has not yet been merged
        config_type (str): Whether the JupyterHub uses a singleuser image or
            has a profile list of multiple images. Accepted values are
            'singluser' or 'profileList' (case sensitive).
    """
    allowed_config_types = ["singleuser", "profileList"]
    if config_type not in allowed_config_types:
        raise NotImplementedError(
            "The config type you are trying to use is not supported. Currently accepted config types are: %s"
            % allowed_config_types
        )

    # Set API URLs for requests
    repo_api = "/".join([API_ROOT, "repos", repo_owner, repo_name])
    fork_api = "/".join([API_ROOT, "repos", "HelmUpgradeBot", repo_name])

    if pr_exists:
        # Return commit SHA and URL
        resp = get_ref(fork_api, header, f"heads/{head_branch}")
        target_commit_sha = resp["object"]["sha"]
        target_commit_url = resp["object"]["url"]
    else:
        # Get a reference to HEAD of base_branch
        resp = get_ref(repo_api, header, f"heads/{base_branch}")

        # Create head_branch, and return reference SHA and URL
        resp = create_ref(fork_api, header, head_branch, resp["object"]["sha"])
        target_commit_sha = resp["object"]["sha"]
        target_commit_url = resp["object"]["url"]

    # Get the commit that the HEAD of the reference points to and extract
    # the tree's SHA
    resp = get_request(target_commit_url, headers=header, output="json")
    tree_sha = resp["tree"]["sha"]

    # Download the file
    if pr_exists:
        file_contents_url = "/".join(
            [RAW_ROOT, "HelmUpgradeBot", repo_name, head_branch, filepath]
        )
    else:
        file_contents_url = "/".join(
            [RAW_ROOT, repo_owner, repo_name, base_branch, filepath]
        )

    file_contents = edit_config(
        file_contents_url, header, images_to_update, image_tags, config_type
    )

    # Create a blob and return it's SHA
    resp = create_blob(fork_api, header, yaml.safe_dump(file_contents))
    blob_sha = resp["sha"]

    # Create a tree containing the modified file contents and return it's SHA
    resp = create_tree(fork_api, header, filepath, tree_sha, blob_sha)
    new_tree_sha = resp["sha"]

    # Create a commit and return it's SHA
    commit_msg = f"Bump images {[image for image in images_to_update]} to tags {[image_tags[image]['latest'] for image in images_to_update]}, respectively"
    resp = create_commit(fork_api, header, new_tree_sha, target_commit_sha, commit_msg)
    commit_sha = resp["sha"]

    # Update the reference
    update_ref(fork_api, header, head_branch, commit_sha)


def compare_image_tags(image_tags: dict) -> list:
    """Compare the currently deployed image tags to those most recently
    available on the container registry and ascertain if an image can be updated

    Args:
        image_tags (dict): A dictionary of all docker images in use by the
            JupyterHub, their currently deployed tags, and the most recent tags
            available on the container registry

    Returns:
        images_to_update (list): A list of docker images that need updating
    """
    cond = [
        image_tags[image_name]["current"] != image_tags[image_name]["latest"]
        for image_name in image_tags.keys()
    ]
    return list(compress(image_tags.keys(), cond))


def run(
    repo_owner: str,
    repo_name: str,
    config_file: str,
    config_type: str,
    base_branch: str,
    head_branch: str,
    token: str,
    dry_run: bool = False,
) -> None:
    """Run the bot to check if the docker images are up to date

    Args:
        repo_owner (str): The owner of the GitHub repo where the config is stored
        repo_name (str): The name of the GitHub repo where the config is stored
        config_file (str): Path to the JupyterHub config file relative to the
            repo root
        config_type (str): Whether the JupyterHub uses a singleuser image or
            has a profile list of multiple images. Accepted values are
            'singluser' or 'profileList' (case sensitive).
        base_branch (str): The default branch of the repo or the branch PRs
            should be merged into.
        head_branch (str): The name of a branch PRs should be opened from
        token (str): A GitHub Personal Access Token to authenticate against
            the API with
        dry_run (bool, optional): When True, perform a dry run and do not open a
            Pull Request. Defaults to False.
    """
    REPO_API = "/".join([API_ROOT, "repos", repo_owner, repo_name])
    HEADER = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Check if Pull Request exists
    pr_exists, branch_name = find_existing_pr(REPO_API, HEADER)

    # Check if a fork exists
    fork_exists = check_fork_exists(repo_name, HEADER)

    # Get and compare image tags
    if branch_name is None:
        image_tags = get_image_tags(
            repo_owner, repo_name, base_branch, config_file, HEADER
        )
    else:
        image_tags = get_image_tags(
            repo_owner, repo_name, branch_name, config_file, HEADER
        )

    images_to_update = compare_image_tags(image_tags)

    if (len(images_to_update) > 0) and (not dry_run):
        if branch_name is None:
            random_id = "".join(random.sample(string.ascii_letters, 4))
            head_branch = "-".join([head_branch, random_id])
        else:
            head_branch = branch_name

        if (not fork_exists) and (not pr_exists):
            _ = make_fork(REPO_API, HEADER)

        update_image_tags(
            REPO_API,
            repo_name,
            head_branch,
            config_file,
            images_to_update,
            image_tags,
            HEADER,
            pr_exists,
        )

        if not pr_exists:
            create_pr(REPO_API, HEADER, base_branch, head_branch)

    elif (len(images_to_update) == 0) and (not dry_run):
        if pr_exists:
            # A PR exists so exit cleanly
            import sys

            sys.exit()

        if fork_exists and (not pr_exists):
            pass
            # A fork exists but there's no PR open, so remove the fork
            _ = remove_fork(repo_name, HEADER)
