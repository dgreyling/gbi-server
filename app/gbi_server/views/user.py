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

from werkzeug.exceptions import NotFound
from flask import (
    render_template, Blueprint, flash, redirect, url_for,
    request, current_app, session,
)
from flask.ext.babel import gettext as _
from flask.ext.login import login_user, logout_user, login_required, current_user

from gbi_server.forms.user import (
    LoginForm, NewUserForm, RemoveUserForm, RecoverSetForm,
    EditAddressForm, EditPasswordForm, RecoverRequestForm
)
from gbi_server.extensions import db
from gbi_server.model import User, WMTS, EmailVerification
from gbi_server.lib.helper import send_mail

from gbi_server.lib.couchdb import init_user_boxes

user = Blueprint("user", __name__, template_folder="../templates")


@user.route("/")
def home():
    if current_user.is_anonymous:
        layers = WMTS.query.filter_by(is_public=True).all()
    else:
        layers = WMTS.query.all()
    return render_template('index.html', user=current_user, layers=layers,)


@user.route("/user", methods=["GET"])
@login_required
def index():
    return render_template("user/index.html", user=current_user)


@user.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.by_email(form.data['email'])
        if not user or not user.check_password(form.data['password']):
            flash(_("user or passwort is not correct"), 'error')
            pass # fall through
        elif user and not user.verified:
            return redirect(url_for('.verify_wait', id=user.id))
        elif user and not user.active:
            flash(_("account not activated"), 'error')
        else:
            login_user(user)
            session['authproxy_token'] = user.authproxy_token
            user.update_last_login()
            db.session.commit()
            flash(_("Logged in successfully."), 'success')
            return redirect(request.args.get("next") or url_for(".home"))

    # else: update form with errors
    return render_template("user/login.html", form=form)


@user.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for(".home"))


@user.route("/user/new", methods=["GET", "POST"])
def new():
    form = NewUserForm()
    form.type.choices = []
    form.federal_state.choices = current_app.config['FEDERAL_STATES']
    form.title.choices = current_app.config['SALUTATIONS']

    # add choice wich account types are possible
    if current_app.config['FEATURE_CUSTOMER_USERS']:
        form.type.choices.append((User.Type.CUSTOMER, _('customer')))
    if current_app.config['FEATURE_CONSULTANT_USERS']:
        form.type.choices.append((User.Type.CONSULTANT, _('consultant')))
    form.type.choices.append((User.Type.SERVICE_PROVIDER, _('service_provider')))

    if form.validate_on_submit():
        user = User(form.data['email'], form.data['password'])
        user.set_user_data(form.data)
        user.type = form.data.get('type')

        # no use type will be active automatically all must be activated by an admin
        user.active = False

        # send verifycation mail to check user email
        verify = EmailVerification.verify(user)
        db.session.add(user)
        db.session.add(verify)
        db.session.commit()

        send_mail(
            _("Email verification mail subject"),
            render_template(
                "user/verify_mail.txt",
                user=user,
                verify=verify,
                _external=True
            ),
            [user.email]
        )

        couch_url = current_app.config.get('COUCH_DB_URL')
        if user.is_service_provider or user.is_customer:
            # create couch document and area boxes
            # and initialize security
            init_user_boxes(user, couch_url)

        return redirect(url_for(".verify_wait", id=user.id))

    return render_template(
        "user/new.html",
        form=form,
        customer_id=User.Type.CUSTOMER,
        service_provider_id=User.Type.SERVICE_PROVIDER,
    )


@user.route("/user/remove", methods=["GET", "POST"])
@login_required
def remove():
    form = RemoveUserForm()
    if form.validate_on_submit():
        user = current_user
        db.session.delete(user)
        logout_user()
        db.session.commit()
        flash(_("Account removed"), 'success')
        return redirect(url_for(".home"))
    return render_template("user/remove.html", form=form)


@user.route("/user/<id>/send_verify_mail")
def send_verifymail(id):
    user = User.by_id(id)
    if not user or user.verified:
        raise NotFound()

    verify = EmailVerification.verify(user)
    db.session.add(verify)
    db.session.commit()
    send_mail(
        _("Email verification mail subject"),
        render_template("user/verify_mail.txt", user=user, verify=verify, _external=True),
        [user.email]
    )

    flash(_('email verification was sent successfully'), 'success')
    return redirect(url_for(".login"))


@user.route("/user/<id>/verify_wait")
def verify_wait(id):
    user = User.by_id(id)
    if not user or user.verified:
        raise NotFound()
    return render_template("user/verify_wait.html", user_id=id)


@user.route("/user/<uuid>/verify")
def verify(uuid):
    verify = EmailVerification.by_hash(uuid)
    if not verify or not verify.is_verify:
        return render_template(
            "errors/404.html",
            error_msg=_('infotext verify not possible')
        )

    user = verify.user
    user.verified = True
    db.session.delete(verify)
    db.session.commit()

    send_mail(
        _("Activate user subject"),
        render_template("admin/user_activate_mail.txt", user=user, _external=True),
        [member.email for member in User.all_admins()]
    )

    flash(_("Email verified"), 'success')
    return redirect(url_for(".login"))


@user.route("/user/recover", methods=["GET", "POST"])
def recover():
    form = RecoverRequestForm()
    if form.validate_on_submit():
        user = User.by_email(form.data['email'])
        recover = EmailVerification.recover(user)
        db.session.add(recover)
        db.session.commit()

        send_mail(
            _("Password recover mail subject"),
            render_template("user/recover_mail.txt", user=user, recover=recover),
            [user.email]
        )

        return redirect(url_for(".recover_sent"))
    return render_template("user/recover.html", form=form)


@user.route("/user/recover_sent")
def recover_sent():
    return render_template("user/recover_sent.html")


@user.route("/user/<uuid>/recover", methods=["GET", "POST"], endpoint='recover_password')
@user.route("/user/<uuid>/new", methods=["GET", "POST"], endpoint='new_password')
def recover_new_password(uuid):
    verify = EmailVerification.by_hash(uuid)
    if not verify or not (verify.is_import or verify.is_recover):
        return render_template(
            "errors/404.html",
            error_msg=_('infotext recover not possible')
        )

    user = verify.user
    form = RecoverSetForm()
    if form.validate_on_submit():
        user.update_password(form.data['password'])
        db.session.delete(verify)
        db.session.commit()
        login_user(user)
        return redirect(url_for(".home"))

    return render_template("user/password_set.html", user=user, form=form, verify=verify)


@user.route("/user/edit_address", methods=["GET", "POST"])
@login_required
def edit_address():
    user = current_user
    form = EditAddressForm(request.form, user)
    form.federal_state.choices = current_app.config['FEDERAL_STATES']
    form.title.choices = current_app.config['SALUTATIONS']

    if form.validate_on_submit():
        # save user data to database
        user.set_user_data(form.data)
        db.session.commit()
        flash(_('Address changed'), 'success')
        return redirect(url_for(".edit_address"))
    return render_template("user/edit_address.html", form=form)


@user.route("/user/edit_password", methods=["GET", "POST"])
@login_required
def edit_password():
    user = current_user
    form = EditPasswordForm(request.form)
    if form.validate_on_submit():
        if user.check_password(form.data['old_password']):
            user.update_password(form.data['password'])
            db.session.commit()
            flash(_('Password changed'), 'success')
            return redirect(url_for(".edit_password"))
        else:
            flash(_("Old password is not correct"), 'error')
    return render_template("user/edit_password.html", user=user, form=form)
