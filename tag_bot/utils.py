from collections import defaultdict
from collections.abc import Mapping
from typing import Dict, Generator, List, Union


def keypaths(nested_dict: Mapping) -> Generator:
    """Traverse a dictionary and map the path of keys for every value

    Args:
        nested_dict (Mapping): The dictionary to traverse

    Yields:
        Generator: A mapping of the keys that lead to a specific value
    """
    for key, value in nested_dict.items():
        if isinstance(value, Mapping):
            for subkey, subvalue in keypaths(value):
                yield [key] + subkey, subvalue
        elif isinstance(value, list):
            for i in range(len(value)):
                for subkey, subvalue in keypaths(value[i]):
                    yield [f"{key}[{str(i)}]"] + subkey, subvalue
        else:
            yield [key], value


def create_reverse_lookup_dict(nested_dict: dict) -> Dict[str, List[str]]:
    """A reverse lookup dictionary: where the values become the keys and
    the list of keys that once represented that specific value are the new
    values

    Args:
        nested_dict (dict): The dictionary to generate a reverse lookup
            dictionary for

    Returns:
        dict: The reverse lookup dictionary
    """
    reverse_dict = defaultdict(list)

    for keypath, value in keypaths(nested_dict):
        reverse_dict[value].extend(keypath)

    return reverse_dict


def lookup_key_return_path(
    target_key: str, lookup_dict: dict, format: str = "list"
) -> Union[str, None]:
    """For a given target in a reverse lookup dict, return the keypath for the
    original dictionary as a string. Optionally format this with a leading "."
    to be compatible with jq commands.

    Args:
        target_key (str): The target key in the lookup dictionary to return the
            keypath for
        lookup_dict (dict): The lookup dictionary to search
        format (str, optional): Select format in which to return the path.
            Accepts values "list" (no formatting), "str" (joins contents of list
            together with "."s) or "jq" (same as "str" but adds a leading "." to
            be compatible with jq commands). Defaults to "list".

    Returns:
        str: The keypath to the desired value in the original dictionary.
            Returns None if the target is not found.
    """
    accepted_formats = ["list", "str", "jq"]
    if format not in accepted_formats:
        raise ValueError(
            f"{format} is not an accepted format! Please use one of: {accepted_formats}"
        )

    if target_key in lookup_dict.keys():
        path_list = lookup_dict[target_key]

        if "singleuser" in path_list:
            path_list[-1] = "tag"

        if format == "list":
            return path_list
        elif format == "str":
            return ".".join(path_list)
        elif format == "jq":
            path_list = [""] + path_list
            return ".".join(path_list)

    else:
        return None
