import json
import subprocess
import tempfile


def update_config_with_jq(config, var_path, new_var):
    """Run a jq command to update a variable in a JSON dictionary given the keypath
    to that variable.

    Args:
        config (dict): The dictionary config to be updated
        var_path (str): The keypath to the variable that should be updated
        new_var (str): The new value to set the variable to

    Returns:
        updated_config (dict): The updated dictionary config
    """
    # Construct the jq command to run
    cmd = ["jq", f'{var_path} = "{new_var}"']

    # Use a temporary file for jq to "read"
    with tempfile.NamedTemporaryFile(mode="r+", suffix=".json") as fp:
        # Dump the config to the temp file
        json.dump(config, fp)
        fp.flush()

        # Run the jq command and capture the result
        cmd.append(fp.name)
        call_output = subprocess.check_output(cmd)

    # Cleaning up of the jq output, make sure it is dict format!
    updated_config = json.loads(call_output.decode("utf-8").strip("\n"))

    return updated_config


def read_config_with_jq(config: dict, var_path: str):
    """Run a jq command to read a variable in a JSON dictionary given the keypath
    to that variable.

    Args:
        config (dict): The JSON dictionary config to be read
        var_path (str): The keypath to the variable that should be read

    Returns:
        (dict or str): The value stored at the provided keypath. If it is not a pure
            string, the value will be parsed by a JSON library to return the object.
    """
    cmd = ["jq", "-r", var_path]

    with tempfile.NamedTemporaryFile(mode="r+", suffix=".json") as fp:
        json.dump(config, fp)
        fp.flush()

        cmd.append(fp.name)
        call_output = subprocess.check_output(cmd)

    call_output = call_output.decode("utf-8").strip("\n")

    try:
        return json.loads(call_output)
    except json.JSONDecodeError:
        return call_output
