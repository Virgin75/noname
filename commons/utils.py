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