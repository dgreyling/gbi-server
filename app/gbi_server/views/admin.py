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

from datetime import datetime

from flask import render_template, Blueprint, flash, redirect, \
    url_for, request, current_app, session, Response
from flask.ext.login import current_user
from flask.ext.babel import gettext as _, to_user_timezone

from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy import asc, desc, or_
from geoalchemy2.functions import ST_Envelope, ST_AsGeoJSON

from gbi_server.extensions import db
from gbi_server.model import User, EmailVerification, Log
from gbi_server.forms.admin import CreateUserForm, SearchUserForm, DownloadLogsForm
from gbi_server.forms.user import RecoverSetForm, EditAddressForm
from gbi_server.lib.helper import send_mail
from gbi_server.lib.couchdb import init_user_boxes
from gbi_server.lib.log import log_spec_to_csv

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


@admin.route('/admin/users_list', methods=["GET"])
@admin.route('/admin/users_list/<int:page>', methods=["GET"])
def user_list(page=1):
    form = SearchUserForm(csrf_enabled=False)
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

    search_requests = request.args
    if request.args.get('refresh') and 'search_requests' in session:
        session.pop('search_requests')

    search_request_session = session.get('search_requests')
    if not search_requests and search_request_session:
        search_requests = search_request_session

    if search_requests:
        name = search_requests.get('name', '')
        email = search_requests.get('email', '')
        zipcode_or_city = search_requests.get('zipcode_or_city', '')
        federal_state = search_requests.get('federal_state', False)
        type_ = int(search_requests.get('type', -99))
        company_number = search_requests.get('company_number', '')
        status = search_requests.get('status', False)
        sort_key = search_requests.get('sort_key', False)
        order = search_requests.get('order', 'asc')

        access_start = search_requests.get('access_start', False)
        access_end = search_requests.get('access_end', False)

        # set requests to form fields
        form.name.data = name
        form.email.data = email
        form.zipcode_or_city.data = zipcode_or_city
        form.federal_state.data = federal_state
        form.type.data = type_
        form.company_number.data = company_number
        form.status.data = status
        if access_start:
            form.access_start.data = datetime.strptime(access_start, '%d-%m-%Y')
        if access_end:
            form.access_end.data = datetime.strptime(access_end, '%d-%m-%Y')

        # query user join log for access start and end search options
        query = User.query
        if status:
            query = query.filter(User.active == status)

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
        if email:
            query = query.filter(User.email.like('%'+email+'%'))

        if company_number:
            query = query.filter(User.company_number.like('%'+company_number+'%'))

        if access_start or access_end:
            query = query.join(Log)

        if access_start:
            query = query.filter(Log.time >= access_start)

        if access_end:
            query = query.filter(Log.time < access_end)

        if order == 'asc':
            order_func = asc
        else:
            order_func = desc

        if sort_key == 'lastname':
            query = query.order_by(order_func(User.lastname))

        if sort_key == 'email':
            query = query.order_by(order_func(User.email))

        if sort_key == 'type':
            query = query.order_by(order_func(User.type))

        if sort_key == 'registered':
            query = query.order_by(order_func(User.registered))

        if sort_key == 'zipcode':
            query = query.order_by(order_func(User.zipcode))

        if sort_key == 'status':
            query = query.order_by(order_func(User.active))

        users = query.paginate(page, current_app.config["USER_PER_PAGE"])
    else:
        users = User.query.paginate(page, current_app.config["USER_PER_PAGE"])

    session['search_requests'] = search_requests
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
    return redirect(request.args.get("next") or url_for("admin.inactive_users_list"))


@admin.route('/admin/user/<int:user_id>/deactivate', methods=["GET"])
def deactivate_user(user_id):
    user = User.by_id(user_id)
    user.active = False
    db.session.commit()
    flash(_('User deactivate %(email)s', email=user.email), 'success')
    return redirect(request.args.get("next") or url_for("admin.inactive_users_list"))


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
        return redirect(request.args.get("next") or url_for("admin.inactive_users_list"))

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
    form = RecoverSetForm()
    if form.validate_on_submit():
        user.update_password(form.password.data)
        db.session.commit()
        flash(_('Password reset', username=user.email), 'success')
    return render_template('admin/reset_user_password.html', form=form, user=user)


# @admin.route('/admin/user_log/<int:user_id>', methods=["GET"])
# def user_log(user_id):
#     user = User.by_id(user_id)
#     result = Log.query.filter_by(user=user).all()
#     return render_template('admin/user_log.html', user=user, logs=result)

@admin.route('/admin/logs/', methods=["GET"])
@admin.route('/admin/logs/<int:page>', methods=["GET"])
@admin.route('/admin/user_log/<int:user_id>/logs/', methods=["GET"])
@admin.route('/admin/user_log/<int:page>/logs/<int:user_id>', methods=["GET"])
def logs(page=1, user_id=False):
    form = DownloadLogsForm()

    access_start = request.args.get('access_start', False)
    access_end = request.args.get('access_end', False)

    button_action = request.args.get('button-action', 'show-table')

    query = Log.query
    if user_id:
        user = User.by_id(user_id)
        query = query.filter_by(user=user)

    if access_start:
        query = query.filter(Log.time >= access_start)

    if access_end:
        query = query.filter(Log.time < access_end)

    if button_action == 'show-table':
        results = query.paginate(page, current_app.config["USER_PER_PAGE"])
    else:
        results = query.all()
        csv = log_spec_to_csv(
            logs=results,
            csv_headers=current_app.config['LOG_CSV_HEADER']
        )
        filename = 'geobox-access-%s.csv' % (to_user_timezone(datetime.utcnow()).strftime('%Y%m%d-%H%M%S'))

        resp = Response(
            csv,
            headers={
                'Content-type': 'application/octet-stream',
                'Content-disposition': 'attachment; filename=%s' % filename})

        return resp

    if user_id:
        return render_template('admin/user_log.html', user=user, logs=results)

    # fill forms
    try:
        if access_start:
            form.access_start.data = datetime.strptime(access_start, '%d-%m-%Y')
    except ValueError:
        form.access_start.data = ''

    try:
        if access_end:
            form.access_end.data = datetime.strptime(access_end, '%d-%m-%Y')
    except ValueError:
        form.access_end.data = ''

    return render_template('admin/logs.html', form=form, logs=results)
