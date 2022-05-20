import warnings
from datetime import datetime
from itertools import compress

from .http_requests import get_request
from .utils import read_config_with_jq
from .yaml_parser import YamlParser

yaml = YamlParser()


class ImageTags:
    def __init__(self, inputs, branch):
        self.inputs = inputs
        self.branch = branch
        self.github_api_url = "/".join(
            ["https://api.github.com", "repos", self.inputs.repository]
        )
        self.image_tags = {}

    def _get_config(self, ref):
        url = "/".join([self.github_api_url, "contents", self.inputs.config_path])
        query = {"ref": ref}
        resp = get_request(url, headers=self.headers, params=query, output="json")

        download_url = resp["download_url"]
        sha = resp["sha"]

        resp = get_request(download_url, headers=self.headers, output="text")
        return yaml.yaml_string_to_object(resp), sha

    def _get_local_image_tags(self):
        for values_path in self.inputs.values_paths:
            value = read_config_with_jq(self.inputs.config, values_path)

            if (
                isinstance(value, dict)
                and ("name" in value.keys())
                and ("tag" in value.keys())
            ):
                path = values_path + ".tag"
                self.image_tags[value["name"]] = {
                    "current": value["tag"],
                    "path": path,
                }
            elif isinstance(value, str):
                name, tag = value.split(":")
                self.image_tags[name] = {"current": tag, "path": values_path}
            else:
                warnings.warn(
                    f"Unknown image definition in path. Skipping for now. {values_path}"
                )
                continue

    def _get_most_recent_image_tag_dockerhub(self, image_name):
        url = "/".join(["https://hub.docker.com/v2/repositories", image_name, "tags"])
        resp = get_request(url, output="json")

        tags_sorted = sorted(resp["results"], key=lambda k: k["last_updated"])

        if tags_sorted[-1]["name"] == "latest":
            latest_tag = tags_sorted[-2]["name"]
        else:
            latest_tag = tags_sorted[-1]["name"]

        self.image_tags[image_name]["latest"] = latest_tag

    def _get_most_recent_image_tag_quayio(self, image_name):
        url = "/".join(["https://quay.io/api/v1/repository", image_name])
        resp = get_request(url, output="json")
        tags = [resp["tags"][key] for key in resp["tags"].keys()]

        for tag in tags:
            tag["last_modified"] = datetime.strptime(
                tag["last_modified"], "%a, %d %b %Y %H:%M:%S %z"
            )

        tags_sorted = sorted(tags, key=lambda k: k["last_modified"])

        if tags_sorted[-1]["name"] == "latest":
            latest_tag = tags_sorted[-2]["name"]
        else:
            latest_tag = tags_sorted[-1]["name"]

        self.image_tags[image_name]["latest"] = latest_tag

    def _get_remote_tags(self):
        for image in self.image_tags.keys():
            if len(image.split("/")) == 2:
                self._get_most_recent_image_tag_dockerhub(image)
            elif len(image.split("/")) > 2:
                if image.split("/")[0] == "quay.io":
                    self._get_most_recent_image_tag_quayio(image)
                else:
                    warnings.warn(
                        f"NotImplemented: Cannot currently retrieve image from {image.split('/')[0]}"
                    )
                    continue
            else:
                warnings.warn(f"UnknownImage: Cannot recognise image {image}")
                continue

    def _compare_image_tags(self):
        cond = [
            self.image_tags[image]["current"] != self.image_tags[image]["latest"]
            for image in self.image_tags.keys()
        ]
        return list(compress(self.image_tags.keys(), cond))

    def get_image_tags(self):
        self.inputs.config, self.inputs.sha = self._get_config()
        self._get_local_image_tags()
        self._get_remote_tags()
        self.inputs.images_to_update = self._compare_image_tags()
        self.inputs.image_tags = self.image_tags
