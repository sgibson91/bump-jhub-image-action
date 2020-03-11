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
        self.api_urls = {
            "jupyterhub": f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/config/config-template.yaml",
            "minimal_notebook": "https://hub.docker.com/v2/repositories/jupyter/minimal-notebook/tags",
            "datascience-notebook": "https://hub.docker.com/v2/repositories/jupyter/datascience-notebook/tags",
            "custom-env": f"https://hub.docker.com/v2/repositories/{self.docker_repo}/{self.docker_image}/tags",
        }


if __name__ == "__main__":
    obj = UpdateDockerTags()
    obj.check_image_tags()
