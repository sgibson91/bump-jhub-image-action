import base64
import unittest

from tag_bot.main import UpdateImageTags, split_str_to_list
from tag_bot.yaml_parser import YamlParser

yaml = YamlParser()


class TestUpdateImageTags(unittest.TestCase):
    def test_update_config_singleuser(self):
        update_images = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        update_images.config = {
            "singleuser": {
                "image": {"name": "image_owner/image_name", "tag": "image_tag"}
            }
        }
        update_images.images_to_update = ["image_owner/image_name"]
        update_images.image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "latest": "new_image_tag",
                "path": ".singleuser.image.tag",
            }
        }

        expected_output = {
            "singleuser": {
                "image": {"name": "image_owner/image_name", "tag": "new_image_tag"},
            }
        }
        expected_output = yaml.object_to_yaml_str(expected_output).encode("utf-8")
        expected_output = base64.b64encode(expected_output)
        expected_output = expected_output.decode("utf-8")

        result = update_images.update_config()

        self.assertEqual(result, expected_output)

    def test_update_config_profileList(self):
        update_images = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.profileList[0].kubespawner_override.image"],
        )
        update_images.config = {
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
        update_images.images_to_update = ["image_owner/image_name"]
        update_images.image_tags = {
            "image_owner/image_name": {
                "current": "image_tag",
                "latest": "new_image_tag",
                "path": ".singleuser.profileList[0].kubespawner_override.image",
            }
        }

        expected_output = {
            "singleuser": {
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name:new_image_tag"
                        }
                    }
                ]
            }
        }
        expected_output = yaml.object_to_yaml_str(expected_output).encode("utf-8")
        expected_output = base64.b64encode(expected_output)
        expected_output = expected_output.decode("utf-8")

        result = update_images.update_config()

        self.assertEqual(result, expected_output)

    def test_update_config_both(self):
        update_images = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [
                ".singleuser.image",
                ".singleuser.profileList[0].kubespawner_override.image",
            ],
        )
        update_images.config = {
            "singleuser": {
                "image": {"name": "image_owner/image_name1", "tag": "image_tag1"},
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name2:image_tag2"
                        }
                    }
                ],
            }
        }
        update_images.images_to_update = [
            "image_owner/image_name1",
            "image_owner/image_name2",
        ]
        update_images.image_tags = {
            "image_owner/image_name1": {
                "current": "image_tag1",
                "latest": "new_image_tag1",
                "path": ".singleuser.image.tag",
            },
            "image_owner/image_name2": {
                "current": "image_tag2",
                "latest": "new_image_tag2",
                "path": ".singleuser.profileList[0].kubespawner_override.image",
            },
        }

        expected_output = {
            "singleuser": {
                "image": {"name": "image_owner/image_name1", "tag": "new_image_tag1"},
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name2:new_image_tag2"
                        }
                    }
                ],
            }
        }
        expected_output = yaml.object_to_yaml_str(expected_output).encode("utf-8")
        expected_output = base64.b64encode(expected_output)
        expected_output = expected_output.decode("utf-8")

        result = update_images.update_config()

        self.assertEqual(result, expected_output)


def test_split_str_to_list_simple():
    test_str1 = "label1,label2"
    test_str2 = "label1 , label2"

    expected_output = ["label1", "label2"]

    result1 = split_str_to_list(test_str1, split_char=",")
    result2 = split_str_to_list(test_str2, split_char=",")

    assert result1 == expected_output
    assert result2 == expected_output
    assert result1 == result2


def test_split_str_to_list_complex():
    test_str1 = "type: feature,impact: low"
    test_str2 = "type: feature , impact: low"

    expected_output = ["type: feature", "impact: low"]

    result1 = split_str_to_list(test_str1, split_char=",")
    result2 = split_str_to_list(test_str2, split_char=",")

    assert result1 == expected_output
    assert result2 == expected_output
    assert result1 == result2


if __name__ == "__main__":
    unittest.main()
