import os
import pwd

import ceda_cmip6_tools.config as config


def get_user_name():
    "get a user name (to use as the requester)"
    name = pwd.getpwuid(os.getuid()).pw_gecos
    return name[: config.max_requester_len]



