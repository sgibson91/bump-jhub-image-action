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
    config_type: str = "singleuser",
) -> dict:
    allowed_config_types = ["singleuser", "profileList"]
    if config_type not in allowed_config_types:
        raise NotImplementedError(
            "The type of config you requested has not yet been implemented. Current options are: %s"
            % allowed_config_types
        )

    url = "/".join([RAW_ROOT, repo_owner, repo_name, branch, filepath])
    resp = get_request(url, headers=header, output="text")
    config = yaml.safe_load(resp)

    image_tags[config["singleuser"]["image"]["name"]] = {
        "current": config["singleuser"]["image"]["tag"]
    }

    if config_type == "profileList":
        for image in config["singleuser"]:
            if "kubespawner_override" in image.keys():
                image_name, image_tag = image["kubespawner_override"]["image"].split(
                    ":"
                )
                image_tags[image_name] = {"current": image_tag}

    return image_tags


def get_most_recent_image_tags_dockerhub(image_name: str, image_tags: dict) -> dict:
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
