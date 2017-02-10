def segment(initials, py_token):
    if len(py_token) == 2:
        return ('_', py_token)
    for initial in initials:
        if py_token.startswith(initial):
            return (initial, py_token.lstrip(initial))
    return ('_', py_token)


def find_finals(initials, py_list):
    return list(set(
        segment(initials, py_token)[1] for py_token in py_list
    ))
