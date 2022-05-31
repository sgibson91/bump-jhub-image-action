import base64
import unittest
from unittest.mock import call, patch

from tag_bot.github_api import GitHubAPI
from tag_bot.main import UpdateImageTags
from tag_bot.yaml_parser import YamlParser

yaml = YamlParser()


class TestGitHubAPI(unittest.TestCase):
    def test_assign_labels(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            labels=["label1", "label2"],
        )
        github = GitHubAPI(main)
        pr_url = "/".join([github.api_url, "pull", "1"])

        with patch("tag_bot.github_api.post_request") as mock:
            github._assign_labels(pr_url)
            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([pr_url, "labels"]),
                headers=main.headers,
                json={"labels": main.labels},
            )

    def test_assign_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            reviewers=["reviewer1", "reviewer2"],
        )
        github = GitHubAPI(main)
        pr_url = "/".join([github.api_url, "pull", "1"])

        with patch("tag_bot.github_api.post_request") as mock:
            github._assign_reviewers(pr_url)
            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([pr_url, "requested_reviewers"]),
                headers=main.headers,
                json={"reviewers": main.reviewers},
            )

    def test_assign_team_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            team_reviewers=["team1", "team2"],
        )
        github = GitHubAPI(main)
        pr_url = "/".join([github.api_url, "pull", "1"])

        with patch("tag_bot.github_api.post_request") as mock:
            github._assign_reviewers(pr_url)
            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([pr_url, "requested_reviewers"]),
                headers=main.headers,
                json={"team_reviewers": main.team_reviewers},
            )

    def test_create_pr_no_labels_no_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        github.pr_exists = False

        main.image_tags = {
            "image_owner/image1": {
                "current": "old_tag",
                "latest": "new_tag",
            },
            "image_owner/image2": {
                "current": "old_tag",
                "latest": "new_tag",
            },
        }
        main.images_to_update = ["image_owner/image1", "image_owner/image2"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": "main",
            "head": "bump-image-tags/config-configyaml",
        }

        with patch("tag_bot.github_api.post_request") as mock:
            github.create_update_pull_request()

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            )

    def test_create_pr_with_labels_no_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            labels=["label1", "label2"],
        )
        github = GitHubAPI(main)
        github.pr_exists = False

        main.image_tags = {
            "image_owner/image1": {
                "current": "old_tag",
                "latest": "new_tag",
            },
            "image_owner/image2": {
                "current": "old_tag",
                "latest": "new_tag",
            },
        }
        main.images_to_update = ["image_owner/image1", "image_owner/image2"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": "main",
            "head": "bump-image-tags/config-configyaml",
        }

        mock_post = patch(
            "tag_bot.github_api.post_request",
            return_value={
                "issue_url": "/".join([github.api_url, "issues", "1"]),
                "number": 1,
            },
        )

        calls = [
            call(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            ),
            call(
                "/".join([github.api_url, "issues", "1", "labels"]),
                headers=main.headers,
                json={"labels": main.labels},
            ),
        ]

        with mock_post as mock:
            github.create_update_pull_request()

            self.assertEqual(mock.call_count, 2)
            self.assertEqual(
                mock.return_value,
                {
                    "issue_url": "/".join([github.api_url, "issues", "1"]),
                    "number": 1,
                },
            )
            mock.assert_has_calls(calls)

    def test_create_update_pr_no_labels_with_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            reviewers=["reviewer1", "reviewer2"],
        )
        github = GitHubAPI(main)
        github.pr_exists = False

        main.image_tags = {
            "image_owner/image1": {
                "current": "old_tag",
                "latest": "new_tag",
            },
            "image_owner/image2": {
                "current": "old_tag",
                "latest": "new_tag",
            },
        }
        main.images_to_update = ["image_owner/image1", "image_owner/image2"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": "main",
            "head": "bump-image-tags/config-configyaml",
        }

        mock_post = patch(
            "tag_bot.github_api.post_request",
            return_value={
                "url": "/".join([github.api_url, "pulls", "1"]),
                "number": 1,
            },
        )

        calls = [
            call(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            ),
            call(
                "/".join([github.api_url, "pulls", "1", "requested_reviewers"]),
                headers=main.headers,
                json={"reviewers": main.reviewers},
            ),
        ]

        with mock_post as mock:
            github.create_update_pull_request()

            self.assertEqual(mock.call_count, 2)
            self.assertEqual(
                mock.return_value,
                {
                    "url": "/".join([github.api_url, "pulls", "1"]),
                    "number": 1,
                },
            )
            mock.assert_has_calls(calls)

    def test_create_update_pr_with_labels_and_reviewers(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            labels=["label1", "label2"],
            reviewers=["reviewer1", "reviewer2"],
        )
        github = GitHubAPI(main)
        github.pr_exists = False

        main.image_tags = {
            "image_owner/image1": {
                "current": "old_tag",
                "latest": "new_tag",
            },
            "image_owner/image2": {
                "current": "old_tag",
                "latest": "new_tag",
            },
        }
        main.images_to_update = ["image_owner/image1", "image_owner/image2"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": "main",
            "head": "bump-image-tags/config-configyaml",
        }

        mock_post = patch(
            "tag_bot.github_api.post_request",
            return_value={
                "issue_url": "/".join([github.api_url, "issues", "1"]),
                "url": "/".join([github.api_url, "pulls", "1"]),
                "number": 1,
            },
        )

        calls = [
            call(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            ),
            call(
                "/".join([github.api_url, "issues", "1", "labels"]),
                headers=main.headers,
                json={"labels": main.labels},
            ),
            call(
                "/".join([github.api_url, "pulls", "1", "requested_reviewers"]),
                headers=main.headers,
                json={"reviewers": main.reviewers},
            ),
        ]

        with mock_post as mock:
            github.create_update_pull_request()

            self.assertEqual(mock.call_count, 3)
            assert mock.return_value == {
                "issue_url": "/".join([github.api_url, "issues", "1"]),
                "url": "/".join([github.api_url, "pulls", "1"]),
                "number": 1,
            }
            mock.assert_has_calls(calls)

    def test_create_pr_fork_exists(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            push_to_users_fork="user",
        )
        github = GitHubAPI(main)
        github.pr_exists = False
        github.fork_exists = True

        main.image_tags = {
            "image_owner/image1": {
                "current": "old_tag",
                "latest": "new_tag",
            },
            "image_owner/image2": {
                "current": "old_tag",
                "latest": "new_tag",
            },
        }
        main.images_to_update = ["image_owner/image1", "image_owner/image2"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": main.base_branch,
            "head": ":".join([main.push_to_users_fork, main.head_branch]),
        }

        with patch("tag_bot.github_api.post_request") as mock:
            github.create_update_pull_request()

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            )

    def test_find_existing_pr_no_matches(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
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
            github.find_existing_pull_request()

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                params={"state": "open", "sort": "created", "direction": "desc"},
                output="json",
            )
            self.assertFalse(github.pr_exists)
            self.assertTrue(
                "/".join(
                    [
                        "bump-image-tags",
                        main.config_path.replace("/", "-").replace(".", ""),
                    ]
                )
                in main.head_branch
            )

    def test_find_existing_pr_match(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        mock_get = patch(
            "tag_bot.github_api.get_request",
            return_value=[
                {
                    "head": {
                        "label": "bump-image-tags/config-configyaml",
                    },
                    "number": 1,
                }
            ],
        )

        with mock_get as mock:
            github.find_existing_pull_request()

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "pulls"]),
                headers=main.headers,
                params={"state": "open", "sort": "created", "direction": "desc"},
                output="json",
            )
            self.assertTrue(github.pr_exists)
            self.assertTrue(
                "/".join(
                    [
                        "bump-image-tags",
                        main.config_path.replace("/", "-").replace(".", ""),
                    ]
                )
                in main.head_branch
            )

    def test_create_commit(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)

        main.sha = "test_sha"
        commit_msg = "This is a commit message"
        contents = {"key1": "This is a test"}

        contents = yaml.object_to_yaml_str(contents).encode("utf-8")
        contents = base64.b64encode(contents).decode("utf-8")

        body = {
            "message": commit_msg,
            "content": contents,
            "sha": main.sha,
            "branch": main.head_branch,
        }

        with patch("tag_bot.github_api.put") as mock:
            github.create_commit(
                commit_msg,
                contents,
            )

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "contents", main.config_path]),
                json=body,
                headers=main.headers,
            )

    def test_create_commit_fork_exists(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            push_to_users_fork="user",
        )
        github = GitHubAPI(main)
        github.fork_exists = True
        github.fork_api_url = "/".join(
            ["https://api.github.com", "repos", main.push_to_users_fork, "octocat"]
        )

        main.sha = "test_sha"
        commit_msg = "This is a commit message"
        contents = {"key1": "This is a test"}

        contents = yaml.object_to_yaml_str(contents).encode("utf-8")
        contents = base64.b64encode(contents).decode("utf-8")

        body = {
            "message": commit_msg,
            "content": contents,
            "sha": main.sha,
            "branch": main.head_branch,
        }

        with patch("tag_bot.github_api.put") as mock:
            github.create_commit(
                commit_msg,
                contents,
            )

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.fork_api_url, "contents", main.config_path]),
                json=body,
                headers=main.headers,
            )

    def test_create_ref(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        test_ref = "test_ref"
        test_sha = "test_sha"

        test_body = {"ref": f"refs/heads/{test_ref}", "sha": test_sha}

        with patch("tag_bot.github_api.post_request") as mock:
            github.create_ref(test_ref, test_sha)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "git", "refs"]),
                headers=main.headers,
                json=test_body,
            )

    def test_create_ref_fork_exists(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            push_to_users_fork="user",
        )
        github = GitHubAPI(main)
        github.fork_exists = True
        github.fork_api_url = "/".join(
            ["https://api.github.com", "repos", main.push_to_users_fork, "octocat"]
        )
        test_ref = "test_ref"
        test_sha = "test_sha"

        test_body = {"ref": f"refs/heads/{test_ref}", "sha": test_sha}

        with patch("tag_bot.github_api.post_request") as mock:
            github.create_ref(test_ref, test_sha)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.fork_api_url, "git", "refs"]),
                headers=main.headers,
                json=test_body,
            )

    def test_get_ref(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        test_ref = "test_ref"

        mock_get = patch(
            "tag_bot.github_api.get_request", return_value={"object": {"sha": "sha"}}
        )

        with mock_get as mock:
            resp = github.get_ref(test_ref)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.api_url, "git", "ref", "heads", test_ref]),
                headers=main.headers,
                output="json",
            )
            self.assertDictEqual(resp, {"object": {"sha": "sha"}})

    def test_get_ref_fork_exists(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "token ThIs_Is_A_ToKeN",
            "config/config.yaml",
            [".singleuser.image"],
            push_to_users_fork="user",
        )
        github = GitHubAPI(main)
        github.fork_exists = True
        github.fork_api_url = "/".join(
            ["https://api.github.com", "repos", main.push_to_users_fork, "octocat"]
        )
        test_ref = "test_ref"

        mock_get = patch(
            "tag_bot.github_api.get_request", return_value={"object": {"sha": "sha"}}
        )

        with mock_get as mock:
            resp = github.get_ref(test_ref)

            self.assertEqual(mock.call_count, 1)
            mock.assert_called_with(
                "/".join([github.fork_api_url, "git", "ref", "heads", test_ref]),
                headers=main.headers,
                output="json",
            )
            self.assertDictEqual(resp, {"object": {"sha": "sha"}})

    def test_check_fork_exists_true(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        main.push_to_users_fork = "user1/octocat"

        mock_get = patch(
            "tag_bot.github_api.get_request",
            return_value=[{"full_name": "user1/octocat"}],
        )

        with mock_get as mock:
            github.check_fork_exists()

            self.assertTrue(github.fork_exists)
            mock.assert_called_with(
                "/".join([github.api_url, "forks"]),
                headers=main.headers,
                output="json",
            )

    def test_check_fork_exists_false(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        main.push_to_users_fork = "user1/octocat"

        mock_get = patch(
            "tag_bot.github_api.get_request",
            return_value=[{"full_name": "user2/octocat"}],
        )

        with mock_get as mock:
            github.check_fork_exists()

            self.assertFalse(github.fork_exists)
            mock.assert_called_with(
                "/".join([github.api_url, "forks"]),
                headers=main.headers,
                output="json",
            )

    def test_create_fork(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
            push_to_users_fork="user1",
        )
        github = GitHubAPI(main)

        mock_post = patch("tag_bot.github_api.post_request")

        with mock_post as mock:
            github.create_fork()

            mock.assert_called_with(
                "/".join([github.api_url, "forks"]),
                headers=main.headers,
            )

    def test_merge_upstream(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        github.fork_api_url = "/".join(
            ["https://api.github.com", "repos", "user", "octocat"]
        )

        mock_post = patch("tag_bot.github_api.post_request")

        with mock_post as mock:
            github.merge_upstream()

            mock.assert_called_with(
                "/".join([github.fork_api_url, "merge-upstream"]),
                headers=main.headers,
                json={"branch": main.base_branch},
            )

    def test_update_existing_pr(self):
        main = UpdateImageTags(
            "octocat/octocat",
            "ThIs_Is_A_t0k3n",
            "config/config.yaml",
            [".singleuser.image"],
        )
        github = GitHubAPI(main)
        github.pr_exists = True
        github.pr_number = 1
        main.image_tags = {"image": {"current": "old_tag", "latest": "new_tag"}}
        main.images_to_update = ["image"]

        expected_pr = {
            "title": "Bumping Docker image tags in JupyterHub config",
            "body": (
                "This Pull Request is bumping the Docker tags for the following images to the listed versions.\n\n"
                + "\n".join(
                    [
                        f"- `{image}`: `{main.image_tags[image]['current']}` -> `{main.image_tags[image]['latest']}`"
                        for image in main.images_to_update
                    ]
                )
            ),
            "base": main.base_branch,
            "state": "open",
        }

        mock_patch = patch(
            "tag_bot.github_api.patch_request", return_value={"number": 1}
        )

        with mock_patch as mock:
            github.create_update_pull_request()

            mock.assert_called_with(
                "/".join([github.api_url, "pulls", str(github.pr_number)]),
                headers=main.headers,
                json=expected_pr,
                return_json=True,
            )
            self.assertEqual(mock.return_value, {"number": 1})


if __name__ == "__main__":
    unittest.main()
