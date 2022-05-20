import base64
import os

from .github_api import GitHubAPI
from .parse_image_tags import ImageTags
from .utils import read_config_with_jq, update_config_with_jq
from .yaml_parser import YamlParser

yaml = YamlParser()


class UpdateImageTags:
    """Update the tags of images stored in a JupyterHub YAML config"""

    def __init__(
        self,
        repository,
        github_token,
        config_path,
        values_paths,
        base_branch="main",
        head_branch="bump-image-tags",
        labels=[],
        reviewers=[],
        team_reviewers=[],
        dry_run=False,
    ):
        self.repository = repository
        self.config_path = config_path
        self.values_paths = values_paths
        self.base_branch = base_branch
        self.head_branch = head_branch
        self.labels = labels
        self.reviewers = reviewers
        self.team_reviewers = team_reviewers
        self.dry_run = dry_run

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
        for image in self.images_to_update:
            value = read_config_with_jq(self.config, self.image_tags[image]["path"])

            if ":" in value:
                self.config = update_config_with_jq(
                    self.config,
                    self.image_tags[image]["path"],
                    ":".join([image, self.image_tags[image]["latest"]]),
                )
            else:
                self.config = update_config_with_jq(
                    self.config,
                    self.image_tags[image]["path"],
                    self.image_tags[image]["latest"],
                )

        encoded_config = yaml.object_to_yaml_str(self.config).encode("utf-8")
        base64_bytes = base64.b64encode(encoded_config)
        config = base64_bytes.decode("utf-8")

        return config

    def update(self):
        """Run the action to check if the docker images are up to date"""
        github = GitHubAPI(self)
        github.find_existing_pull_request()

        if github.pr_exists:
            image_parser = ImageTags(self, self.head_branch)
        else:
            image_parser = ImageTags(self, self.base_branch)

            resp = github.get_ref(self.base_branch)
            github.create_ref(self.head_branch, resp["object"]["sha"])

        image_parser.get_image_tags()

        updated_config = self.update_config()
        commit_msg = f"Bump images {[image for image in self.images_to_update]} to tags {[self.image_tags[image]['latest'] for image in self.images_to_update]}, respectively"
        github.create_commit(commit_msg, updated_config)
        github.create_update_pull_request()


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


def main():
    # Retrieve environment variables
    config_path = (
        os.environ["INPUT_CONFIG_PATH"] if "INPUT_CONFIG_PATH" in os.environ else None
    )
    values_paths = (
        os.environ["INPUT_VALUES_PATHS"] if "INPUT_VALUES_PATHS" in os.environ else None
    )
    github_token = (
        os.environ["INPUT_GITHUB_TOKEN"] if "INPUT_GITHUB_TOKEN" in os.environ else None
    )
    repository = (
        os.environ["INPUT_REPOSITORY"] if "INPUT_REPOSITORY" in os.environ else None
    )
    base_branch = (
        os.environ["INPUT_BASE_BRANCH"] if "INPUT_BASE_BRANCH" in os.environ else "main"
    )
    head_branch = (
        os.environ["INPUT_HEAD_BRANCH"]
        if "INPUT_HEAD_BRANCH" in os.environ
        else "bump-image-tags"
    )
    labels = os.environ["INPUT_LABELS"] if "INPUT_LABELS" in os.environ else []
    reviewers = os.environ["INPUT_REVIEWERS"] if "INPUT_REVIEWERS" in os.environ else []
    team_reviewers = (
        os.environ["INPUT_TEAM_REVIEWERS"]
        if "INPUT_TEAM_REVIEWERS" in os.environ
        else []
    )
    dry_run = os.environ["INPUT_DRY_RUN"] if "INPUT_DRY_RUN" in os.environ else False

    # Reference dict for required inputs
    required_vars = {
        "CONFIG_PATH": config_path,
        "VALUES_PATHS": values_paths,
        "GITHUB_TOKEN": github_token,
        "REPOSITORY": repository,
    }

    # Check all the required inputs are properly set
    for k, v in required_vars.items():
        if v is None:
            raise ValueError(f"{k} must be set!")

    # Split the parsed values paths into a list
    values_paths = split_str_to_list(values_paths)

    # If labels/reviewers have been provided, transform from string into a list
    if len(labels) > 0:
        labels = split_str_to_list(labels, split_char=",")
    if len(reviewers) > 0:
        reviewers = split_str_to_list(reviewers, split_char=",")
    if len(team_reviewers) > 0:
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
        values_paths,
        base_branch=base_branch,
        head_branch=head_branch,
        labels=labels,
        reviewers=reviewers,
        team_reviewers=team_reviewers,
        dry_run=dry_run,
    )
    update_image_tags.update()


if __name__ == "__main__":
    main()
