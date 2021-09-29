# TODO: Write tests for the following functions:
#       - edit_config()
#       - update_image_tags()
#       - run()

from tag_bot.app import compare_image_tags


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
