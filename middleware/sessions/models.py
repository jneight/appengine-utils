# coding=utf-8

import os
from random import randrange
from datetime import datetime
from time import time

from django.utils.hashcompat import md5_constructor
try:
    import json as simplejson
except:
    from django.utils import simplejson
from django.conf import settings
from google.appengine.ext import db
from georemindme import model_plus
from properties import PickleProperty
from geouser.models import User

import UserDict

class _Session_Dict(UserDict.DictMixin):
    _decoded = dict()
    
    @property
    def id(self):
        return None
    
    @classmethod
    def new_session(cls, session_data=None):
        session = _Session_Dict()
        if session_data is not None:
            try:
                session_data = simplejson.loads(session_data)
                session._decoded = session_data
                session['LANGUAGE_CODE'] = session_data.get('LANGUAGE_CODE')
            except:
                pass
        return session
    
    def clear(self):
        '''
            Borra la sesion
        '''
        self._decoded = {}
        
    def __getitem__(self, key):
        return self._decoded[key]
    
    def __setitem__(self, key, value):
        self._decoded[key] = value
        
    def __delitem__(self, key):
        del self._decoded[key]
        
    def keys(self):
        return self._decoded.keys()
        
    def __contains__(self, key):
        try:
            self.__getitem__(key)
        except Exception:
            return False
        return True
   

class _Session_Data(model_plus.Model, _Session_Dict):
    session_data = PickleProperty()
    expires = db.DateTimeProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    _user = db.ReferenceProperty(User, collection_name='session_data')
    _language_code = db.TextProperty()
    remember = db.BooleanProperty(default=False)
    is_from_facebook = db.BooleanProperty(default=False)
    
    @property
    def id(self):
        if self.is_saved():
            return self.key().name()
        return None
    
    
    def decode(self):
        '''
            Obtiene el diccionario pickled
        '''
        if self.session_data is not None:
            self._decoded = self.session_data
        else:
            self._decoded = {}
        
    
    def encode(self):
        '''
            Guarda el diccionario
        '''
        self.session_data = self._decoded
        

    @classmethod        
    def new_session(cls, lang='es', user=None, remember=False, is_from_facebook=False):
        '''
            Crea una nueva sesion, generando un ID unico
        '''
        def _new_session_id():
            '''Genera un nuevo session_id'''
            def _exists_session_id(session_id):
                '''Comprueba que existe el id'''
                if _Session_Data.get_by_key_name(session_id) is not None:
                    return True
                else:
                    return False
            try:
                pid = os.getpid()
            except AttributeError:
                pid = 1
            while 1:
                session_id = 's%s' % md5_constructor("%s%s%s%s"
                                          % (randrange(0, settings.MAX_SESSION_ID), pid, time(),
                                            settings.SECRET_KEY)).hexdigest()
                if not _exists_session_id(session_id):
                    return session_id
        session = _Session_Data(key_name=_new_session_id())
        t = time() + settings.SESSION_COOKIE_AGE
        session.expires = datetime.fromtimestamp(t)
        if lang is not None:
            session['LANGUAGE_CODE'] = lang
        if user is not None:
            session._user = user
        session.remember = remember
        session.is_from_facebook = is_from_facebook
        session.put()
        return session
    
    def is_valid(self):
        if self.expires > datetime.now():
            return True
        else:
            return False
    
    def put(self):
        '''
            Aumenta el tiempo de validez de la sesion
        '''
        t = time() + settings.SESSION_COOKIE_AGE
        self.expires = datetime.fromtimestamp(t)
        self.encode()
        super(model_plus.Model, self).put()

    @classmethod
    def restore_session(cls, session_id):
        '''
            Restaura una sesion
            Comprueba que la fecha sea valida
            
                :params session_id: Identificador de sesion
                :type session_id: :class:`string`
                :returns: :class:`_Session_Data` o None
        '''
        return _Session_Data.get_by_key_name(session_id)
        
    def get_expiry_age(self):
        expires = self.expires - datetime.now()
        return expires.days * 86400 + expires.seconds
    
    def __getitem__(self, key):
        if key.lower()=='user':
            return self._user
        if key.lower()=='language_code':
            return self._language_code
        return self._decoded[key]
    
    def __setitem__(self, key, value):
        if key.lower()=='user':
            self._user = value
        elif key.lower()=='language_code':
            self._language_code = value
        else:
            self._decoded[key] = value
            
    def __contains__(self, key):
        if key.lower()=='user':
            if self._user is None:
                return False
            else:
                return True
        try:
            self.__getitem__(key)
        except KeyError:
            return False
        return True
        