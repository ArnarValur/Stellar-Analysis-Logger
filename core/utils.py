from typing import Any, Dict, List

def get_by_path(dic: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """Access a multi-level nested dict by a sequence of keys.

    Args:
        dic (Dict[str, Any]): The dict to access
        keys (List[str]): A list of keys to access in sequence
        default (Any, optional): The default value to be returned if the key cannot be found at any level. Defaults to None.

    Returns:
        Any: The value of the nested key
    """
    try:
        for key in keys:
            dic = dic[key]
    except (KeyError, TypeError, AttributeError):
        return default
    return dic
