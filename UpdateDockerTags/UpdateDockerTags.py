import os
import json
import yaml
import requests

import numpy as np

API_TOKEN = os.getenv("API_TOKEN", None)
if API_TOKEN is None:
    raise EnvironmentError("API_TOKEN must be set")


class UpdateDockerTags:
    """Class to check that the tags of Docker images in a JupyterHub config
    are up to date"""

    def __init__(self):
        """Constructor function for UpdateDockerTags class"""
        self.repo_owner = "alan-turing-institute"
        self.repo_name = "bridge-data-platform"
        self.docker_repo = "turinginst"
        self.docker_image = "bridge-data-env"

    def check_image_tags(self):
        """Function to check the image tags against the currently deployed tags
        """
        self.new_image_tags = {}
        self.old_image_tags = {}

        api_urls = {
            "jupyterhub": f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/config/config-template.yaml",
            "minimal-notebook": "https://hub.docker.com/v2/repositories/jupyter/minimal-notebook/tags",
            "datascience-notebook": "https://hub.docker.com/v2/repositories/jupyter/datascience-notebook/tags",
            "custom-env": f"https://hub.docker.com/v2/repositories/{self.docker_repo}/{self.docker_image}/tags",
        }
        images = list(api_urls.keys())
        images.remove("jupyterhub")

        self.find_most_recent_tag_github(api_urls["jupyterhub"])

        for image in images:
            self.find_most_recent_tag_dockerhub(image, api_urls[image])

        cond = [
            (self.old_image_tags[image] != self.new_image_tags[image])
            for image in images
        ]

        if np.any(cond):
            print("Some images need updating")
            # self.update_images(list(compress(images, condition)))
        else:
            print("All images are up to date")

    def find_most_recent_tag_dockerhub(self, name, url):
        """Function to find most recent tag of an image from Docker Hub

        Arguments:
            name {str} -- Name of the image
            url {str} -- API URL of the Docker Hub image repository
        """
        res = json.loads(requests.get(url).text)

        updates_sorted = sorted(
            res["results"], key=lambda k: k["last_updated"]
        )

        if updates_sorted[-1]["name"] == "latest":
            new_tag = updates_sorted[-2]["name"]
        else:
            new_tag = updates_sorted[-1]["name"]

        self.new_image_tags[name] = new_tag

    def find_most_recent_tag_github(self, url):
        """Function to find old image tags from GitHub

        Arguments:
            url {str} -- GitHub raw content URL to read config from
        """
        headers = {"Authorization": f"token {API_TOKEN}"}
        res = yaml.safe_load(requests.get(url, headers=headers).text)

        self.old_image_tags["minimal-notebook"] = res["singleuser"]["image"][
            "tag"
        ]

        for image_name in ["datascience-notebook", "custom-env"]:
            for profile in res["singleuser"]["profileList"]:
                datascience_cond = (image_name == "datascience-notebook") and (
                    profile["display_name"] == "Data Science Environment"
                )
                custom_cond = (image_name == "custom-env") and (
                    profile["display_name"] == "Custom repo2docker image"
                )

                if datascience_cond or custom_cond:
                    old_image = profile["kubespawner_override"]["image"]
                    old_tag = old_image.split(":")[-1]
                    self.old_image_tags[image_name] = old_tag


if __name__ == "__main__":
    obj = UpdateDockerTags()
    obj.check_image_tags()
