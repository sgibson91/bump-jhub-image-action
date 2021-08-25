import json
import random
import string

from itertools import compress

from .utils import get_request
from .parse_image_tags import get_image_tags

from .github import check_fork_exists, create_branch, find_existing_pr, get_a_reference, make_fork

API_ROOT = "https://api.github.com"


def update_image_tags(repo_api: str, repo_name: str, base_branch: str, target_branch: str, path: str, images_to_update: list, image_tags: dict, header: dict, pr_exists: bool, config_type: str = "singleuser"):
    allowed_config_types = ["singleuser", "profileList"]
    if config_type not in allowed_config_types:
        raise NotImplementedError(
            "The config type you are trying to use is not supported. Currently accepted config types are: %s" % allowed_config_types
        )

    base_ref = get_a_reference(repo_api, f"heads/{base_branch}", header)

    if pr_exists:
        # Set params for contents request
        params = {"ref": f"refs/heads/{target_branch}"}

        # Return reference
    else:
        # Set params for contents request
        params = {"ref": f"refs/heads/{base_branch}"}

        # Create target_branch, and return reference
        target_ref = create_branch(repo_api, target_branch, base_ref["object"]["sha"], header)

    # Download the file
    url = "/".join([API_ROOT, "repos", "HelmUpgradeBot", repo_name, "contents", path])
    resp = get_request(url, headers=header, params=params, output="json")

    # Decode file contents
    file_contents = json.loads(resp["content"].decode(encoding=resp["enconding"]))

    # Edit file contents
    if file_contents["singleuser"]["image"]["name"] in images_to_update:
        file_contents["singleuser"]["image"]["tag"] = image_tags[file_contents["singleuser"]["image"]["name"]]["latest"]

    if config_type == "profileList":
        for i, image in enumerate(file_contents["singleuser"]["profileList"]):
            if ("kubespawner_override" in image.keys()) and (image["kubespawner_override"]["image"].split(":")[0] in images_to_update):
                image_name = image["kubespawner_override"]["image"].split(":")[0]
                file_contents["singleuser"]["profileList"][i]["kubespawner_override"]["image"] = ":".join([image_name, image_tags[image_name]["latest"]])

    # Update the branch


def compare_image_tags(image_tags: dict) -> list:
    cond = [image_tags[image_name]["current"] != image_tags[image_name]["latest"] for image_name in image_tags.keys()]
    return list(compress(image_tags.keys(), cond))


def main(repo_owner, repo_name, config_file, target_branch, token, base_branch: str = "main", dry_run: bool = False):
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
        image_tags = get_image_tags(repo_owner, repo_name, base_branch, config_file, HEADER)
    else:
        image_tags = get_image_tags(repo_owner, repo_name, branch_name, config_file, HEADER)

    images_to_update = compare_image_tags(image_tags)

    if (len(images_to_update) > 0) and (not dry_run):
        if branch_name is None:
            random_id = "".join(random.sample(string.ascii_letters, 4))
            target_branch = "-".join([target_branch, random_id])
        else:
            target_branch = branch_name

        if (not fork_exists) and (not pr_exists):
            _ = make_fork(REPO_API, HEADER)

        update_image_tags(REPO_API, repo_name, target_branch, config_file, images_to_update, image_tags, HEADER, pr_exists)

    elif (len(images_to_update) == 0) and (not dry_run):
        # Delete local copy of the repo
        # cleanup(repo_name)

        if pr_exists:
            # A PR exists so exit cleanly
            import sys

            sys.exit

        if fork_exists and (not pr_exists):
            pass
            # A fork exists but there's no PR open, so remove the fork
            # remove_fork(repo_name, HEADER)
