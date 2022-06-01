import subprocess
import tempfile

from .yaml_parser import YamlParser

yaml = YamlParser()


def update_config_with_yq(config, var_path, new_var):
    """Run a yq command to update a variable in a YAML file given the keypath
    to that variable.

    Args:
        config (dict): The dictionary config to be updated
        var_path (str): The keypath to the variable that should be updated
        new_var (str): The new value to set the variable to

    Returns:
        updated_config (dict): The updated dictionary config
    """
    # Construct the yq command to run
    cmd = ["yq", f'{var_path} = "{new_var}"']

    # Use a temporary file for yq to "read"
    with tempfile.NamedTemporaryFile(mode="r+", suffix=".yaml") as fp:
        # Dump the config to the temp file
        yaml.yaml.dump(config, fp)
        fp.flush()

        # Run the yq command and capture the result
        cmd.append(fp.name)
        call_output = subprocess.check_output(cmd)

    # Cleaning up of the yq output, make sure it is dict format!
    updated_config = yaml.yaml.load(call_output.decode("utf-8").strip("\n"))

    return updated_config


def read_config_with_yq(config: dict, var_path: str):
    """Run a yq command to read a variable in a YAML file given the keypath
    to that variable.

    Args:
        config (dict): The YAML config to be read
        var_path (str): The keypath to the variable that should be read

    Returns:
        (dict or str): The value stored at the provided keypath..
    """
    cmd = ["yq", var_path]

    with tempfile.NamedTemporaryFile(mode="r+", suffix=".yaml") as fp:
        yaml.yaml.dump(config, fp)
        fp.flush()

        cmd.append(fp.name)
        call_output = subprocess.check_output(cmd)

    call_output = call_output.decode("utf-8").strip("\n")
    return yaml.yaml.load(call_output)
