# codingdb

from google.appengine.ext import db

class BaseManager(object):
    model = None

    def _copy_to_model(self, new_class):
        manager = copy.copy(self)
        manager.model = new_class
        return manager
    
    def all(self):
        return self.model.all()


class MetaModel(type, db.Model):
    objects = None

    def __new__(cls, *args, **kwargs):
        new_class = super(MetaModel, cls).__new__(cls, *args, **kwargs)

        if getattr(new_class, 'objects', None):
            new_class.objects = new_class.objects._copy_to_model(new_class)
        else:
            new_class.objects = BaseManager()._copy_to_model(new_class)

        return new_class


class Model(object):
    __metaclass__ = MetaModel

    def __init__(self, *args, **kwargs):
        return super(self.__class__, self).__init__(*args, **kwargs)

