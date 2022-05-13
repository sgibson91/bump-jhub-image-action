from unittest.mock import patch

from tag_bot.github_api import add_labels, assign_reviewers, create_pr, find_existing_pr

test_url = "http://jsonplaceholder.typicode.com"
test_header = {"Authorization": "token ThIs_Is_A_ToKeN"}


def test_add_labels():
    test_labels = ["label1", "label2"]

    with patch("tag_bot.github_api.post_request") as mocked_func:
        add_labels(test_labels, test_url, test_header)

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            test_url, headers=test_header, json={"labels": test_labels}
        )


def test_assign_reviewers():
    test_reviewers = ["reviewer1", "reviewer2"]

    with patch("tag_bot.github_api.post_request") as mocked_func:
        assign_reviewers(test_reviewers, [], test_url, test_header)

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            "/".join([test_url, "requested_reviewers"]),
            headers=test_header,
            json={"reviewers": test_reviewers, "team_reviewers": []},
        )


def test_create_pr_no_labels_no_reviewers():
    test_base_branch = "main"
    test_head_branch = "head"
    test_labels = []
    test_reviewers = []
    test_team_reviewers = []

    expected_pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": test_base_branch,
        "head": test_head_branch,
    }

    with patch("tag_bot.github_api.post_request") as mocked_func:
        create_pr(
            test_url,
            test_header,
            test_base_branch,
            test_head_branch,
            labels=test_labels,
            reviewers=test_reviewers,
            team_reviewers=test_team_reviewers,
        )

        assert mocked_func.call_count == 1
        mocked_func.assert_called_with(
            "/".join([test_url, "pulls"]),
            headers=test_header,
            json=expected_pr,
            return_json=True,
        )


def test_create_pr_with_labels_no_reviewers():
    test_base_branch = "main"
    test_head_branch = "head"
    test_labels = ["label1", "label2"]
    test_reviewers = []
    test_team_reviewers = []

    expected_pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": test_base_branch,
        "head": test_head_branch,
    }

    mock_post = patch(
        "tag_bot.github_api.post_request",
        return_value={"issue_url": "/".join([test_url, "issues", "1"])},
    )
    mock_labels = patch("tag_bot.github_api.add_labels")

    with mock_post as mock1, mock_labels as mock2:
        create_pr(
            test_url,
            test_header,
            test_base_branch,
            test_head_branch,
            labels=test_labels,
            reviewers=test_reviewers,
            team_reviewers=test_team_reviewers,
        )

        assert mock1.call_count == 1
        assert mock1.return_value == {"issue_url": "/".join([test_url, "issues", "1"])}
        mock1.assert_called_with(
            "/".join([test_url, "pulls"]),
            headers=test_header,
            json=expected_pr,
            return_json=True,
        )
        assert mock2.call_count == 1
        mock2.assert_called_with(
            test_labels, "/".join([test_url, "issues", "1"]), test_header
        )


def test_create_pr_no_labels_with_reviewers():
    test_base_branch = "main"
    test_head_branch = "head"
    test_labels = []
    test_reviewers = ["reviewer1", "reviewer2"]
    test_team_reviewers = []

    expected_pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": test_base_branch,
        "head": test_head_branch,
    }

    mock_post = patch(
        "tag_bot.github_api.post_request",
        return_value={"url": "/".join([test_url, "pulls", "1"])},
    )
    mock_reviewers = patch("tag_bot.github_api.assign_reviewers")

    with mock_post as mock1, mock_reviewers as mock2:
        create_pr(
            test_url,
            test_header,
            test_base_branch,
            test_head_branch,
            labels=test_labels,
            reviewers=test_reviewers,
            team_reviewers=test_team_reviewers,
        )

        assert mock1.call_count == 1
        assert mock1.return_value == {"url": "/".join([test_url, "pulls", "1"])}
        mock1.assert_called_with(
            "/".join([test_url, "pulls"]),
            headers=test_header,
            json=expected_pr,
            return_json=True,
        )
        assert mock2.call_count == 1
        mock2.assert_called_with(
            test_reviewers,
            test_team_reviewers,
            "/".join([test_url, "pulls", "1"]),
            test_header,
        )


def test_create_pr_with_labels_and_reviewers():
    test_base_branch = "main"
    test_head_branch = "head"
    test_labels = ["label1", "label2"]
    test_reviewers = ["reviewer1", "reviewer2"]
    test_team_reviewers = []

    expected_pr = {
        "title": "Bumping Docker image tags",
        "body": "This PR is bumping the Docker image tags for the computational environments to the most recently published",
        "base": test_base_branch,
        "head": test_head_branch,
    }

    mock_post = patch(
        "tag_bot.github_api.post_request",
        return_value={
            "issue_url": "/".join([test_url, "issues", "1"]),
            "url": "/".join([test_url, "pulls", "1"]),
        },
    )
    mock_labels = patch("tag_bot.github_api.add_labels")
    mock_reviewers = patch("tag_bot.github_api.assign_reviewers")

    with mock_post as mock1, mock_labels as mock2, mock_reviewers as mock3:
        create_pr(
            test_url,
            test_header,
            test_base_branch,
            test_head_branch,
            labels=test_labels,
            reviewers=test_reviewers,
            team_reviewers=test_team_reviewers,
        )

        assert mock1.call_count == 1
        assert mock1.return_value == {
            "issue_url": "/".join([test_url, "issues", "1"]),
            "url": "/".join([test_url, "pulls", "1"]),
        }
        mock1.assert_called_with(
            "/".join([test_url, "pulls"]),
            headers=test_header,
            json=expected_pr,
            return_json=True,
        )
        assert mock2.call_count == 1
        mock2.assert_called_with(
            test_labels, "/".join([test_url, "issues", "1"]), test_header
        )
        assert mock3.call_count == 1
        mock3.assert_called_with(
            test_reviewers,
            test_team_reviewers,
            "/".join([test_url, "pulls", "1"]),
            test_header,
        )


def test_find_existing_pr_no_matches():
    mock_get = patch(
        "tag_bot.github_api.get_request",
        return_value=[
            {
                "head": {
                    "label": "some_branch",
                }
            }
        ],
    )

    with mock_get as mock:
        pr_exists, branch_name = find_existing_pr(test_url, test_header)

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url + "/pulls",
            headers=test_header,
            params={"state": "open", "sort": "created", "direction": "desc"},
            output="json",
        )
        assert not pr_exists
        assert branch_name is None


def test_find_existing_pr_one_match():
    mock_get = patch(
        "tag_bot.github_api.get_request",
        return_value=[
            {
                "head": {
                    "label": "bump_image_tags",
                }
            }
        ],
    )

    with mock_get as mock:
        pr_exists, branch_name = find_existing_pr(test_url, test_header)

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url + "/pulls",
            headers=test_header,
            params={"state": "open", "sort": "created", "direction": "desc"},
            output="json",
        )
        assert pr_exists
        assert branch_name == "bump_image_tags"


def test_find_existing_pr_multiple_matches():
    mock_get = patch(
        "tag_bot.github_api.get_request",
        return_value=[
            {
                "head": {
                    "label": "bump_image_tags1",
                }
            },
            {
                "head": {
                    "label": "bump_image_tags2",
                }
            },
        ],
    )

    with mock_get as mock:
        pr_exists, branch_name = find_existing_pr(test_url, test_header)

        assert mock.call_count == 1
        mock.assert_called_with(
            test_url + "/pulls",
            headers=test_header,
            params={"state": "open", "sort": "created", "direction": "desc"},
            output="json",
        )
        assert pr_exists
        assert branch_name == "bump_image_tags1"
