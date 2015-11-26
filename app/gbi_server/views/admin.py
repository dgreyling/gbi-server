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

from flask import render_template, Blueprint, flash, redirect, \
    url_for, request, current_app
from flask.ext.login import current_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy import asc, desc, or_

from gbi_server.extensions import db
from gbi_server.model import User, EmailVerification, Log
from gbi_server.forms.admin import CreateUserForm, SearchUserForm
from gbi_server.forms.user import RecoverSetForm, EditAddressForm
from gbi_server.lib.helper import send_mail
from gbi_server.lib.couchdb import init_user_boxes

admin = Blueprint("admin", __name__, template_folder="../templates")


def assert_admin_user():
    if current_app.config.get('ADMIN_PARTY'):
        return
    if current_user.is_anonymous:
        raise Unauthorized()
    if not current_user.is_admin:
        raise Forbidden()

admin.before_request(assert_admin_user)


@admin.route('/admin')
def index():
    return render_template('admin/index.html')


@admin.route('/admin/users_list', methods=["GET", "POST"])
def user_list():
    form = SearchUserForm()
    form.federal_state.choices = []
    form.federal_state.choices.append(('', ''))
    for state in current_app.config['FEDERAL_STATES']:
        form.federal_state.choices.append(state)

    form.type.choices = []
    form.type.choices.append((-99, ''))
    if current_app.config['FEATURE_CUSTOMER_USERS']:
        form.type.choices.append((User.Type.CUSTOMER, _('customer')))
    form.type.choices.append((User.Type.SERVICE_PROVIDER, _('service_provider')))
    if current_app.config['FEATURE_CONSULTANT_USERS']:
        form.type.choices.append((User.Type.CONSULTANT, _('consultant')))
    form.type.choices.append((User.Type.ADMIN, _('admin')))

    if form.validate_on_submit():
        name = form.data.get('name', False)
        zipcode_or_city = form.data.get('zipcode_or_city', False)
        federal_state = form.data.get('federal_state', False)
        type_ = form.data.get('type', False)
        company_number = form.data.get('company_number', False)
        active = form.data.get('active', False)

        query = User.query
        if type_ != -99:
            query = query.filter(User.type == type_)

        if federal_state:
            query = query.filter(User.federal_state == federal_state)

        if name:
            query = query.filter(or_(
                User.firstname.like('%'+name+'%'),
                User.lastname.like('%'+name+'%'),
            ))

        if zipcode_or_city:
            query = query.filter(or_(
                User.zipcode.like('%'+zipcode_or_city+'%'),
                User.city.like('%'+zipcode_or_city+'%'),
            ))

        if company_number:
            query = query.filter(User.company_number.like('%'+company_number+'%'))

        query = query.filter(User.active == active)
        users = query.all()
    else:
        users = User.query.all()
    return render_template('admin/user_list.html', form=form, users=users)


@admin.route('/admin/users_list/inactive', methods=["GET"])
def inactive_users_list():
    query = User.query.filter(User.active==False)
    users = query.order_by(desc(User.registered)).all()
    return render_template('admin/user_list_inactive.html', users=users)


@admin.route('/admin/user/<int:user_id>/details', methods=["GET", "POST"])
def user_detail(user_id):
    user = User.by_id(user_id)
    return render_template('admin/user_detail.html', user=user)


@admin.route('/admin/user/<int:user_id>/activate', methods=["GET"])
def activate_user(user_id):
    user = User.by_id(user_id)
    user.verified = True
    user.active = True
    db.session.commit()

    send_mail(
        _("Account activated mail subject"),
        render_template("user/activated_mail.txt", user=user, _external=True),
        [user.email]
    )

    flash(_('User activated %(email)s', email=user.email), 'success')
    return redirect(url_for("admin.inactive_users_list"))


@admin.route('/admin/user/<int:user_id>/deactivate', methods=["GET"])
def deactivate_user(user_id):
    user = User.by_id(user_id)
    user.active = False
    db.session.commit()
    flash(_('User deactivate %(email)s', email=user.email), 'success')
    return redirect(url_for("admin.inactive_users_list"))


@admin.route('/admin/user/<int:user_id>/remove', methods=["GET", "POST"])
def remove_user(user_id):
    user = User.by_id(user_id)

    if user == current_user:
        flash(_('Self-User cannot be removed', 'success'))
        return render_template('admin/remove_user.html', user=user)

    if request.method == 'POST':
        email = user.email
        db.session.delete(user)
        db.session.commit()
        flash(_('User was removed %(email)s', email=email), 'success')
        return redirect(url_for("admin.inactive_users_list"))
    return render_template('admin/remove_user.html', user=user)


@admin.route('/admin/create_user', methods=["GET", "POST"])
def create_user():
    form = CreateUserForm()
    form.type.choices = []
    form.federal_state.choices = current_app.config['FEDERAL_STATES']
    form.title.choices = current_app.config['SALUTATIONS']

    if current_app.config['FEATURE_CUSTOMER_USERS']:
        form.type.choices.append((User.Type.CUSTOMER, _('customer')))
    form.type.choices.append((User.Type.SERVICE_PROVIDER, _('service_provider')))
    if current_app.config['FEATURE_CONSULTANT_USERS']:
        form.type.choices.append((User.Type.CONSULTANT, _('consultant')))
    form.type.choices.append((User.Type.ADMIN, _('admin')))

    if form.validate_on_submit():
        user = User(form.data['email'], form.data['password'])
        user.set_user_data(form.data)
        user.type = form.data.get('type')

        if not form.data['verified']:
            verify = EmailVerification.verify(user)
            db.session.add(verify)
            send_mail(
                _("Email verification mail subject"),
                render_template(
                    "user/verify_mail.txt",
                    user=user,
                    verify=verify,
                    _external=True,
                ),
                [user.email]
            )
        else:
            user.verified = True
            if form.data['activate']:
                user.active = True
        db.session.add(user)
        db.session.commit()

        init_user_boxes(user, current_app.config.get('COUCH_DB_URL'))

        flash(_('User created', email=user.email), 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/create_user.html', form=form)


@admin.route('/admin/edit_user/<int:user_id>', methods=["GET", "POST"])
def edit_user(user_id):
    user = User.by_id(user_id)
    form = EditAddressForm(request.form, user)
    form.federal_state.choices = current_app.config['FEDERAL_STATES']
    form.title.choices = current_app.config['SALUTATIONS']
    if form.validate_on_submit():
        user.set_user_data(form.data)
        db.session.commit()
        flash(_('User edited', username=user.email), 'success')
    return render_template('admin/edit_user.html', form=form, user=user)


@admin.route('/admin/reset_user_password/<int:user_id>', methods=["GET", "POST"])
def reset_user_password(user_id):
    user = User.by_id(user_id)
    form = RecoverSetForm()
    if form.validate_on_submit():
        user.update_password(form.password.data)
        db.session.commit()
        flash(_('Password reset', username=user.email), 'success')
    return render_template('admin/reset_user_password.html', form=form, user=user)


@admin.route('/admin/user_log/<int:user_id>', methods=["GET"])
def user_log(user_id):
    user = User.by_id(user_id)
    result = db.session.query(Log, Log.geometry.envelope().wkt).filter_by(user=user).all()
    return render_template('admin/user_log.html', logs=result)

