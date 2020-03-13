import os
import sys
import json
import yaml
import shutil
import logging
import requests
import subprocess

import numpy as np

from itertools import compress


def configure_logging(identity=False):
    if identity:
        logging.basicConfig(
            level=logging.DEBUG,
            filename="UpdateDockerTags.log",
            filemode="a",
            format="[%(asctime)s %(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s %(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


class UpdateDockerTags:
    """Class to check that the tags of Docker images in a JupyterHub config
    are up to date"""

    def __init__(self, argsDict):
        """Constructor function for UpdateDockerTags class"""
        for k, v in argsDict.items():
            setattr(self, k, v)

        self.repo_api = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/"
        )
        configure_logging(identity=self.identity)
        self.remove_fork()

        if self.token_name is None:
            self.token = os.getenv("API_TOKEN", None)
            if self.token is None:
                raise EnvironmentError(
                    "Either --token-name or API_TOKEN must be set"
                )

            self.headers = {"Authorization": f"token {self.token}"}

        else:
            self.get_token()

    def check_image_tags(self):
        """Function to check the image tags against the currently deployed tags
        """
        if self.dry_run:
            logging.info("THIS IS A DRY-RUN. CHANGES WILL NOT BE MADE.")

        self.new_image_tags = {}
        self.old_image_tags = {}

        api_urls = {
            "jupyterhub": f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/master/config/config-template.yaml",
            "minimal-notebook": "https://hub.docker.com/v2/repositories/jupyter/minimal-notebook/tags",
            "datascience-notebook": "https://hub.docker.com/v2/repositories/jupyter/datascience-notebook/tags",
            "custom-env": f"https://hub.docker.com/v2/repositories/turinginst/bridge-data-env/tags",
        }
        images = list(api_urls.keys())
        images.remove("jupyterhub")

        logging.info("Pulling currently deployed image tags...")
        self.find_most_recent_tag_github(api_urls["jupyterhub"])

        logging.info("Pulling most recent image tags...")
        for image in images:
            self.find_most_recent_tag_dockerhub(image, api_urls[image])

        cond = [
            (self.old_image_tags[image] != self.new_image_tags[image])
            for image in images
        ]

        if np.any(cond):
            logging.info(
                "The following images can be updated: %s"
                % list(compress(images, cond))
            )
            if not self.dry_run:
                self.update_images(list(compress(images, cond)))
        else:
            logging.info("All images are up to date")

    def update_images(self, images_to_update):
        """Function to update the Docker image tags in a JupyterHub config file

        Arguments:
            images_to_update {list of strings} -- list of images to be updated
        """
        if not self.fork_exists:
            self.make_fork()
        self.clone_fork()

        os.chdir(self.repo_name)
        self.checkout_branch()
        self.edit_config(images_to_update)
        self.add_commit_push(images_to_update)
        self.create_pull_request()

        self.clean_up()

    def add_commit_push(self, images_to_update):
        """Perform git add, commit, push actions to an edited file

        Arguments:
            images_to_update {list of strings} -- list of image tags to be updated
        """
        logging.info("Adding file: %s" % self.fname)
        add_cmd = ["git", "add", self.fname]

        try:
            subprocess.check_call(add_cmd)
            logging.info("Successfully added file")
        except Exception:
            self.clean_up()
            self.remove_fork()

        logging.info("Committing file: %s" % self.fname)
        commit_msg = f"Bump images {[image for image in images_to_update]} to tags {[self.new_image_tags[image] for image in images_to_update]}, respectively"
        commit_cmd = ["git", "commit", "-m", commit_msg]

        try:
            subprocess.check_call(commit_cmd)
            logging.info("Successfully committed file")
        except Exception:
            self.clean_up()
            self.remove_fork()

        logging.info("Pushing commits to branch: %s" % self.branch)
        push_cmd = [
            "git",
            "push",
            f"https://sgibson91:{self.token}@github.com/sgibson91/{self.repo_name}",
            self.branch,
        ]

        try:
            subprocess.check_call(push_cmd)
            logging.info("Successfully pushed changes")
        except Exception:
            self.clean_up()
            self.remove_fork()

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

            logging.info(
                "Pulling master branch of: %s/%s"
                % (self.repo_owner, self.repo_name)
            )
            pull_cmd = [
                "git",
                "pull",
                f"https://github.com/{self.repo_owner}/{self.repo_name}.git",
                "master",
            ]

            try:
                subprocess.check_call(pull_cmd)
                logging.info("Successfully pulled master branch")
            except Exception:
                self.clean_up()
                self.remove_fork()

        logging.info("Checkout out branch: %s" % self.branch)
        chkt_cmd = ["git", "checkout", "-b", self.branch]

        try:
            subprocess.check_call(chkt_cmd)
            logging.info("Successfully checked out branch")
        except Exception:
            self.clean_up()
            self.remove_fork()

    def clean_up(self):
        """Clean up locally cloned git repo"""
        cwd = os.getcwd()
        this_dir = cwd.split("/")[-1]
        if this_dir == self.repo_name:
            os.chdir(os.pardir)

        if os.path.exists(self.repo_name):
            logging.info("Deleting local repo: %s" % self.repo_name)
            shutil.rmtree(self.repo_name)
            logging.info("Deleted local repository")

        sys.exit()

    def clone_fork(self):
        """Locally clone a fork of a GitHub repo"""
        logging.info("Cloning fork: %s" % self.repo_name)
        clone_cmd = [
            "git",
            "clone",
            f"https://github.com/sgibson91/{self.repo_name}.git",
        ]

        try:
            subprocess.check_call(clone_cmd)
            logging.info("Successfully cloned repo")
        except Exception:
            self.clean_up()
            self.remove_fork()

    def create_pull_request(self):
        """Open a Pull Request to the original repo on GitHub"""
        logging.info("Creating Pull Request")
        pr = {
            "title": "Bumping Docker image tags",
            "body": "This PR is bumping the Docker image tags for the computing environments to the most recently published",
            "base": "master",
            "head": f"sgibson91:{self.branch}",
        }

        res = requests.post(
            self.repo_api + "pulls", headers=self.headers, json=pr
        )

        if res:
            logging.info("Successfully opened Pull Request")
        else:
            self.clean_up()
            self.remove_fork()

    def delete_old_branch(self):
        """Delete a branch of a git repo"""
        res = requests.get(
            f"https://api.github.com/repos/sgibson91/{self.repo_name}/branches",
            headers=self.headers,
        )

        if self.branch in [x["name"] for x in res.json()]:
            logging.info("Deleting old branch: %s" % self.branch)
            del_remote_cmd = ["git", "push", "--delete", "origin", self.branch]

            try:
                subprocess.check_call(del_remote_cmd)
                logging.info("Successfully deleted remote branch")
            except Exception:
                self.clean_up()
                self.remove_fork()

    def edit_config(self, images_to_update):
        """Update the JupyterHub config file with the new image tags

        Arguments:
            images_to_update {list of strings} -- list of image tags to be updated
        """
        logging.info("Updating JupyterHub config file")

        self.fname = os.path.join("config", "config-template.yaml")

        with open(self.fname, "r") as f:
            config_yaml = yaml.safe_load(f)

        if "minimal-notebook" in images_to_update:
            config_yaml["singleuser"]["image"]["tag"] = self.new_image_tags[
                "minimal-notebook"
            ]

        if "datascience-notebook" in images_to_update:
            [
                d["kubespawner_override"].__setitem__(
                    "image",
                    f"jupyter/datascience-notebook:{self.new_image_tags['datascience-notebook']}",
                )
                for d in config_yaml["singleuser"]["profileList"]
                if d["display_name"] == "Data Science Environment"
            ]

        if "custom-env" in images_to_update:
            [
                d["kubespawner_override"].__setitem__(
                    "image",
                    f"turinginst/bridge-data-env:{self.new_image_tags['custom-env']}",
                )
                for d in config_yaml["singleuser"]["profileList"]
                if d["display_name"] == "Custom repo2docker image"
            ]

        with open(self.fname, "w") as f:
            yaml.safe_dump(config_yaml, f)

        logging.info("Updated JupyterHub config")

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
        res = yaml.safe_load(requests.get(url, headers=self.headers).text)

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

    def get_token(self):
        """Get GitHub Personal Access Token from Azure Keyvault"""
        self.login()

        logging.info("Retrieving token: %s" % self.token_name)
        vault_cmd = [
            "az",
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            self.keyvault,
            "--name",
            self.token_name,
            "--query",
            "value",
            "--output",
            "tsv",
        ]

        try:
            self.token = (
                subprocess.check_output(vault_cmd).decode("utf-8").strip("\n")
            )
            self.headers = {"Authorization": f"token {self.token}"}
            logging.info("Successfully retrieved token")
        except Exception:
            self.clean_up()
            self.remove_fork()

    def login(self):
        """Login to Azure"""
        login_cmd = ["az", "login"]

        if self.identity:
            login_cmd.append("--identity")
            logging.info("Logging into Azure with Managed System Identity")
        else:
            login_cmd.extend(["--output", "none"])
            logging.info("Logging into Azure interactively")

        try:
            subprocess.check_call(login_cmd)
            logging.info("Successfully logged into Azure")
        except Exception:
            self.clean_up()
            self.remove_fork()

    def make_fork(self):
        """Fork a GitHub repo"""
        logging.info("Forking repo: %s" % self.repo_name)
        requests.post(self.repo_api + "forks", headers=self.headers)
        self.fork_exists = True

    def remove_fork(self):
        """Delete a fork of a GitHub repo"""
        self.check_fork_exists()

        if self.fork_exists:
            logging("A fork exists of repo: %s" % self.repo_name)

            logging.info("Deleting fork...")
            requests.delete(
                f"https://api.github.com/repos/sgibson91/{self.repo_name}",
                headers=self.headers,
            )

            self.fork_exists = False
            time.sleep(5)

            logging.info("Fork successfully deleted")
