import yaml

from .utils import get_request

RAW_ROOT = "https://raw.githubusercontent.com"
DOCKERHUB_ROOT = "https://hub.docker.com/v2/repositories"


def get_deployed_image_tags(
    repo_owner: str,
    repo_name: str,
    branch: str,
    filepath: str,
    header: dict,
    image_tags: dict,
) -> dict:
    """Read the tags of the deployed images from a YAML config file

    Args:
        repo_owner (str): The GitHub account that owns the host repo
        repo_name (str): The name of the host repo
        branch (str): The branch the config file is located on
        filepath (str): The path to the config file
        header (dict): A dictionary of headers to send with the API requests.
            Must contain an authorisation token.
        image_tags (dict): A dictionary to store the image information in

    Returns:
        image_tags (dict): A dictionary containing info on the images currently
            deployed
    """
    url = "/".join([RAW_ROOT, repo_owner, repo_name, branch, filepath])
    resp = get_request(url, headers=header, output="text")
    config = yaml.safe_load(resp)

    if "singleuser" in config.keys():
        image_tags[config["singleuser"]["image"]["name"]] = {
            "current": config["singleuser"]["image"]["tag"]
        }

        if "profileList" in config["singleuser"].keys():
            for image in config["singleuser"]:
                if "kubespawner_override" in image.keys():
                    image_name, image_tag = image["kubespawner_override"][
                        "image"
                    ].split(":")
                    image_tags[image_name] = {"current": image_tag}

    return image_tags


def get_most_recent_image_tags_dockerhub(image_name: str, image_tags: dict) -> dict:
    """For an image hosted on DockerHub, look up the most recent tag

    Args:
        image_name (str): The name of the image to look up tags for
        image_tags (dict): A dictionary to store the most recent tag in

    Returns:
        image_tags (dict): A dictionary containing info on the images and their
            most recent tags
    """
    url = "/".join([DOCKERHUB_ROOT, image_name, "tags"])
    resp = get_request(url, output="json")

    tags_sorted = sorted(resp["results"], key=lambda k: k["last_updated"])

    if tags_sorted[-1]["name"] == "latest":
        new_tag = tags_sorted[-2]["name"]
    else:
        new_tag = tags_sorted[-1]["name"]

    image_tags[image_name] = {"latest": new_tag}

    return image_tags


def get_image_tags(
    repo_owner: str, repo_name: str, branch: str, filepath: str, header: dict
) -> dict:
    """Get the image names and tags that are deployed in a config file

    Args:
        repo_owner (str): The GitHub account that owns the host repo
        repo_name (str): The name of the host repo
        branch (str): The name of the branch on which the config file is located
        filepath (str): The path to the config file relative to the root of the
            repo
        header (dict): A dictionary of headers to send with API requests.
            Must contain an authorisation token.

    Returns:
        image_tags (dict): A dictionary containing the names and tags, both
            currently deployed and most recently released
    """
    image_tags = {}

    image_tags = get_deployed_image_tags(
        repo_owner, repo_name, branch, filepath, header, image_tags
    )

    for image in image_tags.keys():
        if len(image.split("/")) == 2:
            image_tags = get_most_recent_image_tags_dockerhub(image, image_tags)
        elif len(image.split("/")) > 2:
            raise NotImplementedError(
                "Cannot currently retrieve images from: %s" % image.split("/")[0]
            )
        else:
            raise ValueError("Unknown image name: %s" % image)

    return image_tags
