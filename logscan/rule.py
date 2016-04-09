import json
from collections import namedtuple
from base64 import urlsafe_b64decode

Threshold = namedtuple('Threshold', ['min', 'max'])


class Contact:
    def __init__(self, mail, mobile, **kwargs):
        self.mail = mail
        self.mobile = mobile
        self.extra = kwargs

    def dumps(self):
        ret = self.extra.copy()
        ret['mail'] = self.mail
        ret['mobile'] = self.mobile
        return json.dumps(ret)

    @classmethod
    def loads(cls, src):
        return cls(**json.loads(src))


class Rule:
    def __init__(self, filename, name, expression, interval, threshold, order, contacts):
        self.filename = filename
        self.name = name
        self.expression = expression
        self.interval = interval
        self.threshold = threshold
        self.order = order
        self.contacts = contacts

    @classmethod
    def loads(cls, filename, name, src):
        filename = urlsafe_b64decode(filename)
        name = urlsafe_b64decode(name)
        content = json.loads(src)
        contacts = [Contact(**contact) for contact in content.get('contacts', [])]
        # contacts = []
        # for contact in content.get('contacts', []):
        #     contacts.append(Contact(**contact))
        threshold = Threshold(**content['threshold'])
        return cls(filename, name, content['expression'],
                   content['interval'], threshold, content['order'], contacts)
