from typing import Tuple, Union

import jmespath
from loguru import logger

from .http_requests import get_request, patch_request, post_request


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
    logger.info("Adding labels to Pull Request: {}", pr_url)
    logger.info("Adding labels: {}", labels)
    post_request(pr_url, headers=header, json={"labels": labels})


def assign_reviewers(
    reviewers: list, team_reviewers: list, pr_url: str, header: dict
) -> None:
    """Request reviews from GitHub users on a Pull Request

    Args:
        reviewers (list): A list of GitHub user to request reviews from
            (**excluding** the leading `@` symbol)
        team_reviewers (list): A list of GitHub teams to request reviews from, in the
            form ORG_NAME/TEAM_NAME
        pr_url (str): The API URL of the Pull Request (pulls endpoint) to send
            the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain an authorisation token.
    """
    logger.info("Assigning reviewers to Pull Request: {}", pr_url)

    if reviewers:
        logger.info("Assigning reviewers: {}", reviewers)
    if team_reviewers:
        logger.info("Assigning team reviewers: {}", team_reviewers)

    url = "/".join([pr_url, "requested_reviewers"])
    post_request(
        url,
        headers=header,
        json={"reviewers": reviewers, "team_reviewers": team_reviewers},
    )


def create_update_pr(
    api_url: str,
    header: dict,
    base_branch: str,
    head_branch: str,
    image_tags: dict,
    images_to_update: list,
    labels: list,
    reviewers: list,
    team_reviewers: list,
    pr_exists: bool,
) -> None:
    """Create or update a Pull Request via the GitHub API

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        base_branch (str): The name of the branch to open the Pull Request against
        head_branch (str): The name of the branch to open the Pull Request from
        image_tags (dict): A dictionary of all docker images in use by the
            JupyterHub, their currently deployed tags, and the most recent tags
            available on the container registry
        images_to_update (list): A list of docker images that need updating
        labels (list): A list of labels to apply to the Pull Request
        reviewers (list): A list of GitHub users to request reviews from
        team_reviewers (list): A list of GitHub teams to request reviews from, in the
            form ORG_NAME/TEAM_NAME
        pr_exists (bool): True when a Pull Request has already been opened. This existing
            PR will be updated.
    """
    logger.info("Creating Pull Request...")

    url = "/".join([api_url, "pulls"])
    pr = {
        "title": "Bumping Docker image tags in JupyterHub config",
        "body": (
            "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
            + "\n".join(
                [
                    f"`{image}`: `{image_tags[image]['current']}` -> `{image_tags[image]['latest']}`"
                    for image in images_to_update
                ]
            )
        ),
        "base": base_branch,
    }

    if pr_exists:
        pr["state"] = "open"

        resp = patch_request(url, headers=header, json=pr, return_json=True)

        logger.info(f"Pull Request #{resp['number']} updated!")
    else:
        pr["head"] = head_branch

        resp = post_request(url, headers=header, json=pr, return_json=True)

        logger.info(f"Pull Request #{resp['number']} created!")

        if labels:
            add_labels(labels, resp["issue_url"], header)

        if reviewers or team_reviewers:
            assign_reviewers(reviewers, team_reviewers, resp["url"], header)


def find_existing_pr(api_url: str, header: dict) -> Tuple[bool, Union[str, None]]:
    """Check if the bot already has an open Pull Request

    Args:
        api_url (str): The API URL of the GitHub repository to send requests to
        header (dict): A dictionary of headers to send with the GET request

    Returns:
        pr_exists (bool): True if there is already an open Pull Request.
            False otherwise.
        head_branch (str): The name of the branch to send commits to
    """
    logger.info("Finding Pull Requests previously opened to bump image tags...")

    url = "/".join([api_url, "pulls"])
    params = {"state": "open", "sort": "created", "direction": "desc"}
    resp = get_request(url, headers=header, params=params, output="json")

    # Expression to match the head ref
    head_label_exp = jmespath.compile("[*].head.label")
    matching_labels = head_label_exp.search(resp)

    # Create list of labels of matching PRs
    matching_prs = [label for label in matching_labels if "bump_image_tags" in label]

    if len(matching_prs) > 1:
        logger.info(
            "More than one Pull Request open. Will push new commits to the most recent Pull Request."
        )

        ref = matching_prs[0].split(":")[-1]

        return True, ref

    elif len(matching_prs) == 1:
        logger.info(
            "One Pull Request open. Will push new commits to this Pull Request."
        )

        ref = matching_prs[0].split(":")[-1]

        return True, ref

    else:
        logger.info(
            "No relevant Pull Requests found. A new Pull Request will be opened."
        )
        return False, None
