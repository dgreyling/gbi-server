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

from sqlalchemy import or_

from wtforms.fields import TextField, PasswordField, SelectField, BooleanField, FileField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import validators
from flask.ext.babel import lazy_gettext as _l
from .base import Form

from .validator import username_unique, username_exists, check_password_length
from gbi_server.model import User


def query_all_user_boxes():
     users = User.query.filter(or_(User.type == User.Type.CUSTOMER, User.type == User.Type.SERVICE_PROVIDER)).all()
     return users

class LoginForm(Form):
    email = TextField(_l('email'), [validators.Required(), validators.Email()])
    password = PasswordField(_l('password'), [validators.Required()])

class EditAddressForm(Form):
    florlp_name = TextField(_l('florlp_username'), [username_unique])
    realname = TextField(_l('realname'), [validators.Required()])
    street = TextField(_l('street'), [validators.Required()])
    housenumber = TextField(_l('housenumber'), [validators.Required()])
    zipcode = TextField(_l('zipcode'), [validators.Required(), validators.Regexp('[0-9]+$')])
    city = TextField(_l('city'), [validators.Required()])

class NewUserForm(EditAddressForm):
    florlp_password = PasswordField(_l('florlp_password'))
    type = SelectField(_l('type'), coerce=int)
    email = TextField(_l('email'), [validators.Required(), username_unique, validators.Email()])
    password = PasswordField(_l('password'), [
        validators.Required(),
        validators.EqualTo('password2', message=_l("Passwords must match")),
        check_password_length])
    password2 = PasswordField(_l('password repeat'))
    terms_of_use = BooleanField(_l('terms of use'), [validators.Required()])

class RemoveUserForm(Form):
    password = PasswordField(_l('password'), [validators.Required()])

class RecoverRequestForm(Form):
    email = TextField(_l('email'), [validators.Required(), username_exists, validators.Email()])

class RecoverSetForm(Form):
    password = PasswordField(_l('password'), [
        validators.Required(),
        validators.EqualTo('password2', message=_l("Passwords must match")),
        check_password_length])
    password2 = PasswordField(_l('password repeat'))

class EditPasswordForm(RecoverSetForm):
    old_password = PasswordField(_l('old password'), [validators.Required()])

class RefreshFlorlpForm(Form):
    password = PasswordField(_l('password'), [validators.Required()])

class UploadForm(Form):
    file = FileField(_l('file'), [validators.Required()])
    overwrite = HiddenField('overwrite', default=False)

class CopyFileForm(Form):
    filename = TextField(_l('filename'), [validators.Required()])
    boxes = QuerySelectField(_l('select target user'), [validators.Required()], query_factory=query_all_user_boxes, get_label='email')

