import unittest
from unittest.mock import patch

from tag_bot.main import UpdateImageTags
from tag_bot.parse_image_tags import ImageTags


class TestImageTags(unittest.TestCase):
    def test_get_local_image_tags_singleuser(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [{"values_path": ".singleuser.image"}],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.inputs.config = {
            "singleuser": {
                "image": {
                    "name": "image_owner/image_name",
                    "tag": "image_tag",
                }
            }
        }

        expected_image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "path": ".singleuser.image.tag",
                "regexpr": None,
            }
        }

        image_parser._get_local_image_tags()

        self.assertDictEqual(image_parser.image_tags, expected_image_tags)

    def test_get_deployed_image_tags_profileList(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [{"values_path": ".singleuser.profileList[0].kubespawner_override.image"}],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.inputs.config = {
            "singleuser": {
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name:image_tag"
                        }
                    }
                ]
            }
        }

        expected_image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "path": ".singleuser.profileList[0].kubespawner_override.image",
                "regexpr": None,
            },
        }

        image_parser._get_local_image_tags()

        self.assertDictEqual(image_parser.image_tags, expected_image_tags)

    def test_get_most_recent_image_tags_dockerhub(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.image_tags = {"image_owner/image_name": {"current": "image_tag"}}
        image = "image_owner/image_name"

        expected_image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "latest": "new_image_tag",
            }
        }

        mock_get = patch(
            "tag_bot.parse_image_tags.get_request",
            return_value={
                "results": [
                    {
                        "last_updated": "2021-09-27T16:00:00.000000Z",
                        "name": "latest",
                    },
                    {
                        "last_updated": "2021-09-27T15:59:00.000000Z",
                        "name": "new_image_tag",
                    },
                    {
                        "last_updated": "2021-08-27T16:00:00.000000Z",
                        "name": "some_other_tag",
                    },
                ]
            },
        )

        with mock_get as mock:
            image_parser._get_most_recent_image_tag_dockerhub(image)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join(["https://hub.docker.com/v2/repositories", image, "tags"]),
                output="json",
            )
            self.assertDictEqual(image_parser.image_tags, expected_image_tags)

    def test_get_most_recent_image_tags_quayio(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.image_tags = {"image_owner/image_name": {"current": "image_tag"}}
        image = "image_owner/image_name"

        expected_image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "latest": "new_image_tag",
            }
        }

        mock_get = patch(
            "tag_bot.parse_image_tags.get_request",
            return_value={
                "tags": {
                    "latest": {
                        "last_modified": "Mon, 27 Sep 2021 16:00:00 -0000",
                        "name": "latest",
                    },
                    "new_image_tag": {
                        "last_modified": "Mon, 27 Sep 2021 15:59:00 -0000",
                        "name": "new_image_tag",
                    },
                    "some_other_tag": {
                        "last_modified": "Fri, 27 Aug 2021 16:00:00 -0000",
                        "name": "some_other_tag",
                    },
                }
            },
        )

        with mock_get as mock:
            image_parser._get_most_recent_image_tag_quayio(image)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join(["https://quay.io/api/v1/repository", image]),
                output="json",
            )
            self.assertDictEqual(image_parser.image_tags, expected_image_tags)

    def test_compare_image_tags_match(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.image_tags = {
            "image_name": {
                "current": "image_name",
                "latest": "image_name",
            }
        }

        expected = []

        result = image_parser._compare_image_tags()

        self.assertEqual(result, expected)

    def test_compare_image_tags_no_match(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        image_parser = ImageTags(main, "octocat/octocat", "main")
        image_parser.image_tags = {
            "image_name": {
                "current": "image_name",
                "latest": "new_image_name",
            }
        }

        expected = ["image_name"]

        result = image_parser._compare_image_tags()

        self.assertEqual(result, expected)

    @patch("tag_bot.parse_image_tags.get_request")
    def test_get_config(self, mock_get):
        main = UpdateImageTags(
            "octocat/octocat", "t0k3n", "config/config.yaml", [".singleuser.image"]
        )
        image_parser = ImageTags(main, main.repository, main.base_branch)

        mock_get.side_effect = [
            {
                "download_url": "https://example.com",
                "sha": "123456789",
            },
            "hello: world",
        ]

        expected_config = {"hello": "world"}
        expected_sha = "123456789"

        config, sha = image_parser._get_config(main.base_branch)

        self.assertDictEqual(config, expected_config)
        self.assertEqual(sha, expected_sha)


if __name__ == "__main__":
    unittest.main()
