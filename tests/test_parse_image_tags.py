import pytest

from unittest.mock import patch

from tag_bot.parse_image_tags import (
    get_image_tags,
    get_deployed_image_tags,
    get_most_recent_image_tags_dockerhub,
)

test_url = "http://jsonplaceholder.typicode.com"
test_header = {"Authorization": "token ThIs_Is_A_ToKeN"}


def test_get_deployed_image_tags_singleuser():
    branch = "test_branch"
    filepath = "config/test_config.yaml"
    input_image_tags = {}

    expected_image_tags = {"image_owner/image_name": {"current": "image_tag"}}

    mock_get = patch(
        "tag_bot.parse_image_tags.get_request",
        return_value='{"singleuser": {"image": {"name": "image_owner/image_name", "tag": "image_tag"}}}',
    )

    with mock_get as mock:
        output_image_tags = get_deployed_image_tags(
            test_url, test_header, branch, filepath, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            "/".join(
                [
                    test_url,
                    branch,
                    filepath,
                ]
            ),
            headers=test_header,
            output="text",
        )
        assert output_image_tags == expected_image_tags


def test_get_deployed_image_tags_profileList():
    branch = "test_branch"
    filepath = "config/test_config.yaml"
    input_image_tags = {}

    expected_image_tags = {
        "image_owner/image_name1": {"current": "image_tag1"},
        "image_owner/image_name2": {"current": "image_tag2"},
    }

    mock_get = patch(
        "tag_bot.parse_image_tags.get_request",
        return_value="""{
            "singleuser": {
                "image": {"name": "image_owner/image_name1", "tag": "image_tag1"},
                "profileList": [
                    {"default": true},
                    {
                        "kubespawner_override": {
                            "image": "image_owner/image_name2:image_tag2"
                        }
                    },
                ],
            },
        }""",
    )

    with mock_get as mock:
        output_image_tags = get_deployed_image_tags(
            test_url, test_header, branch, filepath, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            "/".join(
                [
                    test_url,
                    branch,
                    filepath,
                ]
            ),
            headers=test_header,
            output="text",
        )
        assert output_image_tags == expected_image_tags


def test_get_most_recent_image_tags_dockerhub():
    image = "image_owner/image_name"
    input_image_tags = {"image_owner/image_name": {"current": "image_tag"}}

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
        output_image_tags = get_most_recent_image_tags_dockerhub(
            image, input_image_tags
        )

        assert mock.call_count == 1
        mock.assert_called_with(
            "/".join(["https://hub.docker.com/v2/repositories", image, "tags"]),
            output="json",
        )
        assert output_image_tags == expected_image_tags


def test_get_image_tags():
    branch = "test_branch"
    filepath = "config/config.yaml"

    mock_deployed_tags = patch(
        "tag_bot.parse_image_tags.get_deployed_image_tags",
        return_value={"image_owner/image_name": {"current": "image_tag"}},
    )
    mock_dockerhub_tags = patch(
        "tag_bot.parse_image_tags.get_most_recent_image_tags_dockerhub",
        return_value={
            "image_owner/image_name": {
                "current": "image_tag",
                "latest": "new_image_tag",
            }
        },
    )

    expected_image_tags = {
        "image_owner/image_name": {
            "current": "image_tag",
            "latest": "new_image_tag",
        }
    }

    with mock_deployed_tags as mock1, mock_dockerhub_tags as mock2:
        image_tags = get_image_tags(test_url, test_header, branch, filepath)

        assert mock1.call_count == 1
        mock1.assert_called_with(
            test_url,
            test_header,
            branch,
            filepath,
            {},
        )
        assert mock2.call_count == 1
        mock2.assert_called_with(
            "image_owner/image_name",
            mock1.return_value,
        )
        assert image_tags == expected_image_tags


def test_get_image_tags_not_implemented_error():
    branch = "test_branch"
    filepath = "config/config.yaml"

    mock_deployed_tags = patch(
        "tag_bot.parse_image_tags.get_deployed_image_tags",
        return_value={"quay.io/image_owner/image_name": {"current": "image_tag"}},
    )

    with mock_deployed_tags as mock1, pytest.raises(NotImplementedError):
        _ = get_image_tags(test_url, test_header, branch, filepath)

        assert mock1.call_count == 1
        mock1.assert_called_with(
            test_url,
            test_header,
            branch,
            filepath,
            {},
        )


def test_get_image_tags_value_error():
    branch = "test_branch"
    filepath = "config/config.yaml"

    mock_deployed_tags = patch(
        "tag_bot.parse_image_tags.get_deployed_image_tags",
        return_value={"image_name": {"current": "image_tag"}},
    )

    with mock_deployed_tags as mock1, pytest.raises(ValueError):
        _ = get_image_tags(test_url, test_header, branch, filepath)

        assert mock1.call_count == 1
        mock1.assert_called_with(
            test_url,
            test_header,
            branch,
            filepath,
            {},
        )
