import os
import json
import yaml
import requests
import subprocess

import numpy as np

from itertools import compress

API_TOKEN = os.getenv("API_TOKEN", None)
if API_TOKEN is None:
    raise EnvironmentError("API_TOKEN must be set")
headers = {"Authorization": f"token {API_TOKEN}"}


class UpdateDockerTags:
    """Class to check that the tags of Docker images in a JupyterHub config
    are up to date"""

    def __init__(self):
        """Constructor function for UpdateDockerTags class"""
        self.repo_owner = "alan-turing-institute"
        self.repo_name = "bridge-data-platform"
        self.docker_repo = "turinginst"
        self.docker_image = "bridge-data-env"

        self.branch = "bump-image-tags"
        self.fork_exists = self.check_fork_exists()
        self.repo_api = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/"
        )

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
            self.update_images(list(compress(images, cond)))
        else:
            print("All images are up to date")

    def update_images(self, images_to_update):
        """[summary]

        Arguments:
            images_to_update {[type]} -- [description]
        """
        if not self.fork_exists:
            self.make_fork()
        self.clone_fork()

        os.chdir(self.repo_name)
        self.checkout_branch()
        self.edit_config(images_to_update)

    def check_fork_exists(self):
        """Check if sgibson91 has a fork of the repo or not"""
        res = requests.get("https://api.github.com/users/sgibson91/repos")

        self.fork_exists = bool(
            [x for x in res.json() if x["name"] == self.repo_name]
        )

    def checkout_branch(self):
        """Checkout a branch of a git repo"""
        if self.fork_exists:
            self.delete_old_branch()

            pull_cmd = [
                "git",
                "pull",
                f"https://github.com/{self.repo_owner}/{self.repo_name}.git",
                "master",
            ]
            subprocess.check_call(pull_cmd)

        chkt_cmd = ["git", "checkout", "-b", self.branch]
        subprocess.check_call(chkt_cmd)

    def clone_fork(self):
        """Locally clone a fork of a GitHub repo"""
        clone_cmd = [
            "git",
            "clone",
            f"https://github.com/sgibson91/{self.repo_name}.git",
        ]
        subprocess.check_call(clone_cmd)

    def delete_old_branch(self):
        """Delete a branch of a git repo"""
        res = requests.get(
            f"https://api.github.com/repos/sgibson91/{self.repo_name}/branches",
            headers=headers,
        )

        if self.branch in [x["name"] for x in res.json()]:
            del_remote_cmd = ["git", "push", "--delete", "origin", self.branch]
            subprocess.check_call(del_remote_cmd)

            del_local_cmd = ["git", "branch", "-d", self.branch]
            subprocess.check_call(del_local_cmd)

    def edit_config(self, images_to_update):
        """Update the JupyterHub config file with the new image tags

        Arguments:
            images_to_update {list of strings} -- list of image tags to be updated
        """
        fname = os.path.join("config", "config-template.yaml")

        with open(fname, "r") as f:
            config_yaml = yaml.safe_load(f)
        print(json.dumps(config_yaml, indent=2))

        if "minimal-notebook" in images_to_update:
            config_yaml["singleuser"]["image"]["tag"] = self.new_image_tags[
                "minimal-notebook"
            ]

        if "datascience-notebook" in images_to_update:
            [
                d.__setitem__(
                    "image",
                    f"jupyter/datascience-notebook:{self.new_image_tags['datascience-notebook']}",
                )
                for d in config_yaml["singleuser"]["profileList"]
                if d["display_name"] == "Data Science Environment"
            ]

        if "custom-env" in images_to_update:
            [
                d.__setitem__(
                    "image",
                    f"{self.docker_repo}/{self.docker_image}:{self.new_image_tags['custom-env']}",
                )
                for d in config_yaml["singleuser"]["profileList"]
                if d["display_name"] == "Custom repo2docker image"
            ]

        with open(fname, "w") as f:
            yaml.safe_dump(config_yaml, f)

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

    def make_fork(self):
        """Fork a GitHub repo"""
        requests.post(self.repo_api + "forks", headers=headers)
        self.fork_exists = True


if __name__ == "__main__":
    obj = UpdateDockerTags()
    obj.check_image_tags()
