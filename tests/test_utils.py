import pytest

from tag_bot.utils import (
    create_reverse_lookup_dict,
    lookup_key_return_path,
    update_config_with_jq,
)


def test_create_reverse_lookup_dict_simple():
    test_dict = {
        "jupyterhub": {
            "singleuser": {"image": {"name": "image_name", "tag": "image_tag"}}
        }
    }

    expected_output = {
        "image_name": ["jupyterhub", "singleuser", "image", "name"],
        "image_tag": ["jupyterhub", "singleuser", "image", "tag"],
    }

    result = create_reverse_lookup_dict(test_dict)

    assert result == expected_output


def test_create_reverse_lookup_dict_complex():
    test_dict = {
        "jupyterhub": {
            "singleuser": {
                "image": {"name": "image_name", "tag": "image_tag"},
                "profileList": [
                    {"default": True},
                    {"kubespawner_override": {"image": "image_name:image_tag"}},
                    {"kubespawner_override": {"image": "image_name2:image_tag2"}},
                ],
            }
        }
    }

    expected_output = {
        True: ["jupyterhub", "singleuser", "profileList[0]", "default"],
        "image_name": ["jupyterhub", "singleuser", "image", "name"],
        "image_name2:image_tag2": [
            "jupyterhub",
            "singleuser",
            "profileList[2]",
            "kubespawner_override",
            "image",
        ],
        "image_name:image_tag": [
            "jupyterhub",
            "singleuser",
            "profileList[1]",
            "kubespawner_override",
            "image",
        ],
        "image_tag": ["jupyterhub", "singleuser", "image", "tag"],
    }

    result = create_reverse_lookup_dict(test_dict)

    assert result == expected_output


def test_create_reverse_lookup_dict_2i2c_style():
    test_dict = {
        "hubs": [
            {
                "name": "hub1",
                "config": {
                    "jupyterhub": {
                        "singleuser": {
                            "image": {"name": "image_name1", "tag": "image_tag1"},
                            "profileList": [
                                {"default": True},
                                {
                                    "kubespawner_override": {
                                        "image": "image_name2:image_tag2"
                                    }
                                },
                            ],
                        },
                    }
                },
            },
            {
                "name": "hub2",
                "config": {
                    "jupyterhub": {
                        "singleuser": {
                            "image": {"name": "image_name3", "tag": "image_tag3"}
                        }
                    }
                },
            },
        ]
    }

    expected_output = {
        True: [
            "hubs[0]",
            "config",
            "jupyterhub",
            "singleuser",
            "profileList[0]",
            "default",
        ],
        "hub1": ["hubs[0]", "name"],
        "hub2": ["hubs[1]", "name"],
        "image_name1": [
            "hubs[0]",
            "config",
            "jupyterhub",
            "singleuser",
            "image",
            "name",
        ],
        "image_name2:image_tag2": [
            "hubs[0]",
            "config",
            "jupyterhub",
            "singleuser",
            "profileList[1]",
            "kubespawner_override",
            "image",
        ],
        "image_name3": [
            "hubs[1]",
            "config",
            "jupyterhub",
            "singleuser",
            "image",
            "name",
        ],
        "image_tag1": ["hubs[0]", "config", "jupyterhub", "singleuser", "image", "tag"],
        "image_tag3": ["hubs[1]", "config", "jupyterhub", "singleuser", "image", "tag"],
    }

    result = create_reverse_lookup_dict(test_dict)

    assert result == expected_output


def test_lookup_key_return_path_singleuser():
    test_target = "image_name"
    null_target = "something_else"
    test_lookup = {
        "image_name": ["jupyterhub", "singleuser", "image", "name"],
        "image_tag": ["jupyterhub", "singleuser", "image", "tag"],
    }

    expected_output = ["jupyterhub", "singleuser", "image", "tag"]
    expected_output_str = "jupyterhub.singleuser.image.tag"
    expected_output_jq = ".jupyterhub.singleuser.image.tag"

    result = lookup_key_return_path(test_target, test_lookup)
    result_str = lookup_key_return_path(test_target, test_lookup, format="str")
    result_jq = lookup_key_return_path(test_target, test_lookup, format="jq")
    result_null = lookup_key_return_path(null_target, test_lookup)

    assert result == expected_output
    assert result_str == expected_output_str
    assert result_jq == expected_output_jq
    assert result_null is None

    with pytest.raises(ValueError):
        lookup_key_return_path(test_target, test_lookup, format="dict")


def test_lookup_key_return_path_profileList():
    test_target = "image_name:image_tag"
    null_target = "something_else:another_tag"
    test_lookup = {
        True: ["singleuser", "profileList[0]", "default"],
        "image_name:image_tag": [
            "singleuser",
            "profileList[1]",
            "kubespawner_override",
            "image",
        ],
    }

    expected_output = ["singleuser", "profileList[1]", "kubespawner_override", "image"]
    expected_output_str = "singleuser.profileList[1].kubespawner_override.image"
    expected_output_jq = ".singleuser.profileList[1].kubespawner_override.image"

    result = lookup_key_return_path(test_target, test_lookup)
    result_str = lookup_key_return_path(test_target, test_lookup, format="str")
    result_jq = lookup_key_return_path(test_target, test_lookup, format="jq")
    result_null = lookup_key_return_path(null_target, test_lookup)

    assert result == expected_output
    assert result_str == expected_output_str
    assert result_jq == expected_output_jq
    assert result_null is None

    with pytest.raises(ValueError):
        lookup_key_return_path(test_target, test_lookup, format="dict")


def test_update_config_with_jq_singleuser():
    test_config = {"singleuser": {"image": {"name": "image_name", "tag": "old_tag"}}}
    test_image_tags = {"image_name": {"current": "old_tag", "latest": "new_tag"}}

    lookup_config = create_reverse_lookup_dict(test_config)
    tag_path = lookup_key_return_path(
        test_image_tags["image_name"]["current"], lookup_config, format="jq"
    )
    new_config = update_config_with_jq(
        test_config, tag_path, test_image_tags["image_name"]["latest"]
    )

    expected_output = {
        "singleuser": {"image": {"name": "image_name", "tag": "new_tag"}}
    }

    assert new_config == expected_output


def test_update_config_with_jq_profileList():
    test_config = {
        "singleuser": {
            "profileList": [
                {"default": True},
                {"kubespawner_override": {"image": "image_name:old_tag"}},
            ]
        }
    }
    test_image_tags = {"image_name": {"current": "old_tag", "latest": "new_tag"}}
    lookup_config = create_reverse_lookup_dict(test_config)

    target_key = f"image_name:{test_image_tags['image_name']['current']}"
    new_var = f"image_name:{test_image_tags['image_name']['latest']}"

    tag_path = lookup_key_return_path(target_key, lookup_config, format="jq")
    new_config = update_config_with_jq(test_config, tag_path, new_var)

    expected_output = {
        "singleuser": {
            "profileList": [
                {"default": True},
                {"kubespawner_override": {"image": "image_name:new_tag"}},
            ]
        }
    }

    assert new_config == expected_output
