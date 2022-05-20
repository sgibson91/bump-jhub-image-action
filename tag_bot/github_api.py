import random
import string

import jmespath
from requests import put

from .http_requests import get_request, patch_request, post_request


class GitHubAPI:
    def __init__(self, inputs):
        self.inputs = inputs
        self.api_url = "/".join(
            ["https://api.github.com", "repos", self.inputs.repository]
        )

    def _assign_labels(self, pr_url):
        url = "/".join([pr_url, "labels"])
        post_request(
            url, headers=self.inputs.headers, json={"labels": self.inputs.labels}
        )

    def _assign_reviewers(self, pr_url):
        url = "/".join([pr_url, "requested_reviewers"])
        post_request(
            url,
            headers=self.inputs.headers,
            json={
                "reviewers": self.inputs.reviewers,
                "team_reviewers": self.inputs.team_reviewers,
            },
        )

    def create_commit(self, commit_msg, content):
        url = "/".join([self.api_url, "contents", self.inputs.config_path])
        body = {
            "message": commit_msg,
            "content": content,
            "sha": self.inputs.sha,
            "branch": self.inputs.head_branch,
        }
        put(url, json=body, headers=self.inputs.headers)

    def create_ref(self, ref, sha):
        url = "/".join([self.api_url, "git", "refs"])
        body = {
            "ref": f"refs/heads/{ref}",
            "sha": sha,
        }
        post_request(url, headers=self.inputs.headers, json=body)

    def create_update_pull_request(self):
        url = "/".join([self.api_url, "pulls"])
        pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"`{image}`: `{self.inputs.image_tags[image]['current']}` -> `{self.inputs.image_tags[image]['latest']}`"
                        for image in self.inputs.images_to_update
                    ]
                )
            ),
            "base": self.inputs.base_branch,
        }

        if self.pr_exists:
            pr["state"] = "open"
            resp = patch_request(
                url, headers=self.inputs.headers, json=pr, return_json=True
            )
        else:
            pr["head"] = self.inputs.head_branch
            resp = post_request(
                url, headers=self.inputs.headers, json=pr, return_json=True
            )

            if self.inputs.labels:
                self._assign_labels(resp["issue_url"])

            if self.inputs.reviewers or self.inputs.team_reviewers:
                self._assign_reviewers(resp["url"])

    def find_existing_pull_request(self):
        url = "/".join([self.api_url, "pulls"])
        params = {"state": "open", "sort": "created", "direction": "desc"}
        resp = get_request(
            url, headers=self.inputs.headers, params=params, output="json"
        )

        head_label_exp = jmespath.compile("[*].head.label")
        matches = head_label_exp.search(resp)
        matches = [label for label in matches if self.inputs.head_branch in label]

        if (len(matches) > 1) or (len(matches) == 1):
            self.inputs.head_branch = matches[0].split(":")[-1]
            self.pr_exists = True
        else:
            random_id = "".join(random.sample(string.ascii_letters, 4))
            self.inputs.head_branch = "-".join([self.inputs.head_branch, random_id])
            self.pr_exists = False

    def get_ref(self, ref):
        url = "/".join([self.api_url, "git", "ref", "heads", ref])
        return get_request(url, headers=self.inputs.headers, output="json")
