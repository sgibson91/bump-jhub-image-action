import base64
from unittest.mock import patch

import yaml

from tag_bot.git_database import (create_commit, create_ref, get_contents,
                                  get_ref)

test_url = "http://jsonplaceholder.typicode.com"
test_header = {"Authorization": "token ThIs_Is_A_ToKeN"}


def test_create_commit():
    test_path = "config/test_config.yaml"
    test_branch = "test_branch"
    test_sha = "test_sha"
    test_commit_msg = "This is a commit message"

    test_contents = {"key1": "This is a test"}
    test_contents = yaml.safe_dump(test_contents).encode("utf-8")
    test_contents = base64.b64encode(test_contents)
    test_contents = test_contents.decode("utf-8")

    test_body = {
        "message": test_commit_msg,
        "content": test_contents,
        "sha": test_sha,
        "branch": test_branch,
    }

    with patch("tag_bot.git_database.put") as mocked_func:
        create_commit(
            test_url,
            test_header,
            test_path,
            test_branch,
            test_sha,
            test_commit_msg,
            test_contents,
        )

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            "/".join([test_url, "contents", test_path]),
            json=test_body,
            headers=test_header,
        )


def test_create_ref():
    test_ref = "test_ref"
    test_sha = "test_sha"

    test_body = {"ref": f"refs/heads/{test_ref}", "sha": test_sha}

    with patch("tag_bot.git_database.post_request") as mocked_func:
        create_ref(test_url, test_header, test_ref, test_sha)

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            "/".join([test_url, "git", "refs"]),
            headers=test_header,
            json=test_body,
        )


def test_get_contents():
    test_path = "config/test_config.yaml"
    test_ref = "test_ref"
    test_query = {"ref": test_ref}

    mock_get = patch(
        "tag_bot.git_database.get_request",
        return_value={
            "download_url": "/".join([test_url, "download", test_path]),
            "sha": "blob_sha",
        },
    )

    with mock_get as mocked_func:
        resp = get_contents(test_url, test_header, test_path, test_ref)

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            "/".join([test_url, "contents", test_path]),
            headers=test_header,
            params=test_query,
            output="json",
        )
        assert resp == {
            "download_url": "/".join([test_url, "download", test_path]),
            "sha": "blob_sha",
        }


def test_get_ref():
    test_ref = "test_ref"

    mock_get = patch(
        "tag_bot.git_database.get_request", return_value={"object": {"sha": "sha"}}
    )

    with mock_get as mock1:
        resp = get_ref(test_url, test_header, test_ref)

        assert mock1.call_count == 1
        mock1.assert_called_with(
            "/".join([test_url, "git", "ref", "heads", test_ref]),
            headers=test_header,
            output="json",
        )
        assert resp == {"object": {"sha": "sha"}}
