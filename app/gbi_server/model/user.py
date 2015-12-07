# This file is part of the GBI project.
# Copyright (C) 2013 Omniscale GmbH & Co. KG <http://omniscale.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bcrypt
import uuid
import datetime

from sqlalchemy import func

from flask import current_app, url_for
from flask.ext.login import UserMixin
from flask.ext.babel import gettext as _

from gbi_server.extensions import db

__all__ = ['User', 'EmailVerification', 'DummyUser']

RECOVER_VALID_FOR = datetime.timedelta(hours=24)

class DummyUser(UserMixin):
    def __init__(self, id):
        self.id = id

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    # login data
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String())

    # address and personal data
    title = db.Column(db.String())
    firstname = db.Column(db.String())
    lastname = db.Column(db.String())
    address = db.Column(db.String())
    address_extend = db.Column(db.String())
    zipcode = db.Column(db.String())
    city = db.Column(db.String())
    federal_state = db.Column(db.String())
    country = db.Column(db.String())
    phone = db.Column(db.String())
    fax = db.Column(db.String())

    company_name = db.Column(db.String())
    company_number = db.Column(db.String())
    commercial_register_number = db.Column(db.String())

    # type from user e.g. customer, consultant etc.
    type = db.Column(db.Integer, default=0)

    # system data
    registered = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_login = db.Column(db.DateTime, default=None)
    active = db.Column(db.Boolean, default=False, nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)
    authproxy_token = db.Column(
        db.String(32),
        unique=True,
        default=lambda: uuid.uuid4().hex
    )

    email_verification = db.relationship(
        'EmailVerification',
        backref='user',
        uselist=False,
        cascade='all,delete,delete-orphan'
    )

    def __init__(self, email, password=None):
        self.email = email
        self.password = None
        if password:
            self.update_password(password)

    class Type(object):
        CUSTOMER = 0 #landwirte
        SERVICE_PROVIDER = 1 #dienstleister
        CONSULTANT = 50 #berater
        ADMIN = 99

        @classmethod
        def as_string(self, type):
            _types = {
                0: _('customer'),
                1: _('service_provider'),
                50: _('consultant'),
                99: _('admin'),
            }
            return _types[type or 0]

    @property
    def type_name(self):
        return self.Type.as_string(self.type)

    @property
    def is_customer(self):
        return True if self.type == self.Type.CUSTOMER else False

    @property
    def is_service_provider(self):
        return True if self.type == self.Type.SERVICE_PROVIDER else False

    @property
    def is_consultant(self):
        return True if self.type == self.Type.CONSULTANT else False

    @property
    def is_admin(self):
        return True if self.type == self.Type.ADMIN else False

    @property
    def realname(self):
        return '%s %s %s' % (self.title_name, self.firstname, self.lastname)

    @property
    def title_name(self):
        salutations = current_app.config['SALUTATIONS']
        for salutation in salutations:
            if salutation[0] == self.title:
                return salutation[1]
        return ''

    @property
    def federal_state_name(self):
        federal_states = current_app.config['FEDERAL_STATES']
        for federal_state in federal_states:
            if federal_state[0] == self.federal_state:
                return federal_state[1]
        return ''

    @classmethod
    def from_dict(cls, data):
        user = User(data['email'], data['password'])
        for name, value in data.iteritems():
            if hasattr(user, name):
                setattr(user, name, value)
        return user

    @classmethod
    def by_email(cls, email):
        q = User.query.filter(func.lower(cls.email) == func.lower(email))
        return q.first()

    @classmethod
    def by_id(cls, id):
        q = User.query.filter(User.id == id)
        return q.first()

    @classmethod
    def by_authproxy_token(cls, authproxy_token):
        q = User.query.filter(User.authproxy_token == authproxy_token)
        return q.first()

    @classmethod
    def all_admins(cls):
        q = cls.query.filter(cls.type == cls.Type.ADMIN)
        return q.all()

    def update_password(self, password):
        if not password:
            raise ValueError("Password must be non empty.")
        password = str(password)

        rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 10)
        self.password = bcrypt.hashpw(password, bcrypt.gensalt(rounds))

    def check_password(self, password):
        if not self.password:
            return False
        return bcrypt.hashpw(password, self.password) == self.password

    def update_last_login(self):
        self.last_login = datetime.datetime.utcnow()

    def is_active(self):
        return self.active

    def get_id(self):
        assert self.id is not None
        return self.id

    def set_user_data(self, data):
        self.title = data['title']
        self.firstname = data['firstname']
        self.lastname = data['lastname']
        self.address = data['address']
        self.address_extend = data['address_extend']
        self.company_name = data['company_name']
        self.zipcode = data['zipcode']
        self.city = data['city']
        self.federal_state = data['federal_state']
        self.phone = data['phone']
        self.fax = data['fax']
        self.company_number = data.get('company_number')
        self.commercial_register_number = data.get('commercial_register_number')

    def __repr__(self):
        return '<User email=%s type=%s>' % (
            self.email, self.type
        )

class EmailVerification(db.Model):
    __tablename__ = 'password_recovery'
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(36), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    valid_till = db.Column(db.DateTime, default=lambda: datetime.datetime.utcnow() + RECOVER_VALID_FOR)

    @classmethod
    def by_hash(cls, hash):
        q = EmailVerification.query.filter(EmailVerification.hash == hash)
        recover = q.first()
        if recover:
            if datetime.datetime.utcnow() < recover.valid_till:
                return recover
            db.session.remove(recover)
            db.session.commit()

    @classmethod
    def recover(cls, user):
        return EmailVerification(user=user, hash=str(uuid.uuid4()), type='recover')

    @classmethod
    def verify(cls, user):
        return EmailVerification(user=user, hash=str(uuid.uuid4()), type='verify')

    @classmethod
    def verify_import(cls, user):
        return EmailVerification(user=user, hash=str(uuid.uuid4()), type='import')

    @property
    def is_recover(self):
        return self.type == 'recover'

    @property
    def is_verify(self):
        return self.type == 'verify'

    @property
    def is_import(self):
        return self.type == 'import'

    @property
    def url(self):
        if self.type == 'recover':
            return url_for('user.recover_password', uuid=self.hash, _external=True)
        if self.type == 'verify':
            return url_for('user.verify', uuid=self.hash, _external=True)
        if self.type == 'import':
            return url_for('user.new_password', uuid=self.hash, _external=True)
        raise AssertionError('unknown verification type: %s', self.type)