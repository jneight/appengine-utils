# coding=utf-8

from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend


class AuthenticateAPIMiddleware(object):
    def process_request(self, request):
        session_key = request.META.get('HTTP_X_GEOREMINDME_SESSION')
        if session_key:
            session_engine = __import__(settings.SESSION_ENGINE, {}, {}, [''])
            session_wrapper = session_engine.SessionStore(session_key)
            session = session_wrapper.load()
            user_id = session_wrapper.get(SESSION_KEY)
            backend_id = session.get(BACKEND_SESSION_KEY)
            if user_id and backend_id:
                auth_backend = load_backend(backend_id)
                user = auth_backend.get_user(user_id)
                if user:
                    request.user = user