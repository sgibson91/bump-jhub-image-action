import yaml

from loguru import logger

from .utils import get_request

API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
DOCKERHUB_ROOT = "https://hub.docker.com/v2/repositories"


def get_deployed_image_tags(
    api_url: str,
    header: dict,
    branch: str,
    filepath: str,
    image_tags: dict,
) -> dict:
    """Read the tags of the deployed images from a YAML config file

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        branch (str): The branch the config file is located on
        filepath (str): The path to the config file
        image_tags (dict): A dictionary to store the image information in

    Returns:
        image_tags (dict): A dictionary containing info on the images currently
            deployed
    """
    api_url = api_url.replace(API_ROOT, RAW_ROOT)
    url = "/".join([api_url, branch, filepath])
    resp = get_request(url, headers=header, output="text")
    config = yaml.safe_load(resp)

    if "singleuser" in config.keys():
        image_tags[config["singleuser"]["image"]["name"]] = {
            "current": config["singleuser"]["image"]["tag"]
        }

        if "profileList" in config["singleuser"].keys():
            for image in config["singleuser"]["profileList"]:
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

    image_tags[image_name]["latest"] = new_tag

    return image_tags


def get_image_tags(api_url: str, header: dict, branch: str, filepath: str) -> dict:
    """Get the image names and tags that are deployed in a config file

    Args:
        api_url (str): The URL to send the request to
        header (dict): A dictionary of headers to send with the request. Must
            contain and authorisation token.
        branch (str): The name of the branch on which the config file is located
        filepath (str): The path to the config file relative to the root of the
            repo

    Returns:
        image_tags (dict): A dictionary containing the names and tags, both
            currently deployed and most recently released
    """
    image_tags: dict[str, str] = {}

    logger.info("Fetching currently deployed image tags...")
    image_tags = get_deployed_image_tags(api_url, header, branch, filepath, image_tags)

    logger.info("Fetching most recently published image tags...")
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
