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

from flask import g, url_for
from gbi_server.extensions import db
from geoalchemy2.types import Geometry


class WMTS(db.Model):
    __tablename__ = 'wmts'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)

    url = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    title = db.Column(db.String)
    format = db.Column(db.String, nullable=False)

    max_tiles = db.Column(db.Integer)

    view_coverage = db.Column(Geometry('POLYGON', srid=4326))
    view_level_start = db.Column(db.Integer)
    view_level_end = db.Column(db.Integer)

    # used in context document but not in gbi-client
    # check we can delete it
    is_baselayer = db.Column(db.Boolean(), default=False)

    # used in context document
    # used on for gbi-client for export in mapproxy mbtiles etc.
    is_overlay = db.Column(db.Boolean(), default=True)

    # used in context document
    # gbi-client use user and password from context document if it is false
    is_protected = db.Column(db.Boolean(), default=True)

    # used on geobox editor and for sorting on context document
    # gbi-client: the first layer of the contxt document is background layer
    is_background_layer = db.Column(db.Boolean(), default=False)

    # used on geobox editor
    is_transparent = db.Column(db.Boolean(), default=True)
    is_visible = db.Column(db.Boolean(), default=True)

    # if it is public the complete view coverage added to the context document
    # if not only the geometry from the user is allowed
    is_public = db.Column(db.Boolean(), default=False)

    # access map without authproxy
    is_accessible = db.Column(db.Boolean(), default=False)

    @classmethod
    def by_id(cls, id):
        q = cls.query.filter(cls.id == id)
        return q.first_or_404()

    @classmethod
    def by_name(cls, name):
        q = cls.query.filter(cls.name == name)
        return q.first_or_404()

    def client_url(self, external=False):
        if self.is_public and self.is_accessible:
            return self.url.rstrip('/') + '/'

        if external:
            return url_for('authproxy.tile_proxy', user_token=g.user.authproxy_token, _external=True).rstrip('/') + '/'  + self.url

        return url_for('authproxy.tile_proxy').rstrip('/') + '/' + self.url


class WMS(db.Model):
    __tablename__ = 'wms'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String, nullable=False, unique=True)

    url = db.Column(db.String(256), nullable=False)
    username = db.Column(db.String(64))
    password = db.Column(db.String(64))
    title = db.Column(db.String)
    layer = db.Column(db.String(256), nullable=False)
    format = db.Column(db.String, nullable=False)
    srs = db.Column(db.String(64), default="EPSG:3857")
    version = db.Column(db.String, default="1.1.1")

    view_coverage = db.Column(Geometry('POLYGON', srid=4326))
    view_level_start = db.Column(db.Integer)
    view_level_end = db.Column(db.Integer)

    is_background_layer = db.Column(db.Boolean(), default=False)
    is_baselayer = db.Column(db.Boolean(), default=False)
    is_overlay = db.Column(db.Boolean(), default=True)
    is_transparent = db.Column(db.Boolean(), default=True)
    is_visible = db.Column(db.Boolean(), default=True)
    is_public = db.Column(db.Boolean(), default=False)
    is_accessible = db.Column(db.Boolean(), default=True)
    is_protected = db.Column(db.Boolean(), default=True)

    @classmethod
    def by_id(cls, id):
        q = cls.query.filter(cls.id == id)
        return q.first_or_404()

    @classmethod
    def by_name(cls, name):
        q = cls.query.filter(cls.name == name)
        return q.first_or_404()
