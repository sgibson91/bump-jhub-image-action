import base64
import filecmp
import unittest
from collections import OrderedDict

from tag_bot.yaml_parser import YamlParser


class TestYamlParser(unittest.TestCase):
    def test_object_to_yaml_str(self):
        yaml = YamlParser()
        result = yaml.object_to_yaml_str({"hello": "world"})
        self.assertEqual(result, "hello: world\n")

    def test_yaml_str_to_object(self):
        yaml = YamlParser()
        result = yaml.yaml_string_to_object("hello: world")
        self.assertEqual(result, {"hello": "world"})

    def test_round_trip(self):
        yaml = YamlParser()

        with open("tests/assets/test.yaml") as stream:
            test_yaml = yaml.yaml.load(stream)

        test_yaml_str = yaml.object_to_yaml_str(test_yaml)
        test_yaml_back_to_obj = yaml.yaml_string_to_object(test_yaml_str)

        with open("tests/assets/test_output.yaml", "w") as fp:
            yaml.yaml.dump(test_yaml_back_to_obj, fp)

        expected_yaml_string = (
            '# This is a block comment\nhello: "world"  # This is an inline comment\n'
        )
        expected_yaml_obj = OrderedDict()
        expected_yaml_obj["hello"] = "world"

        self.assertEqual(test_yaml_str, expected_yaml_string)
        self.assertDictEqual(test_yaml_back_to_obj, expected_yaml_obj)
        self.assertTrue(
            filecmp.cmp(
                "tests/assets/test.yaml", "tests/assets/test_output.yaml", shallow=False
            )
        )

    def test_round_trip_complex(self):
        yaml = YamlParser()

        with open("tests/assets/test_complex.yaml") as stream:
            test_yaml = yaml.yaml.load(stream)

        test_yaml_str = yaml.object_to_yaml_str(test_yaml)
        test_yaml_back_to_obj = yaml.yaml_string_to_object(test_yaml_str)

        with open("tests/assets/test_complex_output.yaml", "w") as fp:
            yaml.yaml.dump(test_yaml_back_to_obj, fp)

        expected_yaml_string = '# This is a block comment\nhello: "world"  # This is an inline comment\nthis:\n  is: "a"\n  test:\n    - "hello"\n    - "world"\n'
        expected_yaml_obj = OrderedDict()
        expected_yaml_obj["hello"] = "world"
        expected_yaml_obj["this"] = OrderedDict()
        expected_yaml_obj["this"]["is"] = "a"
        expected_yaml_obj["this"]["test"] = ["hello", "world"]

        self.assertEqual(test_yaml_str, expected_yaml_string)
        self.assertDictEqual(test_yaml_back_to_obj, expected_yaml_obj)
        self.assertTrue(
            filecmp.cmp(
                "tests/assets/test_complex.yaml",
                "tests/assets/test_complex_output.yaml",
                shallow=False,
            )
        )

    def test_round_trip_encoded(self):
        yaml = YamlParser()

        with open("tests/assets/test.yaml") as stream:
            config = yaml.yaml.load(stream)

        # Encode the config
        encoded_config = yaml.object_to_yaml_str(config).encode("utf-8")
        encoded_config = base64.b64encode(encoded_config).decode("utf-8")

        # Reverse the encoding process
        decoded_config = base64.b64decode(encoded_config.encode("utf-8"))
        decoded_config = yaml.yaml_string_to_object(decoded_config.decode("utf-8"))

        with open("tests/assets/test_encoded_output.yaml", "w") as fp:
            yaml.yaml.dump(decoded_config, fp)

        self.assertDictEqual(config, decoded_config)
        self.assertTrue(
            filecmp.cmp(
                "tests/assets/test.yaml",
                "tests/assets/test_encoded_output.yaml",
                shallow=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
