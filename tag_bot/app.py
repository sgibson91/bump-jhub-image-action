import base64
import random
import string
from itertools import compress

import yaml
from loguru import logger

from .git_database import create_commit, create_ref, get_contents, get_ref
from .github_api import create_pr, find_existing_pr
from .parse_image_tags import get_image_tags
from .http_requests import get_request


def edit_config(
    download_url: str,
    header: dict,
    images_to_update: list,
    image_tags: dict,
) -> str:
    """Update the JupyterHub config file with the new image tags

    Args:
        download_url (str): The URL where the config can be downloaded from
        header (dict): A dictionary of headers to with any requests. Must
            contain an authorisation token.
        images_to_update (list): A list of docker image names that can be updated
        image_tags (dict): A dictionary of docker images used by the JupyterHub,
            the tags that are currently deployed, and the most recent tags on
            the container registry.

    Returns:
        file_contents (str): The updated JupyterHub config in YAML format and encoded in base64
    """
    resp = get_request(download_url, headers=header, output="text")
    file_contents = yaml.safe_load(resp)

    if "singleuser" in file_contents.keys():
        logger.info("Updating JupyterHub config...")
        logger.info("Updating singleuser image tag...")

        if ("image" in file_contents["singleuser"].keys()) and (
            file_contents["singleuser"]["image"]["name"] in images_to_update
        ):
            file_contents["singleuser"]["image"]["tag"] = image_tags[
                file_contents["singleuser"]["image"]["name"]
            ]["latest"]

        if "profileList" in file_contents["singleuser"].keys():
            logger.info("Updating image tags for each profile...")

            for i, image in enumerate(file_contents["singleuser"]["profileList"]):
                if ("kubespawner_override" in image.keys()) and (
                    image["kubespawner_override"]["image"].split(":")[0]
                    in images_to_update
                ):
                    image_name = image["kubespawner_override"]["image"].split(":")[0]
                    file_contents["singleuser"]["profileList"][i][
                        "kubespawner_override"
                    ]["image"] = ":".join(
                        [image_name, image_tags[image_name]["latest"]]
                    )
    else:
        logger.info("Your config doesn't specify any images under `singleuser`!")

        import sys

        sys.exit(1)

    # Encode the file contents
    logger.info("Encoding config in base64...")
    encoded_file_contents = yaml.safe_dump(file_contents).encode("utf-8")
    base64_bytes = base64.b64encode(encoded_file_contents)
    file_contents = base64_bytes.decode("utf-8")

    return file_contents


def update_image_tags(
    api_url: str,
    header: dict,
    config_path: str,
    base_branch: str,
    head_branch: str,
    images_to_update: list,
    image_tags: dict,
    pr_exists: bool,
) -> None:
    """Function to update the Docker image tags in a JupyterHub config file.
    Makes a series of calls to the GitHub API to create a branch and commit the
    updated file to it.

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        config_path (str): The path to the JupyterHub config file relative to
            the repo root
        base_branch (str): The name of the branch to open the Pull Request
            against
        head_branch (str): The name of the branch to open the Pull Request from
        images_to_update (list): A list of docker images that need updating
        image_tags (dict): A dictionary of all docker images in use by the
            JupyterHub, their currently deployed tags, and the most recent tags
            available on the container registry
        pr_exists (bool): If a Pull Request already exists, commit to it's head
            branch instead of opening a new one
    """
    if not pr_exists:
        # Get a reference to HEAD of base_branch
        resp = get_ref(api_url, header, base_branch)

        # Create head_branch, and return reference SHA and URL
        create_ref(api_url, header, head_branch, resp["object"]["sha"])

        # Get the file download URL and blob_sha
        resp = get_contents(api_url, header, config_path, base_branch)
    else:
        # Get the file download URL and blob_sha
        resp = get_contents(api_url, header, config_path, head_branch)

    file_contents_url = resp["download_url"]
    blob_sha = resp["sha"]

    file_contents = edit_config(file_contents_url, header, images_to_update, image_tags)

    # Create a commit
    commit_msg = f"Bump images {[image for image in images_to_update]} to tags {[image_tags[image]['latest'] for image in images_to_update]}, respectively"
    create_commit(
        api_url, header, config_path, head_branch, blob_sha, commit_msg, file_contents
    )


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
    api_url: str,
    header: dict,
    config_path: str,
    base_branch: str,
    head_branch: str,
    labels: list = [],
    reviewers: list = [],
    dry_run: bool = False,
) -> None:
    """Run the action to check if the docker images are up to date

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        config_path (str): The path to the JupyterHub config file relative to
            the repo root
        base_branch (str): The name of the branch to open the Pull Request
            against
        head_branch (str): The name of the branch to open the Pull Request from
        labels (list, optional): A list of labels to apply to the Pull Request.
            They must already exist in the repository. Defaults to [].
        reviewers (list, optional): A list of GitHub users to request reviews
            from. Defaults to [].
        dry_run (bool, optional): Perform a dry-run where a Pull Request will
            not be opened. Defaults to False.
    """
    # Check if Pull Request exists
    pr_exists, branch_name = find_existing_pr(api_url, header)

    # Get and compare image tags
    if branch_name is None:
        image_tags = get_image_tags(
            api_url,
            header,
            base_branch,
            config_path,
        )
    else:
        image_tags = get_image_tags(
            api_url,
            header,
            branch_name,
            config_path,
        )

    images_to_update = compare_image_tags(image_tags)

    if (len(images_to_update) > 0) and (not dry_run):
        logger.info(
            "Newer tags are available for the following charts: {}", images_to_update
        )

        if branch_name is None:
            random_id = "".join(random.sample(string.ascii_letters, 4))
            head_branch = "-".join([head_branch, random_id])
        else:
            head_branch = branch_name

        update_image_tags(
            api_url,
            header,
            config_path,
            base_branch,
            head_branch,
            images_to_update,
            image_tags,
            pr_exists,
        )

        if not pr_exists:
            create_pr(api_url, header, base_branch, head_branch, labels, reviewers)

    elif (len(images_to_update) > 0) and dry_run:
        logger.info(
            "Newer tags are available for the following images: {}. Pull Request will not be opened due to --dry-run flag being set.",
            images_to_update,
        )

    else:
        logger.info("All image tags are up-to-date!")
