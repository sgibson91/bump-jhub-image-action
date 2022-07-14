import base64
import json
import os

from loguru import logger

from .github_api import GitHubAPI
from .parse_image_tags import ImageTags
from .utils import read_config_with_yq, update_config_with_yq
from .yaml_parser import YamlParser

yaml = YamlParser()


class UpdateImageTags:
    """Update the tags of images stored in a JupyterHub YAML config"""

    def __init__(
        self,
        repository,
        github_token,
        config_path,
        images_info,
        base_branch="main",
        head_branch="bump-image-tags",
        labels=[],
        reviewers=[],
        team_reviewers=[],
        push_to_users_fork=None,
        dry_run=False,
    ):
        self.repository = repository
        self.config_path = config_path
        self.images_info = images_info
        self.base_branch = base_branch
        self.labels = labels
        self.reviewers = reviewers
        self.team_reviewers = team_reviewers
        self.push_to_users_fork = push_to_users_fork
        self.dry_run = dry_run

        self.head_branch = "/".join(
            [head_branch, config_path.replace("/", "-").replace(".", "")]
        )
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {github_token}",
        }

    def update_config(self):
        """Update the JupyterHub config file with the new image tags

        Returns:
            file_contents (str): The updated JupyterHub config in YAML format and
                encoded in base64
        """
        logger.info("Updating JupyterHub config...")
        for image in self.images_to_update:
            logger.info("Updating tag for image: {}", image)
            value = read_config_with_yq(self.config, self.image_tags[image]["path"])

            if ":" in value:
                self.config = update_config_with_yq(
                    self.config,
                    self.image_tags[image]["path"],
                    ":".join([image, self.image_tags[image]["latest"]]),
                )
            else:
                self.config = update_config_with_yq(
                    self.config,
                    self.image_tags[image]["path"],
                    self.image_tags[image]["latest"],
                )

        logger.info("Encoding config in base64...")
        config = yaml.object_to_yaml_str(self.config).encode("utf-8")
        config = base64.b64encode(config).decode("utf-8")

        return config

    def update(self):
        """Run the action to check if the docker images are up to date"""
        github = GitHubAPI(self)
        github.find_existing_pull_request()

        if self.push_to_users_fork is not None:
            github.check_fork_exists()

        if self.push_to_users_fork is not None and github.fork_exists:
            url = github.fork_api_url
        else:
            url = github.api_url

        branch = self.head_branch if github.pr_exists else self.base_branch

        image_parser = ImageTags(self, url, branch)
        image_parser.get_image_tags()

        if len(self.images_to_update) > 0 and not self.dry_run:
            logger.info(
                "Newer tags are available for the following images: {}",
                self.images_to_update,
            )

            if self.push_to_users_fork is not None:
                if github.fork_exists:
                    github.merge_upstream()
                else:
                    github.create_fork()

            if not github.pr_exists:
                resp = github.get_ref(self.base_branch)
                github.create_ref(self.head_branch, resp["object"]["sha"])

            updated_config = self.update_config()
            commit_msg = f"Bump images {[image for image in self.images_to_update]} to tags {[self.image_tags[image]['latest'] for image in self.images_to_update]}, respectively"
            github.create_commit(commit_msg, updated_config)
            github.create_update_pull_request()

        elif len(self.images_to_update) > 0 and self.dry_run:
            logger.info(
                "Newer tags are available for the following images: {}. Pull Request will not be opened due to --dry-run flag being set.",
                self.images_to_update,
            )
        else:
            logger.info("All image tags are up-to-date!")


def split_str_to_list(input_str, split_char=" "):
    """Split a string into a list of elements.

    Args:
        input_str (str): The string to split
        split_char (str, optional): The character to split the string by. Defaults
            to " " (a single whitespace).

    Returns:
        List[str]: The string split into a list
    """
    split_str = input_str.split(split_char)

    # For each element in split_str, strip leading/trailing whitespace
    for i, element in enumerate(split_str):
        split_str[i] = element.strip()

    return split_str


def assert_images_info_input(images_info):
    """Assert the user input provided to the images_info variable is as of the expected
    structure. I.e., a list of dictionaries, where each dictionary must have a
    'values_path' key whose value is a string type.

    Args:
        images_info (list[dict]): The input list of dictionaries to check
    """
    assert isinstance(images_info, list)

    for obj in images_info:
        assert isinstance(obj, dict)
        assert "values_path" in obj.keys()
        assert isinstance(obj["values_path"], str)


def main():
    # Retrieve environment variables
    config_path = os.environ.get("INPUT_CONFIG_PATH", None)
    images_info = json.loads(os.environ.get("INPUT_IMAGES_INFO", "null"))
    github_token = os.environ.get("INPUT_GITHUB_TOKEN", None)
    repository = os.environ.get("INPUT_REPOSITORY", None)
    base_branch = os.environ.get("INPUT_BASE_BRANCH", None)
    head_branch = os.environ.get("INPUT_HEAD_BRANCH", "bump-image-tags")
    labels = os.environ.get("INPUT_LABELS", [])
    reviewers = os.environ.get("INPUT_REVIEWERS", [])
    team_reviewers = os.environ.get("INPUT_TEAM_REVIEWERS", [])
    push_to_users_fork = os.environ.get("INPUT_PUSH_TO_USERS_FORK", None)
    dry_run = os.environ.get("INPUT_DRY_RUN", False)

    # Reference dict for required inputs
    required_vars = {
        "CONFIG_PATH": config_path,
        "IMAGES_INFO": images_info,
        "GITHUB_TOKEN": github_token,
        "REPOSITORY": repository,
        "BASE_BRANCH": base_branch,
    }

    # Check all the required inputs are properly set
    for k, v in required_vars.items():
        if v is None:
            raise ValueError(f"{k} must be set!")

    # Assert images_info is set correctly
    assert_images_info_input(images_info)

    # If labels/reviewers have been provided, transform from string into a list
    if labels:
        labels = split_str_to_list(labels, split_char=",")
    if reviewers:
        reviewers = split_str_to_list(reviewers, split_char=",")
    if team_reviewers:
        team_reviewers = split_str_to_list(team_reviewers, split_char=",")

    # Check the dry_run variable is properly set
    if isinstance(dry_run, str) and (dry_run == "true"):
        dry_run = True
    elif isinstance(dry_run, str) and (dry_run != "true"):
        dry_run = False
    elif isinstance(dry_run, bool) and not dry_run:
        pass
    else:
        raise ValueError("DRY_RUN variable can only take values 'true' or 'false'")

    update_image_tags = UpdateImageTags(
        repository,
        github_token,
        config_path,
        images_info,
        base_branch=base_branch,
        head_branch=head_branch,
        labels=labels,
        reviewers=reviewers,
        team_reviewers=team_reviewers,
        push_to_users_fork=push_to_users_fork,
        dry_run=dry_run,
    )
    update_image_tags.update()


if __name__ == "__main__":
    main()
