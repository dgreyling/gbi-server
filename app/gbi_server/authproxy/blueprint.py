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

from flask import Blueprint, request, session, abort, jsonify

from gbi_server.extensions import tileproxy
from gbi_server.extensions import couchdbproxy
from gbi_server import signals
from gbi_server.model import User
from gbi_server.lib.exceptions import json_abort

authproxy = Blueprint("authproxy", __name__)

for code in [401, 403, 404, 405]:
    @authproxy.errorhandler(code)
    def on_error(error):
        return error

@authproxy.route('/authproxy/<string:user_token>/couchdb/', build_only=True)
@authproxy.route('/authproxy/<string:user_token>/couchdb/<path:url>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def couchdb_proxy(url, user_token):
    return couchdbproxy.on_proxy(request, user_token=user_token, url=url)


@authproxy.route('/authproxy/couchdb/<path:url>', methods=['GET'])
def couchdb_proxy_file(url):
    user_token = session.get('authproxy_token')
    if user_token is None:
        abort(401)
    url += '/file'
    return couchdbproxy.on_proxy(request, user_token=user_token, url=url)


@authproxy.route('/authproxy/tiles/', build_only=True)
@authproxy.route('/authproxy/tiles/<path:url>', methods=['GET', 'POST'])
@authproxy.route('/authproxy/<string:user_token>/tiles/', build_only=True)
@authproxy.route('/authproxy/<string:user_token>/tiles/<path:url>', methods=['GET', 'POST'])
@authproxy.route('/authproxy/<string:user_token>/tiles//<path:url>', methods=['GET', 'POST'])
def tile_proxy(url, user_token=None):
    if user_token is None:
        user_token = session.get('authproxy_token')
        if user_token is None:
            abort(401)
    return tileproxy.on_proxy(request, user_token=user_token, url=url)


@authproxy.route('/authproxy/<string:user_token>/update_coverage', methods=['GET'])
def update_download_coverage(user_token):
    user = User.by_authproxy_token(user_token)
    if not user:
        json_abort(401, 'unknown user token')

    signals.features_updated.send(user)

    return jsonify({'sucess': True})
