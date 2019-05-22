import os
from enum import Enum
import datetime
import re

from util import get_user_login_name


class RequestStatus(Enum):
    CREATING = 0
    NOT_STARTED = 1
    DOING = 2
    DONE = 3
    FAILED = 4
    WITHDRAWN = 5


all_statuses = [v for v in RequestStatus.__members__.values()]


class BadFileName(Exception):
    pass


class BadFileContent(Exception):
    pass


class RequestBase(object):

    def __init__(self, filename, requests_mgr, status, reqid=None):
        self.filename = filename
        self.requests_mgr = requests_mgr
        self.status = status
        if reqid == None:
            _, reqid, _ = self.requests_mgr.parse_filename(self.filename)
            self.reqid = reqid
        else:
            self.reqid = reqid


    def create(self, *args, **kwargs):
        self._write(*args, **kwargs)
        self.set_status(RequestStatus.NOT_STARTED)


    def read(self):
        with open(self._path) as f:
            content = f.read()
        try:
            return self._decode(content)
        except BadFileContent:
            raise BadFileContent('could not parse {}'.format(self._path))


    def dump(self):
        print(self)
        self._dump(self.read())
        print("")


    def set_status(self, new_status):
        self.requests_mgr.move_request_file(
            self.filename, self.status, new_status)
        self.status = new_status


    @property
    def _path(self):
        return self.requests_mgr.get_request_file_path(self.filename,
                                                        self.status)


    def _write(self, *args, **kwargs):
        if self.status != RequestStatus.CREATING:
            raise ValueError('write only permitted in CREATING status')
        content = self._encode(*args, **kwargs)
        with open(self._path, "w") as f:
            f.write(content)
        os.chmod(self._path, 0o644)

    
    def _encode(self):
        raise NotImplementedError


    def _decode(self):
        raise NotImplementedError


    def _get_non_empty_lines(self, content):
        lines = [line.strip() for line in content.split('\n')]
        return [line for line in lines if line]


    def __str__(self):
        user, reqid, date = self.requests_mgr.parse_filename(self.filename)
        return '<{} request: user={} id={} date={} status={}>'.format(
            self.request_type,
            user, reqid, date, 
            self.status.name)


    def __repr__(self):
        return '{}({}, {}, RequestStatus.{})'.format(
            self.__class__.__name__,
            repr(self.filename),
            repr(self.requests_mgr),
            self.status.name)



class MigrateRequest(RequestBase):

    request_type = 'migration'


    def _encode(self, path):
        return '{}\n'.format(path)


    def _decode(self, content):
        lines = self._get_non_empty_lines(content)
        n = len(lines)
        if n == 1:
            path = lines[0]
        else:
            raise BadFileContent
        return {'path': path}


    def _dump(self, d):
        print(" path to migrate: {}".format(d['path']))


class RetrieveRequest(RequestBase):

    request_type = 'retrieval'

    def _encode(self, orig_path, retrieve_path=None):
        if retrieve_path:
            return '{}\n{}\n'.format(orig_path, retrieve_path)
        else:
            return '{}\n'.format(orig_path)
        

    def _decode(self, content):
        lines = self._get_non_empty_lines(content)
        n = len(lines)
        if n == 1:
            orig_path = lines[0]
            new_path = None
        elif n == 2:
            orig_path = lines[0]
            new_path = lines[1]
        else:
            raise BadFileContent
        return {'orig_path': orig_path,
                'new_path': new_path}


    def _dump(self, d):
        print(" original path: {}".format(d['orig_path']))
        new_path = d['new_path']
        if new_path == None:
            print(" restore to original location")
        else:
            print(" restore to {}".format(new_path))




class RequestsManagerBase(object):
    
    def __init__(self, gws_root):
        self.gws_root = gws_root


    @property
    def base_dir(self):
        return os.path.join(self.gws_root, 'mngr')


    def get_dir_for_status(self, status):
        return os.path.join(self.base_dir,
                            self.dir_lookup[status])


    def _create_dir_for_status(self, status):
        path = self.get_dir_for_status(status)
        if not os.path.isdir(path):
            os.makedirs(path)
            os.chmod(path, 0o1777)


    def initialise(self):
        for status in all_statuses:
            self._create_dir_for_status(status)
        if not os.path.exists(self._last_id_path):
            self._write_last_id(0)
        os.chmod(self._last_id_path, 0o666)


    _fn_matcher = re.compile(
        '(?P<user>[^-]+)-(?P<id>[0-9]+)-'
        '(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})$'
        ).match


    def parse_filename(self, filename):
        m = self._fn_matcher(filename)
        if not m:
            raise BadFileName("cannot parse {}".format(filename))
        user = m.group('user')
        reqid = int(m.group('id'))
        date = datetime.date(int(m.group('year')),
                             int(m.group('month')),
                             int(m.group('day')))
        return user, reqid, date


    def make_filename(self, user, reqid, date=None):
        if date == None:
            date = datetime.date.today()
        return "{}-{}-{:04}-{:02}-{:02}".format(user, 
                                                reqid, 
                                                date.year,
                                                date.month,
                                                date.day)


    def withdraw(self, reqid):
        req = self.get_by_id(reqid)

        if req.status != RequestStatus.NOT_STARTED:
            raise Exception(('Withdraw only supported for status NOT_STARTED.'
                             ' Current status = {}').format(req.status.name))
            
        req.set_status(RequestStatus.WITHDRAWN)


    def get_by_id(self, reqid, **kwargs):
        reqs = self.scan(reqid=reqid, **kwargs)
        if len(reqs) != 1:
            raise Exception("did not find exactly 1 matching request")
        return reqs[0]
        

    def scan(self, statuses=None, reqid=None, all_users=False):

        if all_users:
            user = None
        else:
            user = get_user_login_name()

        if statuses == None:
            statuses = [status for status in all_statuses
                        if status.name != 'CREATING']
        
        reqs = []

        for status in statuses:
            dir_path = self.get_dir_for_status(status)
            for filename in os.listdir(dir_path):
                req_user, req_id, req_date = self.parse_filename(filename)
                if reqid != None and req_id != reqid:
                    continue
                if user != None and req_user != user:
                    continue
                request = self._request_class(filename,
                                              self,
                                              status)
                reqs.append(request)

        reqs.sort(key=lambda req: req.reqid)
        return reqs


    def get_request_file_path(self, filename, status):
        return os.path.join(self.get_dir_for_status(status),
                            filename)


    def move_request_file(self, filename, old_status, new_status):
        old_path = self.get_request_file_path(filename, old_status)
        new_path = self.get_request_file_path(filename, new_status)
        os.rename(old_path, new_path)

        
    @property
    def _last_id_path(self):
        return os.path.join(self.base_dir, self.last_id_file)


    def _write_last_id(self, reqid):
        with open(self._last_id_path, "w") as f:
            f.write('{}\n'.format(reqid))


    def _read_last_id(self):
        with open(self._last_id_path) as f:
            last_id = int(f.readline())
        return last_id


    def _get_next_id(self):
        last_id = self._read_last_id()
        next_id = last_id + 1
        self._write_last_id(next_id)
        return next_id


    def create_request(self, *args, **kwargs):
        reqid = self._get_next_id()
        user = get_user_login_name()
        filename = self.make_filename(user, reqid)
        request = self._request_class(filename,
                                      self,
                                      RequestStatus.CREATING,
                                      reqid=reqid)
        request.create(*args, **kwargs)
        return request
        
        
    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            repr(self.gws_root))
      

        
class MigrateRequestsManager(RequestsManagerBase):
    
    dir_lookup = { 
        RequestStatus.CREATING: '.creating_migrate',
        RequestStatus.NOT_STARTED: 'to-migrate',
        RequestStatus.DOING: 'migrating',
        RequestStatus.DONE: 'migrated',
        RequestStatus.FAILED: 'failed-migrations',
        RequestStatus.WITHDRAWN: 'withdrawn-migrations'
        }

    _request_class = MigrateRequest

    last_id_file = '.last_migration_id'


class RetrieveRequestsManager(RequestsManagerBase):

    dir_lookup = {
        RequestStatus.CREATING: '.creating_retrieve',
        RequestStatus.NOT_STARTED: 'to-retrieve',
        RequestStatus.DOING: 'retrieving',
        RequestStatus.DONE: 'retrieved',
        RequestStatus.FAILED: 'failed-retrievals',       
        RequestStatus.WITHDRAWN: 'withdrawn-retrievals'
    }

    _request_class = RetrieveRequest
    
    last_id_file = '.last_retrieval_id'



if __name__ == '__main__':
    
    r = MigrateRequestsManager('/tmp/mygws')
    r.initialise()
    print(r.get_dir_for_status(RequestStatus.NOT_STARTED))

