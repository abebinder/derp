import os
from uuid import uuid1
from pickle import UnpicklingError, dumps, loads
from contextlib import suppress
from flask.sessions import SessionInterface, SessionMixin


class PickleSession(SessionMixin):

    def __init__(self, directory, sid, *args, **kwargs):
        self.path = os.path.join(directory, sid)
        self.directory = directory
        self.sid = sid
        self.read()

    def __getitem__(self, key):
        self.read()
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

    def __delitem__(self, key):
        del self.data[key]
        self.save()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def read(self):
        try:
            with open(self.path, 'rb') as blob:
                self.data = loads(blob.read())
        except (FileNotFoundError, ValueError, EOFError, UnpicklingError):
            self.data = {}

    def save(self):
        new_name = '{}.new'.format(self.path)
        with open(new_name, 'wb') as blob:
            blob.write(dumps(self.data))
        os.rename(new_name, self.path)

class PickleSessionInterface(SessionInterface):
    def __init__(self, directory):
        self.directory = os.path.abspath(directory)
        os.makedirs(self.directory, exist_ok=True)

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name) or '{}-{}'.format(uuid1(), os.getpid())
        return PickleSession(self.directory, sid)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            with suppress(FileNotFoundError):
                os.unlink(session.path)
            response.delete_cookie(app.session_cookie_name, domain=domain)
            return 
        cookie_exp = self.get_expiration_time(app, session)
        response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_exp, httponly=True, domain=domain)
