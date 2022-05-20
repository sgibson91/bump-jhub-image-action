from tag_bot.utils import update_config_with_jq


def test_update_config_with_jq_singleuser():
    test_config = {"singleuser": {"image": {"name": "image_name", "tag": "old_tag"}}}
    test_image_tags = {
        "image_name": {
            "current": "old_tag",
            "latest": "new_tag",
            "path": ".singleuser.image.tag",
        }
    }

    new_config = update_config_with_jq(
        test_config,
        test_image_tags["image_name"]["path"],
        test_image_tags["image_name"]["latest"],
    )

    expected_output = {
        "singleuser": {"image": {"name": "image_name", "tag": "new_tag"}}
    }

    assert new_config == expected_output


def test_update_config_with_jq_profileList():
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
    new_config = update_config_with_jq(
        test_config, test_image_tags["image_name"]["path"], new_tag
    )

    expected_output = {
        "singleuser": {
            "profileList": [
                {"kubespawner_override": {"image": "image_name:new_tag"}},
            ]
        }
    }

    assert new_config == expected_output
