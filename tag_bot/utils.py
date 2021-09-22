import requests


def delete_request(url: str, headers: dict = {}) -> None:
    """Send a DELETE request to an HTTP API endpoint

    Args:
        url (str): The URL to send the request to
        headers (dict, optional): A dictionary of any headers to send with the
            request. Defaults to an empty dictionary.
    """
    resp = requests.delete(url, headers=headers)

    if not resp:
        raise RuntimeError(resp.text)


def get_request(
    url: str,
    headers: dict = {},
    params: dict = {},
    output: str = "default",
):
    """Send a GET request to an HTTP API endpoint

    Args:
        url (str): The URL to send the request to
        headers (dict, optional): A dictionary of headers to send with the
            request. Defaults to an empty dict.
        params (dict, optional): A dictionary of parameters to send with the
            request. Defaults to an empty dict.
        output (str): The format in which to output the response in. Currently
            accepts 'default', 'json' or 'text'. 'default' does not apply any
            format parsing of the response.
    """
    accepted_formats = ["default", "json", "text"]
    if output not in accepted_formats:
        raise ValueError(
            "Invalid output format. Please choose one of the following options: %s"
            % accepted_formats
        )

    resp = requests.get(url, headers=headers, params=params)

    if not resp:
        raise RuntimeError(resp.text)

    if output == "default":
        return resp
    elif output == "json":
        return resp.json()
    elif output == "text":
        return resp.text
    else:
        raise NotImplementedError(
            "Requested output format is not yet implemented: %s" % output
        )


def patch_request(
    url: str, headers: dict = {}, json: dict = {}, return_json: bool = False
) -> None:
    """Send a PATCH request to an HTTP API endpoint

    Args:
        url (str): The URL to send the request to
        headers (dict, optional): A dictionary of any headers to send with the
            request. Defaults to {}.
        json (dict, optional): A dictionary containing JSON payload to send with
            the request. Defaults to {}.
        return_json (bool, optional): Return the JSON payload response.
            Defaults to False.
    """
    resp = requests.patch(url, headers=headers, json=json)

    if not resp:
        raise RuntimeError(resp.text)

    if return_json:
        return resp.json()


def post_request(
    url: str, headers: dict = {}, json: dict = {}, return_json: bool = False
) -> None:
    """Send a POST request to an HTTP API endpoint

    Args:
        url (str): The URL to send the request to
        headers (dict, optional): A dictionary of any headers to send with the
            request. Defaults to an empty dictionary.
        json (dict, optional): A dictionary containing JSON payload to send with
            the request. Defaults to an empty dictionary.
        return_json (bool, optional): Return the JSON payload response.
            Defaults to False.
    """
    resp = requests.post(url, headers=headers, json=json)

    if not resp:
        raise RuntimeError(resp.text)

    if return_json:
        return resp.json()