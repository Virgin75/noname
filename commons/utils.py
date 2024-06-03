from django import db


class OpenAndCloseDbConnection:
    """Make sure to close the db connection after the context manager is done."""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        db.connections.close_all()


def get_nested_value(dictionary, keys_str):
    """
    Retrieve a nested value from a dictionary.

    This function takes a dictionary and a string of keys separated by dots, and returns the value at the nested key.
    If the keys do not exist in the dictionary, the function returns None.

    Parameters:
    dictionary (dict): The dictionary from which to retrieve the value.
    keys_str (str): A string of keys separated by dots.

    Returns:
    The value at the nested key if it exists, otherwise None.
    """
    keys = keys_str.split('.')
    for key in keys:
        if isinstance(dictionary, dict):
            dictionary = dictionary.get(key)
        else:
            return None
    return dictionary


import importlib

def call_func_from_str(function_path, *args, **kwargs):
    """
    Call a function from a string path.

    This function takes a string path to a function, imports the module dynamically,
    retrieves the function from the module, and calls it with the provided arguments and keyword arguments.

    Parameters:
    function_path (str): A string path to the function in the format 'module.submodule.function'.
    *args: Variable length argument list to pass to the function.
    **kwargs: Arbitrary keyword arguments to pass to the function.

    Returns:
    The return value of the function call.
    """
    module_path, function_name = function_path.rsplit('.', 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    return function(*args, **kwargs)