def params_from_file(filename):
    """
    Returns a dictionary of parameters from a file, or None if empty/not found

    File format is:

    param1 = value1\n
    param2 = value2\n

    With or without spaces around the equals. Leading and trailing characters
    are removed.  Value is stored as a string. Any repeated keys will have a
    number appended to them

    :param filename: Path of file to open
    :type filename: :class:`String`
    :return params: Dictionary of param:value pairs
    :rtype params: :class:`dict`
    """
    params = {}
    try:
        file = open(filename, "r")
        # go through each line extracting params
        for line in file:
            pair = line.split("=")
            key = pair[0].strip()
            value = pair[1].strip()
            params[key] = value
        file.close()
    # catch file not found error
    except FileNotFoundError:
        return None
    # return params
    return params
