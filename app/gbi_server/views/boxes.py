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

import urllib

from sqlalchemy import or_
from werkzeug.exceptions import NotFound, Forbidden
from flask import (render_template, Blueprint, flash,
    redirect, url_for, request, current_app, jsonify)

from flask.ext.babel import gettext as _
from flask.ext.login import current_user, login_required

from gbi_server.config import SystemConfig
from gbi_server.lib.couchdb import CouchFileBox
from gbi_server.lib.file_validation import get_file_information
from gbi_server.model import User

from gbi_server.forms.user import UploadForm, CopyFileForm
boxes = Blueprint("boxes", __name__, template_folder="../templates")

@boxes.route("/box/<box_name>", methods=["GET", "POST"])
@boxes.route("/box/<box_name>/<user_id>", methods=["GET", "POST"])
@login_required
def files(box_name, user_id=None):
    form = UploadForm()
    copy_form = CopyFileForm()
    user = current_user
    if user_id:
        if not current_user.is_consultant:
            raise Forbidden()
        user = User.by_id(user_id)

    couch_box = get_couch_box_db(user, box_name)
    couch = CouchFileBox(current_app.config.get('COUCH_DB_URL'), couch_box)

    if form.validate_on_submit():
        file = request.files['file']
        overwrite = True if request.form.get('overwrite') == 'true' else False
        if file:
            data = get_file_information(file)
            if data:
                couch.store_file(data, overwrite=overwrite)
                flash(_('upload success'), 'success')
            else:
                flash(_('file type not allowed'), 'error')

    files = couch.all_files()
    for f in files:
        f['download_link'] = couchid_to_authproxy_url(f['id'], couch_box=couch_box)

    return render_template("boxes/%s.html" % box_name, form=form, copy_form=copy_form,
        user=user, files=files, box_name=box_name, user_id=user_id)

def couchid_to_authproxy_url(filename, couch_box):
    if isinstance(filename, unicode):
        filename = filename.encode('utf-8')
    return url_for('authproxy.couchdb_proxy_file',
        url=couch_box + '/' + urllib.quote(filename),
    )

def get_couch_box_db(user, box_name):
    if box_name == 'upload':
        return '%s_%s' % (SystemConfig.UPLOAD_BOX_NAME, user.id)
    elif box_name == 'download':
        return '%s_%s' % (SystemConfig.DOWNLOAD_BOX_NAME, user.id)
    elif box_name == 'file':
        return '%s_%s' % (SystemConfig.FILE_BOX_NAME, user.id)
    else:
        raise NotFound()

@boxes.route("/box/<box_name>/<user_id>/check_file", methods=["POST"])
@login_required
def check_file_exists(box_name, user_id):
    user = current_user
    if user_id != str(current_user.id):
        if not current_user.is_consultant:
            raise Forbidden()
        user = User.by_id(user_id)

    couch_box = get_couch_box_db(user, box_name)
    couch = CouchFileBox(current_app.config.get('COUCH_DB_URL'), couch_box)
    existing_doc = couch.get(request.form['filename'])
    if existing_doc:
        return jsonify(existing=True)
    return jsonify(existing=False)

@boxes.route('/box/<box_name>/<user_id>/delete/<id>/<rev>', methods=["GET", "POST"])
@login_required
def delete_file(box_name, id, rev, user_id):
    user = current_user
    if user_id == str(current_user.id):
        user_id = None
    else:
        if not current_user.is_consultant:
            raise Forbidden()
        user = User.by_id(user_id)

    couch_box = get_couch_box_db(user, box_name)
    couch = CouchFileBox(current_app.config.get('COUCH_DB_URL'), couch_box)
    couch.delete(id, rev)
    flash(_("file deleted"), 'success')
    return redirect(url_for("boxes.files", box_name=box_name, user_id=user_id))

@boxes.route('/box/<box_name>/<user_id>/copy/<id>/<rev>', methods=["POST"])
@login_required
def copy_file(box_name, id, rev, user_id):
    user = current_user
    if user_id == str(current_user.id):
        user_id = None
    else:
        if not current_user.is_consultant:
            raise Forbidden()
        user = User.by_id(user_id)

    filename = request.form.get('filename', False)
    if (not filename):
        flash(_("copy not possible"), 'error')
        return redirect(url_for("boxes.files", box_name=box_name, user_id=user_id))

    customer_id = request.form.get('boxes', False)
    if customer_id:
        customer = User.by_id(customer_id)
        user = current_user
        couch_box = get_couch_box_db(user, 'file')
        target_box_name = get_couch_box_db(customer, 'download')
    else:
        customer = current_user
        user = User.by_id(user_id)
        couch_box = get_couch_box_db(user, 'upload')
        target_box_name = get_couch_box_db(customer, 'file')

    user_couch = CouchFileBox(current_app.config.get('COUCH_DB_URL'), couch_box)
    user_couch.copy(id, filename, target_box_name=target_box_name)

    flash(_("file copied"), 'success')
    return redirect(url_for("boxes.files", box_name=box_name, user_id=user_id))


@boxes.route("/box/overview", methods=["GET", "POST"])
@login_required
def overview():
    if current_user.is_consultant:
        users = User.query.filter(or_(User.type == User.Type.CUSTOMER, User.type == User.Type.SERVICE_PROVIDER))
        return render_template("boxes/overview.html", users=users)
    raise Forbidden()
