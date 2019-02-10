import pwd
import grp
import os


class UserPermissionsChecker(object):

    def __init__(self, username):

        self.username = username
        self.uid, gid = self._get_uid_gid(username)
        self.gids = [gid] + self._get_supplementary_gids(username)

        self.clear_cache()

    
    def clear_cache(self):
        self._cache = {}
        

    def _get_uid_gid(self, username):
        p = pwd.getpwnam(username)
        return p.pw_uid, p.pw_gid


    def _get_supplementary_gids(self, username):
        return [g.gr_gid for g in grp.getgrall()
                if username in g.gr_mem]


    _perm_codes = {"r": 4, "w": 2, "x": 1}

    def _perm_str_to_int(self, s):
        val = 0
        for c in str(s):
            try:
                val |= self._perm_codes[c]
            except KeyError:
                raise ValueError('invalid character {} in access string'.format(s))
        return val
        

    def _perm_int_to_str(self, val):
        s = ""
        for c in "rwx":
            if val & self._perm_codes[c]:
                s += c
        return s

    
    def _abs_path(self, start_dir, path):
        if path.startswith("/"):
            return path
        else:
            return os.path.normpath(os.path.join(start_dir, path))


    def check_access(self, path, access, continue_on_error=False,
                     **kwargs):
        """
        Checks if the user can access a given path with the required level of 
        access.  Raise an exception if not.

        Access can be an integer (0-7) which corresponds to the required access,
        or a string such as "r", "rx", "rw" (integer values 4, 5, 6 respectively)

        If check_dir_access is set to True, then it will check that there is at 
        least execute permission on the parent directories.

        If a list is passed in as 'messages', then on finding a
        permissions error, a message will be appended to the list.

        If a list is passed in as 'permissions', then on finding a
        permissions error, a 2-tuple (path, stat_data) will be
        appended to the list.

        If continue_on_error=True, then on finding a permissions
        error, instead of raising an exception, the processing will
        continue scanning parent directories.  (Other exceptions are
        not affected.)
        """
        if isinstance(access, int):
            if not 0 <= access <= 7:
                raise ValueError('access integer out of range')
        elif isinstance(access, str):
            access = self._perm_str_to_int(access)
        else:
            raise ValueError('access has invalid type')

        if not path.startswith("/"):
            path = self._abs_path(os.getcwd(), path)

        cache_key = (access, path)
        if cache_key not in self._cache:
            self._cache[cache_key] = self._check_access(path, access, 
                                                        continue_on_error=continue_on_error,
                                                        **kwargs)

        ret_val = self._cache[cache_key]
        
        if (not continue_on_error) and (ret_val == False):
            raise Exception(("permissions error affecting {} "
                             "(cached result - see earlier message for details)"
                             ).format(path))

        return ret_val


    def _check_access(self, path, access, check_dir_access=True, 
                      messages=None, permissions=None,
                      continue_on_error=False):


        errors = False

        s = os.stat(path)
        uid = s.st_uid
        gid = s.st_gid
        mode = s.st_mode

        # extract the relevant permission bits
        if uid == self.uid:
            perm = (mode >> 6) & 7
            perm_type = "user"
        elif gid in self.gids:
            perm = (mode >> 3) & 7
            perm_type = "group"
        else:
            perm = mode & 7
            perm_type = "world"

        if perm & access != access:

            tmpl = ("missing permissions:\n"
                    "   on {}\n"
                    "   user '{}' does not have '{}' permission"
                    " (current permissions for {} are '{}')\n")
            message = tmpl.format(path,
                                  self.username, 
                                  self._perm_int_to_str(access),
                                  perm_type,
                                  self._perm_int_to_str(perm) or "(none)")
            errors = True
            if isinstance(messages, list):
                messages.append(message)

            if isinstance(permissions, list):
                permissions.append((path, s))

            if not continue_on_error:
                raise Exception(message)

        recurse = []
        if check_dir_access and path != "/":
            parent = os.path.dirname(path)
            recurse.append(parent)
        
            if os.path.islink(path):

                path2 = self._abs_path(parent, os.readlink(path))
                parent2 = os.path.dirname(path2)
                recurse.append(parent2)

        for d in recurse:
            if not self.check_access(d, "x",
                                     messages=messages,
                                     permissions=permissions,
                                     continue_on_error=continue_on_error):
                errors = True
                                
        return not errors


if __name__ == '__main__':

    upc = UserPermissionsChecker('nobody')
    
    
    f1 = '/badc/cmip6/data/CMIP6/CMIP/CNRM-CERFACS/CNRM-CM6-1/amip/r1i1p1f2/Amon/rsus/gr/v20181203/rsus_Amon_CNRM-CM6-1_amip_r1i1p1f2_gr_197901-201412.nc'
    f2 = '/badc/cmip5/data/cmip5/output1/NICAM/NICAM-09/aquaControl/mon/atmos/cfMon/r1i1p1/latest/hus/hus_cfMon_NICAM-09_aquaControl_r1i1p1_000001-000003.nc'
    for f in [
        f1, f2, f1, f2 ]:

        messages = []
        permissions = []
        print(f, upc.check_access(f, 'r', 
                                  messages=messages, permissions=permissions,
                                  continue_on_error=True))
        [print(m) for m in messages]
        [print("{:o} {}".format(s.st_mode, p)) for p, s in permissions]


    print(upc.check_access(f2, 'r'))
