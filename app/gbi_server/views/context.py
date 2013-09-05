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

import json

from functools import wraps
from flask import Blueprint, request, Response, g, url_for, current_app
from flask.ext.babel import gettext as _

from sqlalchemy.sql.expression import desc
from geoalchemy.postgis import pg_functions
import shapely.geometry

from gbi_server.config import SystemConfig
from gbi_server.model import WMTS, WMS, WFS, User
from gbi_server.extensions import db
from gbi_server.lib.couchdb import CouchDBBox
from gbi_server.lib.geometry import optimize_geometry

context = Blueprint("context", __name__, template_folder="../templates")

def check_auth(username, password):
    user = User.by_email(username)
    if user and user.check_password(password) and user.active:
        g.user = user
        return True
    else:
        return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response("""
                Could not verify your access level for that URL.
                You have to login with proper credentials""", 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

@context.route('/context')
@requires_auth
def get_context_document():
    wmts_sources = db.session.query(WMTS, pg_functions.geojson(WMTS.view_coverage.transform(3857))).order_by(desc(WMTS.is_background_layer)).all()
    wms_sources = db.session.query(WMS, pg_functions.geojson(WMS.view_coverage.transform(3857))).order_by(desc(WMS.is_background_layer)).all()
    wfs_sources = db.session.query(WFS).all()

    response = {
        "version": "0.1",
        "portal": {
            "prefix": current_app.config['PORTAL_PREFIX'],
            "title": current_app.config['PORTAL_TITLE'],
        },
        "wmts_sources": [],
        "wms_sources": [],
        "wfs_sources": [],
        "couchdb_sources": [],
    }

    couchdb = CouchDBBox(current_app.config['COUCH_DB_URL'], '%s_%s' % (SystemConfig.AREA_BOX_NAME, g.user.id))
    user_geom = couchdb.layer_extent(current_app.config['USER_WORKON_LAYER'])
    if user_geom:
        user_geom = optimize_geometry(user_geom)
        user_geom = shapely.geometry.mapping(user_geom)

    for source in wmts_sources:
        wmts, view_coverage = source
        if wmts.is_public:
            geom = json.loads(view_coverage)
        elif user_geom:
            geom = user_geom
        else:
            continue
        response['wmts_sources'].append({
            "name": wmts.name,
            "title": wmts.title,
            "url": wmts.client_url(external=True),
            "layer": wmts.layer,
            "tile_matrix": wmts.matrix_set,
            "format": wmts.format,
            "baselayer": wmts.is_baselayer,
            "overlay": wmts.is_overlay,
            "username": wmts.username,
            "password": wmts.password,
            "is_protected": wmts.is_protected,
            "srs": wmts.srs,
            "max_tiles": wmts.max_tiles,
            "view_restriction": {
                "zoom_level_start": wmts.view_level_start,
                "zoom_level_end": wmts.view_level_end,
                "geometry": geom
            },
            "download_restriction": {
                "zoom_level_start": wmts.view_level_start,
                "zoom_level_end": wmts.view_level_end,
                "geometry": geom
            }
        })

    for source in wms_sources:
        wms, view_coverage = source
        if wms.is_public:
            geom = json.loads(view_coverage)
        elif user_geom:
            geom = user_geom
        else:
            continue
        response['wms_sources'].append({
            "name": wms.name,
            "title": wms.title,
            "url": wms.url,
            "layer": wms.layer,
            "format": wms.format,
            "baselayer": wms.is_baselayer,
            "overlay": wms.is_overlay,
            "username": wms.username,
            "password": wms.password,
            "is_protected": wms.is_protected,
            "srs": wms.srs,
            "wms_version": wms.version,
            "view_restriction": {
                "zoom_level_start": wms.view_level_start,
                "zoom_level_end": wms.view_level_end,
                "geometry": geom
            },
            "download_restriction": {
                "zoom_level_start": wms.view_level_start,
                "zoom_level_end": wms.view_level_end,
                "geometry": geom
            }
        })

    for wfs in wfs_sources:
        response['wfs_sources'].append({
            'id': wfs.id,
            'name': wfs.name,
            'layer': wfs.layer,
            'host': wfs.host,
            'url': wfs.url,
            'srs': wfs.srs,
            'geometry_field': wfs.geometry,
            'feature_ns': wfs.ns_uri,
            'typename': wfs.ns_prefix,
            'search_property': wfs.search_property,
            'username': wfs.username,
            'password': wfs.password,
            'is_protected': wfs.is_protected,

        })

    if current_app.config['FEATURE_AREA_BOXES']:
        response['couchdb_sources'].append({
            "name": _('area box'),
            "url": current_app.config['COUCH_DB_URL'],
            "dbname": '%s_%s' % (SystemConfig.AREA_BOX_NAME, g.user.id),
            "username": 'user_%d' % g.user.id,
            "password": g.user.authproxy_token,
            "writable": True,
            "dbname_user":  SystemConfig.AREA_BOX_NAME_LOCAL,
        })

    if current_app.config['FEATURE_DOC_BOXES']:
        if g.user.is_consultant:
            response['couchdb_sources'].append({
                "name": _('file box'),
                "url": current_app.config['COUCH_DB_URL'],
                "dbname": '%s_%s' % (SystemConfig.FILE_BOX_NAME, g.user.id),
                "username": 'user_%d' % g.user.id,
                "password": g.user.authproxy_token,
                "writable": True,
                "dbname_user":  SystemConfig.FILE_BOX_NAME_LOCAL,
            })
        else:
            response['couchdb_sources'].append({
                "name": _('consultant box'),
                "url": current_app.config['COUCH_DB_URL'],
                "dbname": '%s_%s' % (SystemConfig.DOWNLOAD_BOX_NAME, g.user.id),
                "username": 'user_%d' % g.user.id,
                "password": g.user.authproxy_token,
                "writable": False,
                "dbname_user":  SystemConfig.DOWNLOAD_BOX_NAME_LOCAL,
            })

    response['logging'] = {
        'url': url_for('logserv.log', user_token=g.user.authproxy_token, _external=True),
    }

    response['user'] = {
        'email': g.user.email,
        'type': g.user.type,
        'type_name': g.user.type_name,
    }

    return json.dumps(response)