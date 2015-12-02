# This file is part of the GBI project.
# Copyright (C) 2015 Omniscale GmbH & Co. KG <http://omniscale.com>
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

from flask import render_template, flash, redirect, \
    url_for, request, current_app, jsonify

from flask.ext.babel import gettext as _
from sqlalchemy.exc import IntegrityError

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import asShape
from shapely.geometry import mapping

import json

from gbi_server.views.admin import admin

from gbi_server.extensions import db
from gbi_server.model import WMTS, WMS, WFS
from gbi_server.forms.admin import WMTSForm, WMSForm, WFSForm
from gbi_server.lib.external_wms import write_mapproxy_config
from gbi_server.lib.capabilites import parse_capabilities_url


@admin.route('/admin/wmts/list', methods=["GET"])
def wmts_list():
    return render_template('admin/wmts_list.html', wmts=WMTS.query.all())


@admin.route('/admin/wmts/edit', methods=["GET", "POST"])
@admin.route('/admin/wmts/edit/<int:id>', methods=["GET", "POST"])
def wmts_edit(id=None):

    wmts = WMTS.by_id(id) if id else None
    if wmts:
        form = WMTSForm(request.form, wmts)
    else:
        form = WMTSForm(request.form)

    if form.validate_on_submit():
        if not wmts:
            wmts = WMTS()
            db.session.add(wmts)
        wmts.url = form.data['url']
        wmts.username = form.data['username']
        wmts.password = form.data['password']
        wmts.is_protected = form.data['is_protected']
        wmts.name = form.data['name']
        wmts.title = form.data['title']
        wmts.format = form.data['format']
        wmts.max_tiles = form.data['max_tiles'] or None

        try:
            view_coverage = json.loads(form.data['view_coverage'])
            only_first_geometry = False
            view_geometry = None
            # check if we have a feature colleciton than load only first geometry
            if 'features' in view_coverage:
                for feature in view_coverage['features']:
                    if 'geometry' in feature:
                        if view_geometry:
                            only_first_geometry = True
                            break
                        view_geometry = feature['geometry']

            if view_geometry:
                view_coverage = view_geometry

            if only_first_geometry:
                flash(_('Only the first geometry was used for view coverage'), 'success')

            wmts.view_coverage = from_shape(asShape(view_coverage), srid=4326)
        except:
            db.session.rollback()
            flash(_('Geometry not correct'), 'error')
            return render_template('admin/wmts_edit.html', form=form, id=id)

        wmts.view_level_start = form.data['view_level_start']
        wmts.view_level_end = form.data['view_level_end']
        wmts.is_background_layer = form.data['is_background_layer']
        wmts.is_overlay = form.data['is_transparent']
        wmts.is_transparent = form.data['is_transparent']
        wmts.is_visible = form.data['is_visible']
        wmts.is_public = form.data['is_public']
        wmts.is_accessible = form.data['is_accessible']
        try:
            db.session.commit()
            write_mapproxy_config(current_app)
            flash(_('Saved WMTS'), 'success')
            return redirect(url_for('admin.wmts_list'))
        except IntegrityError:
            db.session.rollback()
            flash(_('WMTS with this name already exist'), 'error')

    # load wmts_coverage as json
    if wmts:
        view_coverage = to_shape(wmts.view_coverage)
        form.view_coverage.data = json.dumps(mapping(view_coverage))

    return render_template('admin/wmts_edit.html', form=form, id=id)


@admin.route('/admin/wmts/remove/<int:id>', methods=["POST"])
def wmts_remove(id):
    wmts = WMTS.by_id(id)
    db.session.delete(wmts)
    db.session.commit()
    flash(_('WMTS removed'), 'success')
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

    wms = WMS.by_id(id) if id else None
    if wms:
        form = WMSForm(request.form, wms)
    else:
        form = WMSForm(request.form)

    if form.validate_on_submit():
        if not wms:
            wms = WMS()
            db.session.add(wms)
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

        try:
            view_coverage = json.loads(form.data['view_coverage'])
            only_first_geometry = False
            view_geometry = None
            # check if we have a feature colleciton than load only first geometry
            if 'features' in view_coverage:
                for feature in view_coverage['features']:
                    if 'geometry' in feature:
                        if view_geometry:
                            only_first_geometry = True
                            break
                        view_geometry = feature['geometry']

            if view_geometry:
                view_coverage = view_geometry

            if only_first_geometry:
                flash(_('Only the first geometry was used for view coverage'), 'success')

            wms.view_coverage = from_shape(asShape(view_coverage), srid=4326)
        except:
            db.session.rollback()
            flash(_('Geometry not correct'), 'error')
            return render_template('admin/wmts_edit.html', form=form, id=id)

        wms.view_level_start = form.data['view_level_start']
        wms.view_level_end = form.data['view_level_end']
        wms.is_background_layer = form.data['is_background_layer']
        wms.is_overlay = form.data['is_transparent']
        wms.is_transparent = form.data['is_transparent']
        wms.is_visible = form.data['is_visible']
        wms.is_public = form.data['is_public']

        # we only support WMS with direct access
        wms.is_accessible = True

        try:
            db.session.commit()
            write_mapproxy_config(current_app)
            flash(_('Saved WMS'), 'success')
            return redirect(url_for('admin.wms_list'))
        except IntegrityError, ex:
            print ex
            db.session.rollback()
            flash(_('WMS with this name already exist'), 'error')
        # load wmts_coverage as json

    if wms:
        view_coverage = to_shape(wms.view_coverage)
        form.view_coverage.data = json.dumps(mapping(view_coverage))

    return render_template('admin/wms_edit.html', form=form, id=id)


@admin.route('/admin/wms/remove/<int:id>', methods=["POST"])
def wms_remove(id):
    wms = WMS.by_id(id)
    db.session.delete(wms)
    db.session.commit()
    flash(_('WMS removed'), 'success')
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
            flash(_('Saved WFS'), 'success')
            return redirect(url_for('admin.wfs_list'))
        except IntegrityError:
            db.session.rollback()
            flash(_('WFS with this name already exist'), 'error')

    return render_template('admin/wfs_edit.html', form=form, id=id)


@admin.route('/admin/wfs/remove/<int:id>', methods=["POST"])
def wfs_remove(id):
    wfs = WFS.by_id(id)
    db.session.delete(wfs)
    db.session.commit()
    flash(_('WFS removed'), 'success')
    return redirect(url_for('admin.wfs_list'))
