import os


class NotAGroupWorkspace(Exception):
    pass


def get_gws_root_from_path(path):
    
    """
    Given a path, return the top-level path to the containing GWS.  The 
    path does not have to exist, but the GWS must do so.
    """

    if path.startswith("/gws/"):
        depth = 4

    elif path.startswith("/group_workspaces/"):
        depth = 3

    elif '_USE_TEST_GWS' in os.environ and path.startswith("/tmp/"):
        depth = 2

    else:
        raise NotAGroupWorkspace(path)

    elements = os.path.normpath(path).split("/")
    
    if len(elements) < depth:
        raise NotAGroupWorkspace(path)
    
    gws_path = os.path.join("/", *elements[:depth + 1])

    if not os.path.isdir(gws_path):
        raise NotAGroupWorkspace(path)

    return gws_path
