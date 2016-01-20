# This file is part of the GBI project.
# Copyright (C) 2016 Omniscale GmbH & Co. KG <http://omniscale.com>
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


import sqlalchemy as sa
from sqlalchemy import sql
from werkzeug import exceptions
from flask import request, current_app

import shapely.wkt
from gbi_server.authproxy.limiter import CouchDBCoverages
from shapely.geometry import mapping

DATA_SRID = 25832
MAX_DIST = 500

metadata = sa.MetaData(schema='qs')
parcel_table = sa.Table('fd044_0515_flst_gf_tb', metadata,
    sa.Column('fd044_fs_kennzeichen', sa.String, key='number'),
    sa.Column('fd044_fs_kennzeichen_alb', sa.String, key='identifier'),
    sa.Column('fd044_geom', sa.LargeBinary, key='geometry'),
)

def cleanup_id(id):
    return id.replace('-', '').replace('/', '').replace(' ', '')


class Query(object):
    def __init__(self, tbl):
        self.tbl = tbl
        self.query = sql.select([tbl])

    def limit(self, n=1000):
        self.query = self.query.limit(n)

    def near(self, coord, srid, dist):
        pt = sql.func.st_setsrid(sql.func.st_point(coord[0], coord[1]), srid)
        pt = sql.func.st_transform(pt, current_app.config['PARCEL_SEARCH_DATABASE_SRID'])

        self.query = self.query.where(
            sql.func.st_intersects(self.tbl.c.geometry,
                sql.func.st_buffer(pt, dist, 2)
            )
        )
        self.query = self.query.where(sql.func.st_distance(self.tbl.c.geometry, pt) < dist)

    def intersection(self, wkt, srid):
        if not isinstance(wkt, basestring):
            wkt = shapely.wkt.dumps(wkt)
        geom = sql.func.st_setsrid(sql.func.st_geomfromtext(wkt), srid)
        geom = sql.func.st_transform(geom, current_app.config['PARCEL_SEARCH_DATABASE_SRID'])

        self.query = self.query.where(
            sql.func.st_intersects(
                self.tbl.c.geometry,
                geom,
            )
        )

    def ids(self, ids):
        self.query = self.query.where(parcel_table.c.number.in_([cleanup_id(id) for id in ids]))

    def as_sa(self):
        return self.query.alias('sub')


class ParcelSearch(object):
    def __init__(self, table_cls=None):
        self.limiter = None
        self.engine = None
        self.table_cls = table_cls or parcel_table

    def init_app(self, app):
        if app.config.get('PARCEL_SEARCH_USE_DUMMY_DATA', False):
            from .dummy import DummyCoverage, DummyEngine
            self.engine = DummyEngine()
            self.limiter = DummyCoverage()
            return

        db_uri = app.config['PARCEL_SEARCH_DATABASE_URI']
        echo = app.config.get('PARCEL_SEARCH_DATABASE_ECHO', False)
        self.engine = sa.create_engine(db_uri, echo=echo)

        self.limiter = CouchDBCoverages(
            cache_dir=None,
            couchdb_url=app.config['COUCH_DB_URL'],
            geometry_layer=None,
        )

    def new_query(self):
        return Query(self.table_cls)

    def search(self, query, user_token):
        from gbi_server.model import User
        user = User.by_authproxy_token(user_token)
        if not user:
            raise exceptions.Unauthorized()

        coverage = self.limiter.coverage(user_token)
        if not coverage:
            current_app.logger.debug("found no coverage user=%s query=%s", user, request.url)
            return None

        query.intersection(coverage, 3857)

        # query.ids(['072578-040-00042/000'])
        # f.near((7.88475, 49.859677), 4326, dist=500)
        # q = sql.select([parcel_table]).where(parcel_table.c.number == cleanup_id('072578-040-00042/000'))

        features = []
        query.limit(1000)
        sub = query.as_sa()
        q = sql.select([sub.c.identifier, sql.func.st_astext(sql.func.st_transform(sub.c.geometry, '3857')).label('geometry')])

        with self.engine.connect() as conn:
            for r in conn.execute(q):
                features.append({
                    "type": "Feature",
                    "properties": {
                        "id": r.identifier,
                    },
                    "geometry": mapping(shapely.wkt.loads(r.geometry)),
                })

        return features



if __name__ == '__main__':

    from gbi_server.application import create_app

    app = create_app()

    app.debug = True
    app.config['flst_limiter'] = DummyCoverage()
    app.register_blueprint(flst)

    app.run(debug=True)

