from tag_bot.utils import create_reverse_lookup_dict, lookup_key_return_path


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


def test_lookup_key_return_path():
    test_target = "image_name"
    null_target = "something_else"
    test_lookup = {
        "image_name": ["jupyterhub", "singleuser", "image", "name"],
        "image_tag": ["jupyterhub", "singleuser", "image", "tag"],
    }

    expected_output = "jupyterhub.singleuser.image.tag"
    expected_output_jq = ".jupyterhub.singleuser.image.tag"

    result = lookup_key_return_path(test_target, test_lookup)
    result_jq = lookup_key_return_path(test_target, test_lookup, jq_format=True)
    result_null = lookup_key_return_path(null_target, test_lookup)

    assert result == expected_output
    assert result_jq == expected_output_jq
    assert result_null is None
