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

import os
import time
import errno
from glob import glob

from shapely.geometry import box
from shapely import wkb
from geoalchemy2.functions import ST_Transform
from geoalchemy2.shape import to_shape

from mapproxy.grid import tile_grid
from mapproxy.util.lock import FileLock

from gbi_server.lib.geometry import optimize_geometry
from gbi_server.lib.couchdb import CouchDBBox
from gbi_server.config import SystemConfig


import logging
log = logging.getLogger(__name__)

class InvalidUserToken(ValueError):
    pass

class LimiterCache(object):
    def __init__(self, cache_dir, file_pattern='*'):
        self.cache_dir = cache_dir
        self.file_pattern = file_pattern
        self.max_cache_time = 5*60 # 5min

    def cache_path(self, user_token):
        return os.path.join(self.cache_dir, user_token[:2], user_token)

    def cache_file(self, user_token, filename):
        return os.path.join(self.cache_path(user_token))

    def clear(self, user_token, file_pattern=None):
        if file_pattern is None:
            file_pattern = self.file_pattern
        for f in glob(os.path.join(self.cache_path(user_token), file_pattern)):
            try:
                os.remove(f)
            except EnvironmentError, ex:
                if ex.errno != errno.EEXIST:
                    raise

    def load(self, user_token, name):
        if not self.cache_dir:
            return self.create(user_token, name)

        cache_file = self.cache_file(user_token, name)
        try:
            mtime = os.path.getmtime(cache_file)
            if (time.time() - mtime) > self.max_cache_time:
                log.debug('removing cached tilelimit for %s %s', user_token, name)
                os.unlink(cache_file)
        except EnvironmentError, ex:
            if ex.errno != errno.ENOENT:
                raise

        try:
            with open(cache_file, 'rb') as f:
                return self.deserialize(f.read())
        except EnvironmentError, ex:
            if ex.errno != errno.ENOENT:
                raise

        with FileLock(cache_file + '.lck', remove_on_unlock=True):
            if os.path.exists(cache_file):
                # created while we were waiting for the lock
                return self.load(user_token, name)
            data = self.create(user_token, name)
            self.cache(user_token, name, data)

        return data

    def create(self, user_token, name):
        raise NotImplementedError

    def serialize(self, date):
        raise NotImplementedError

    def deserialize(self, date):
        raise NotImplementedError

    def cache(self, user_token, name, data):
        try:
            os.makedirs(self.cache_path(user_token))
        except OSError, ex:
            if ex.errno != errno.EEXIST:
                # ignore error when path already exists
                pass

        with open(self.cache_file(user_token, name), 'wb') as f:
            f.write(self.serialize(data))


DEFAULT_GRID = tile_grid(3857, origin='nw')

class CouchDBCoverages(LimiterCache):
    def __init__(self, cache_dir, couchdb_url, geometry_layer):
        LimiterCache.__init__(self, cache_dir=cache_dir)
        self.cache_dir = cache_dir
        self.couchdb_url = couchdb_url
        self.geometry_layer = geometry_layer

    def cache_file(self, user_token, name):
        return os.path.join(self.cache_path(user_token), name + '.wkb')

    def coverage(self, user_token):
        return self.load(user_token, 'vector-search')

    def create(self, user_token, layer):
        from gbi_server.model import User
        from gbi_server.model import WMTS

        from gbi_server.extensions import db

        user = User.by_authproxy_token(user_token)
        if not user:
            raise InvalidUserToken()

        result = db.session.query(WMTS, ST_Transform(WMTS.view_coverage, 3857)).filter_by(name=layer).first()

        if result:
            wmts, view_coverage = result
            if wmts and wmts.is_public:
                return to_shape(view_coverage)

        if user.is_customer:
            couch_url = self.couchdb_url
            couchdb = CouchDBBox(couch_url, '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
            geom = couchdb.layer_extent(self.geometry_layer)
            return optimize_geometry(geom) if geom else None
        elif user.is_service_provider:
            couch_url = self.couchdb_url
            couchdb = CouchDBBox(couch_url, '%s_%s' % (SystemConfig.AREA_BOX_NAME, user.id))
            geom = couchdb.layer_extent()
            return optimize_geometry(geom) if geom else None
        elif user.is_admin or user.is_consultant:
            # permit access to everything
            return box(-20037508.3428, -20037508.3428, 20037508.3428, 20037508.3428)

        return None

    def serialize(self, data):
        if data:
            return data.wkb
        else:
            return ''

    def deserialize(self, data):
        if data:
            return wkb.loads(data)
        else:
            return None


class TileCoverages(CouchDBCoverages):
    def __init__(self, cache_dir, couchdb_url, geometry_layer, tile_grid=DEFAULT_GRID):
        CouchDBCoverages.__init__(self, cache_dir=cache_dir, couchdb_url=couchdb_url, geometry_layer=geometry_layer)
        self.tile_grid = tile_grid

    def is_permitted(self, user_token, layer, tile_coord):
        geometry = self.load(user_token, layer)
        if not geometry:
            return False
        bbox = self.tile_grid.tile_bbox(tile_coord)
        return geometry.intersects(box(*bbox))
