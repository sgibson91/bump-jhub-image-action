import unittest

from tag_bot.utils import read_config_with_yq, update_config_with_yq


class TestUtilityFunctions(unittest.TestCase):
    def test_read_config_with_yq_singleuser(self):
        var_path = ".singleuser.image"
        config = {"singleuser": {"image": {"name": "my_image", "tag": "my_tag"}}}

        expected_value = {"name": "my_image", "tag": "my_tag"}

        value = read_config_with_yq(config, var_path)

        self.assertDictEqual(value, expected_value)

    def test_read_config_with_yq_profileList(self):
        var_path = ".singleuser.profileList[0].kubespawner_override.image"
        config = {
            "singleuser": {
                "profileList": [{"kubespawner_override": {"image": "owner/name:tag"}}]
            }
        }

        expected_value = "owner/name:tag"

        value = read_config_with_yq(config, var_path)

        self.assertEqual(value, expected_value)

    def test_update_config_with_yq_singleuser(self):
        test_config = {
            "singleuser": {"image": {"name": "image_name", "tag": "old_tag"}}
        }
        test_image_tags = {
            "image_name": {
                "current": "old_tag",
                "latest": "new_tag",
                "path": ".singleuser.image.tag",
            }
        }

        new_config = update_config_with_yq(
            test_config,
            test_image_tags["image_name"]["path"],
            test_image_tags["image_name"]["latest"],
        )

        expected_output = {
            "singleuser": {"image": {"name": "image_name", "tag": "new_tag"}}
        }

        self.assertDictEqual(new_config, expected_output)

    def test_update_config_with_yq_profileList(self):
        test_config = {
            "singleuser": {
                "profileList": [
                    {"kubespawner_override": {"image": "image_name:old_tag"}},
                ]
            }
        }
        test_image_tags = {
            "image_name": {
                "current": "old_tag",
                "latest": "new_tag",
                "path": ".singleuser.profileList[0].kubespawner_override.image",
            }
        }

        new_tag = ":".join(["image_name", test_image_tags["image_name"]["latest"]])
        new_config = update_config_with_yq(
            test_config, test_image_tags["image_name"]["path"], new_tag
        )

        expected_output = {
            "singleuser": {
                "profileList": [
                    {"kubespawner_override": {"image": "image_name:new_tag"}},
                ]
            }
        }

        self.assertDictEqual(new_config, expected_output)


if __name__ == "__main__":
    unittest.main()
