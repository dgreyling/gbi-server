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

from flask import render_template, Blueprint, flash, redirect, url_for, request, current_app, session, jsonify
from flask.ext.login import current_user, login_user
from flask.ext.babel import gettext as _
from werkzeug.exceptions import Unauthorized, Forbidden
from sqlalchemy.exc import IntegrityError

from geoalchemy import WKTSpatialElement
from geoalchemy.postgis import pg_functions
from shapely.geometry import asShape, box

from json import loads

from gbi_server.extensions import db
from gbi_server.model import User, EmailVerification, Log, WMTS, WMS, WFS
from gbi_server.forms.admin import CreateUserForm, WMTSForm, WMSForm, WFSForm
from gbi_server.forms.user import RecoverSetForm, EditAddressForm
from gbi_server.lib.helper import send_mail
from gbi_server.lib.couchdb import init_user_boxes
from gbi_server.lib.external_wms import write_mapproxy_config
from gbi_server.lib.capabilites import parse_capabilities_url
from gbi_server.lib.transform import transform_bbox

admin = Blueprint("admin", __name__, template_folder="../templates")

def assert_admin_user():
    if current_app.config.get('ADMIN_PARTY'):
        return
    if current_user.is_anonymous():
        raise Unauthorized()
    if not current_user.is_admin:
        raise Forbidden()

admin.before_request(assert_admin_user)

@admin.route('/admin')
def index():
    return render_template('admin/index.html')

@admin.route('/admin/user_list', methods=["GET"])
def user_list():
    return render_template('admin/user_list.html', users=User.query.all())

@admin.route('/admin/user_detail/<int:id>', methods=["GET", "POST"])
def user_detail(id):
    user = User.by_id(id)
    return render_template('admin/user_detail.html', user=user)

@admin.route('/admin/verify_user/<int:id>', methods=["GET"])
def verify_user(id):
    user = User.by_id(id)
    user.verified = True
    db.session.commit()
    flash(_('User verified', email=user.email), 'success')
    return redirect(url_for("admin.user_detail", id=id))


@admin.route('/admin/login_as/<int:id>', methods=["GET"])
def loging_as(id):
    user = User.by_id(id)
    login_user(user)
    session['authproxy_token'] = user.authproxy_token
    return redirect(url_for("user.home"))

@admin.route('/admin/activate_user/<int:id>', methods=["GET"])
def activate_user(id):
    user = User.by_id(id)
    user.active = True
    db.session.commit()

    send_mail(
        _("Account activated mail subject"),
        render_template("user/activated_mail.txt", user=user, _external=True),
        [user.email]
    )

    flash(_('User activated', email=user.email), 'success')
    return redirect(url_for("admin.user_detail", id=id))

@admin.route('/admin/create_user', methods=["GET", "POST"])
def create_user():
    form = CreateUserForm()
    form.type.choices = []
    if current_app.config['FEATURE_CUSTOMER_USERS']:
        form.type.choices.append((User.Type.CUSTOMER, _('customer')))
    form.type.choices.append((User.Type.SERVICE_PROVIDER, _('service_provider')))
    if current_app.config['FEATURE_CONSULTANT_USERS']:
        form.type.choices.append((User.Type.CONSULTANT, _('consultant')))
    form.type.choices.append((User.Type.ADMIN, _('admin')))

    if form.validate_on_submit():
        user = User(form.data['email'], form.data['password'])
        user.realname = form.data['realname']
        user.florlp_name = form.data['florlp_name']
        user.type = form.data.get('type')
        user.street = form.data['street']
        user.housenumber =  form.data['housenumber']
        user.zipcode = form.data['zipcode']
        user.city = form.data['city']
        if not form.data['verified']:
            verify = EmailVerification.verify(user)
            db.session.add(verify)
            send_mail(
                _("Email verification mail subject"),
                render_template("user/verify_mail.txt", user=user, verify=verify, _external=True),
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

@admin.route('/admin/edit_user/<int:id>', methods=["GET", "POST"])
def edit_user(id):
    user = User.by_id(id)
    form = EditAddressForm(request.form, user)
    if form.validate_on_submit():
        user.realname = form.data['realname']
        user.florlp_name = form.data['florlp_name']
        user.street = form.data['street']
        user.housenumber =  form.data['housenumber']
        user.zipcode = form.data['zipcode']
        user.city = form.data['city']
        db.session.commit()
        flash( _('User edited', username=user.realname), 'success')
        return redirect(url_for("admin.user_detail", id=id))
    return render_template('admin/edit_user.html', form=form)

@admin.route('/admin/reset_user_password/<int:id>', methods=["GET", "POST"])
def reset_user_password(id):
    form = RecoverSetForm()
    if form.validate_on_submit():
        user = User.by_id(id)
        user.update_password(form.password.data)
        db.session.commit()
        flash( _('Password reset', username=user.realname), 'success')
        return redirect(url_for('admin.user_detail', id=id))
    return render_template('admin/reset_user_password.html', form=form)

@admin.route('/admin/remove_user/<int:id>', methods=["GET", "POST"])
def remove_user(id):
    user = User.by_id(id)
    if request.method == 'POST':
        email = user.email
        db.session.delete(user)
        db.session.commit()
        flash( _('User removed', username=email), "success")
        return redirect(url_for('admin.user_list'))
    return render_template('admin/remove_user.html', user=user)

@admin.route('/admin/user_log/<int:id>', methods=["GET"])
def user_log(id):
    user = User.by_id(id)
    result = db.session.query(Log, Log.geometry.envelope().wkt).filter_by(user=user).all()
    return render_template('admin/user_log.html', logs=result)

@admin.route('/admin/wmts/list', methods=["GET"])
def wmts_list():
    return render_template('admin/wmts_list.html', wmts=WMTS.query.all())

@admin.route('/admin/wmts/edit', methods=["GET", "POST"])
@admin.route('/admin/wmts/edit/<int:id>', methods=["GET", "POST"])
def wmts_edit(id=None):

    wmts = db.session.query(WMTS, pg_functions.geojson(WMTS.view_coverage.transform(3857))).filter_by(id=id).first() if id else None
    if wmts:
        wmts[0].view_coverage = wmts[1]
        wmts = wmts[0]
        form = WMTSForm(request.form, wmts)
    else:
        form = WMTSForm(request.form)

    if form.validate_on_submit():
        if not wmts:
            wmts = WMTS()
            db.session.add(wmts)
        if form.data['is_background_layer']:
            old_background_layer = WMTS.query.filter_by(is_background_layer=True).first()
            if old_background_layer:
                old_background_layer.is_background_layer = False
        wmts.url = form.data['url']
        wmts.username = form.data['username']
        wmts.password = form.data['password']
        wmts.is_protected = form.data['is_protected']
        wmts.name = form.data['name']
        wmts.title = form.data['title']
        wmts.layer = form.data['layer']
        wmts.format = form.data['format']
        wmts.srs = form.data['srs']
        wmts.max_tiles = form.data['max_tiles'] or None

        wmts.matrix_set = form.data['matrix_set']

        view_coverage = form.data['view_coverage']
        # load geometry to load string as  json - if not possible then try to use string as bbox
        try:
            geom = asShape(loads(view_coverage))
        except ValueError:
            bbox = [float(x) for x in view_coverage.split(",")]
            transfomed_bbox = transform_bbox('4326', '3857', bbox)
            geom = box(transfomed_bbox[0], transfomed_bbox[1], transfomed_bbox[2], transfomed_bbox[3])

        wmts.view_coverage = WKTSpatialElement(geom.wkt, srid=3857, geometry_type='POLYGON')
        wmts.view_level_start = form.data['view_level_start']
        wmts.view_level_end = form.data['view_level_end']
        wmts.is_background_layer = form.data['is_background_layer']
        wmts.is_baselayer = not form.data['is_transparent']
        wmts.is_overlay = form.data['is_transparent']
        wmts.is_transparent = form.data['is_transparent']
        wmts.is_visible = form.data['is_visible']
        wmts.is_public = form.data['is_public']
        wmts.is_accessible = form.data['is_accessible']
        try:
            db.session.commit()
            write_mapproxy_config(current_app)
            flash( _('Saved WMTS'), 'success')
            return redirect(url_for('admin.wmts_list'))
        except IntegrityError:
            db.session.rollback()
            flash(_('WMTS with this name already exist'), 'error')
    return render_template('admin/wmts_edit.html', form=form, id=id)

@admin.route('/admin/wmts/remove/<int:id>', methods=["GET"])
def wmts_remove(id):
    wmts = WMTS.by_id(id)
    if wmts:
        db.session.delete(wmts)
        db.session.commit()
        flash( _('WMTS removed'), 'success')
    return redirect(url_for('admin.wmts_list'))


@admin.route('/admin/wms/capabilities', methods=["GET"])
def wms_capabilities():
    url = request.args.get('url', False)
    if not url:
        return jsonify(error=_('Need url for capabilities'))

    try:
        data = parse_capabilities_url(url)
    except:
        data = {'error': 'load capabilities not possible'}
    return jsonify(data=data)


@admin.route('/admin/wms/list', methods=["GET"])
def wms_list():
    return render_template('admin/wms_list.html', wms=WMS.query.all())

@admin.route('/admin/wms/edit', methods=["GET", "POST"])
@admin.route('/admin/wms/edit/<int:id>', methods=["GET", "POST"])
def wms_edit(id=None):

    wms = db.session.query(WMS, pg_functions.geojson(WMS.view_coverage.transform(3857))).filter_by(id=id).first() if id else None
    if wms:
        wms[0].view_coverage = wms[1]
        wms = wms[0]
        form = WMSForm(request.form, wms)
    else:
        form = WMSForm(request.form)

    if form.validate_on_submit():
        if not wms:
            wms = WMS()
            db.session.add(wms)
        if form.data['is_background_layer']:
            old_background_layer = WMS.query.filter_by(is_background_layer=True).first()
            if old_background_layer:
                old_background_layer.is_background_layer = False
        wms.url = form.data['url']
        wms.username = form.data['username']
        wms.password = form.data['password']
        wms.is_protected = form.data['is_protected']
        wms.name = form.data['name']
        wms.title = form.data['title']
        wms.layer = form.data['layer']
        wms.format = form.data['format']
        wms.srs = form.data['srs']
        wms.max_tiles = form.data['max_tiles'] or None
        wms.version = form.data['version']

        view_coverage = form.data['view_coverage']
        # load geometry to load string as  json - if not possible then try to use string as bbox
        try:
            geom = asShape(loads(view_coverage))
        except ValueError:
            bbox = [float(x) for x in view_coverage.split(",")]
            transfomed_bbox = transform_bbox('4326', '3857', bbox)
            geom = box(transfomed_bbox[0], transfomed_bbox[1], transfomed_bbox[2], transfomed_bbox[3])

        wms.view_coverage = WKTSpatialElement(geom.wkt, srid=3857, geometry_type='POLYGON')
        wms.view_level_start = form.data['view_level_start']
        wms.view_level_end = form.data['view_level_end']
        wms.is_background_layer = form.data['is_background_layer']
        wms.is_baselayer = not form.data['is_transparent']
        wms.is_overlay = form.data['is_transparent']
        wms.is_transparent = form.data['is_transparent']
        wms.is_visible = form.data['is_visible']
        wms.is_public = form.data['is_public']

        # we only support WMS with direct access
        wms.is_accessible = True

        try:
            db.session.commit()
            write_mapproxy_config(current_app)
            flash( _('Saved WMS'), 'success')
            return redirect(url_for('admin.wms_list'))
        except IntegrityError, ex:
            print ex
            db.session.rollback()
            flash(_('WMS with this name already exist'), 'error')
    return render_template('admin/wms_edit.html', form=form, id=id)

@admin.route('/admin/wms/remove/<int:id>', methods=["GET"])
def wms_remove(id):
    wms = WMS.by_id(id)
    if wms:
        db.session.delete(wms)
        db.session.commit()
        flash( _('WMS removed'), 'success')
    return redirect(url_for('admin.wms_list'))

@admin.route('/admin/wfs/list', methods=["GET"])
def wfs_list():
    return render_template('admin/wfs_list.html', wfs=WFS.query.all())

@admin.route('/admin/wfs/edit', methods=["GET", "POST"])
@admin.route('/admin/wfs/edit/<int:id>', methods=["GET", "POST"])
def wfs_edit(id=None):
    wfs = db.session.query(WFS).filter_by(id=id).first() if id else None
    form = WFSForm(request.form, wfs)

    if form.validate_on_submit():
        if not wfs:
            wfs = WFS()
            db.session.add(wfs)

        wfs.name = form.data['name']
        wfs.host = form.data['host']
        wfs.url = form.data['url']
        wfs.geometry = form.data['geometry']
        wfs.layer = form.data['layer']
        wfs.srs = form.data['srs']
        wfs.ns_prefix = form.data['ns_prefix']
        wfs.ns_uri = form.data['ns_uri']
        wfs.search_property = form.data['search_property']
        wfs.max_features = form.data['max_features']
        wfs.username = form.data['username']
        wfs.password = form.data['password']
        wfs.is_protected = form.data['is_protected']

        try:
            db.session.commit()
            flash( _('Saved WFS'), 'success')
            return redirect(url_for('admin.wfs_list'))
        except IntegrityError:
            db.session.rollback()
            flash(_('WFS with this name already exist'), 'error')

    return render_template('admin/wfs_edit.html', form=form, id=id)


@admin.route('/admin/wfs/remove/<int:id>', methods=["GET"])
def wfs_remove(id):
    wfs = WFS.by_id(id)
    if wfs:
        db.session.delete(wfs)
        db.session.commit()
        flash( _('WFS removed'), 'success')
    return redirect(url_for('admin.wfs_list'))
