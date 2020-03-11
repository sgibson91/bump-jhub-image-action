import json
import requests


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
        self.api_urls = {
            "jupyterhub": f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/config/config-template.yaml",
            "minimal_notebook": "https://hub.docker.com/v2/repositories/jupyter/minimal-notebook/tags",
            "datascience-notebook": "https://hub.docker.com/v2/repositories/jupyter/datascience-notebook/tags",
            "custom-env": f"https://hub.docker.com/v2/repositories/{self.docker_repo}/{self.docker_image}/tags",
        }

        for api_url in self.api_urls.keys():
            if api_url == "jupyterhub":
                pass
            else:
                self.find_most_recent_tag_dockerhub(
                    api_url, self.api_urls[api_url]
                )

    def find_most_recent_tag_dockerhub(self, name, url):
        """Function to find most recent tag of an image from Docker Hub

        Arguments:
            name {str} -- Name of the image
            url {str} -- API URL of the Docker Hub image repository
        """
        results = json.loads(requests.get(url).text)

        updates_sorted = sorted(
            results["results"], key=lambda k: k["last_updated"]
        )

        if updates_sorted[-1]["name"] == "latest":
            new_tag = updates_sorted[-2]["name"]
        else:
            new_tag = updates_sorted[-1]["name"]

        self.new_image_tags[name] = new_tag


if __name__ == "__main__":
    obj = UpdateDockerTags()
    obj.check_image_tags()
