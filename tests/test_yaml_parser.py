import unittest

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


if __name__ == "__main__":
    unittest.main()
