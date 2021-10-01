# TODO: Write tests for the following functions:
#       - update_image_tags()
#       - run()
import yaml
import base64

from unittest.mock import patch

from tag_bot.app import edit_config, compare_image_tags

test_url = "http://jsonplaceholder.typicode.com"
test_header = {"Authorization": "token ThIs_Is_A_ToKeN"}


def test_edit_config_singleuser():
    input_images_to_update = ["image_owner/image_name"]
    input_image_tags = {
        "image_owner/image_name": {"current": "image_tag", "latest": "new_image_tag"}
    }

    expected_output = {
        "singleuser": {
            "image": {"name": "image_owner/image_name", "tag": "new_image_tag"},
        }
    }
    expected_output = yaml.safe_dump(expected_output).encode("utf-8")
    expected_output = base64.b64encode(expected_output)
    expected_output = expected_output.decode("utf-8")

    mock_get = patch(
        "tag_bot.app.get_request",
        return_value="""{
            "singleuser": {
                "image": {"name": "image_owner/image_name", "tag": "image_tag"}
            }
        }""",
    )

    with mock_get as mock:
        result = edit_config(
            test_url, test_header, input_images_to_update, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url,
            headers=test_header,
            output="text",
        )
        assert result == expected_output


def test_edit_config_profileList():
    input_images_to_update = ["image_owner/image_name"]
    input_image_tags = {
        "image_owner/image_name": {"current": "image_tag", "latest": "new_image_tag"}
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
    expected_output = yaml.safe_dump(expected_output).encode("utf-8")
    expected_output = base64.b64encode(expected_output)
    expected_output = expected_output.decode("utf-8")

    mock_get = patch(
        "tag_bot.app.get_request",
        return_value="""{
            "singleuser": {
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name:image_tag"
                        }
                    }
                ]
            }
        }""",
    )

    with mock_get as mock:
        result = edit_config(
            test_url, test_header, input_images_to_update, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url,
            headers=test_header,
            output="text",
        )
        assert result == expected_output


def test_edit_config_both():
    input_images_to_update = ["image_owner/image_name1", "image_owner/image_name2"]
    input_image_tags = {
        "image_owner/image_name1": {
            "current": "image_tag1",
            "latest": "new_image_tag1",
        },
        "image_owner/image_name2": {
            "current": "image_tag2",
            "latest": "new_image_tag2",
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
    expected_output = yaml.safe_dump(expected_output).encode("utf-8")
    expected_output = base64.b64encode(expected_output)
    expected_output = expected_output.decode("utf-8")

    mock_get = patch(
        "tag_bot.app.get_request",
        return_value="""{
            "singleuser": {
                "image": {"name": "image_owner/image_name1", "tag": "image_tag1"},
                "profileList": [
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name2:image_tag2"
                        }
                    }
                ]
            }
        }""",
    )

    with mock_get as mock:
        result = edit_config(
            test_url, test_header, input_images_to_update, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url,
            headers=test_header,
            output="text",
        )
        assert result == expected_output


def test_compare_image_tags_match():
    input_image_tags = {
        "image_name": {
            "current": "image_name",
            "latest": "image_name",
        }
    }

    expected_image_names = []

    output_image_names = compare_image_tags(input_image_tags)

    assert output_image_names == expected_image_names


def test_compare_image_tags_no_match():
    input_image_tags = {
        "image_name": {
            "current": "image_name",
            "latest": "new_image_name",
        }
    }

    expected_image_names = ["image_name"]

    output_image_names = compare_image_tags(input_image_tags)

    assert output_image_names == expected_image_names
