from stv_utils import print as cprint


def lprint(
        *values,
        prefix: str = "[INFO]",
        **kwargs
):
    """
    Prints colored messages to the console based on prefix type.

    Args:
        *values: Variable length argument list to print.
        prefix: Message prefix indicating message type. Defaults to "[INFO]".
            Valid options: "[INFO]", "[Warn]", "[Err]".
        **kwargs: Arbitrary keyword arguments passed to the underlying print function.

    Notes:
        - Uses color coding for different message types:
            [INFO]: Green (#AFE1AF)
            [Warn]: Yellow (#E4D00A)
            [Err]: Red (#DC143C)
            Default: Cadet blue (#5F9EA0)
        - Formats output using `cprint` from stv_utils
    """
    info_c = ";#AFE1AF;"
    warn_c = ";#E4D00A;"
    err__c = ";#DC143C;"
    default_c = ";#5F9EA0;"
    match prefix:
        case "[INFO]":
            color = info_c
        case "[Warn]":
            color = warn_c
        case "[Err ]":
            color = err__c
        case _:
            color = default_c
    cprint(color + prefix, *values, **kwargs)