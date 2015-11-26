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

from itertools import chain
import bcrypt
import datetime

from geoalchemy2.elements import WKTElement
from shapely.geometry import asShape
from json import loads

from gbi_server import model
from gbi_server.config import SystemConfig
from gbi_server.lib.couchdb import CouchDBBox, init_user_boxes

def all():
    users = [
        model.User(email='admin@example.org'),
        model.User(email='landwirt@example.org'),
        model.User(email='dienstleister@example.org'),
        model.User(email='berater@example.org'),
    ]

    users[0].active = True
    users[0].verified = True
    users[0].type = 99
    users[0].title = 'mr'
    users[0].firstname = 'Bernd'
    users[0].lastname = 'Beispiel'
    users[0].address = 'Haupstrasse'
    users[0].zipcode = '26121'
    users[0].city = 'Oldenburg'
    users[0].federal_state = 'NI'
    users[0].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))

    users[1].active = True
    users[1].verified = True
    users[1].type = 0
    users[1].title = 'mr'
    users[1].firstname = 'Peter'
    users[1].lastname = 'Beispiel'
    users[1].address = 'Hauptweg'
    users[1].zipcode = '26123'
    users[1].city = 'Oldenburg'
    users[1].federal_state = 'NI'
    users[1].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))
    users[1].authproxy_token = '12345'

    users[2].active = True
    users[2].verified = True
    users[2].type = 1
    users[2].title = 'mrs'
    users[2].firstname = 'Susanne'
    users[2].lastname = 'Hermann'
    users[2].address = 'Schulstrasse'
    users[2].zipcode = '50991'
    users[2].city = 'Mainz'
    users[2].federal_state = 'BW'
    users[2].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))

    users[3].active = True
    users[3].verified = True
    users[3].type = 50
    users[3].title = 'mr'
    users[3].firstname = 'Karl'
    users[3].lastname = 'Mustermann'
    users[3].address = 'Peterstrasse'
    users[3].zipcode = '50991'
    users[3].city = 'Stuttgart'
    users[3].federal_state = 'RP'
    users[3].password = bcrypt.hashpw('secure', bcrypt.gensalt(10))
    users[3].authproxy_token = '99999'

    wmts = [
        model.WMTS(
            name='omniscale_osm',
            url='http://igreendemo.omniscale.net/wmts/omniscale_osm/GoogleMapsCompatible-{TileMatrix}-{TileCol}-{TileRow}/tile',
            title='Omniscale OSM',
            format='png',
            view_coverage=WKTElement(asShape(loads("""{
                "type":"Polygon",
                "coordinates":[[
                    [6.50390625, 46.800059446787316],
                    [6.50390625, 53.592504809039376],
                    [14.0625, 53.592504809039376],
                    [14.0625, 46.800059446787316],
                    [6.50390625, 46.800059446787316]
                ]]
                }""")).wkt, srid=4326),
            view_level_start=7,
            view_level_end=18,
            is_background_layer=True,
            is_baselayer=True,
            is_overlay=False,
            is_transparent=False,
            is_visible=True),
    ]

    geom = WKTElement('MULTIPOLYGON(((8 49,8 50,9 50,9 49,8 49)))', srid=4326)

    logs = [
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='vector_import', mapping='Schlaege Niedersachsen', source='example.shp', format='SHP'),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='vector_export', mapping='Schlaege Niedersachsen', source='flaechen-box', format='SHP'),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='raster_import', geometry=geom, source='http://localhost:5000/authproxy/12345/tiles', layer='omniscale_osm', zoom_level_start=8, zoom_level_end=14, refreshed=False),
        model.Log(user=users[1], time=datetime.datetime.now().isoformat(), action='raster_export', geometry=geom, format='JPEG', srs='EPSG:3857', layer='omniscale_osm', zoom_level_start=10, zoom_level_end=10, source='http://localhost:5000/authproxy/12345/tiles')
    ]

    return chain(users, wmts, logs)


def init_couchdb(config):
    user = model.User.by_email('landwirt@example.org')
    init_user_boxes(user, config.get('COUCH_DB_URL'))

    user = model.User.by_email('dienstleister@example.org')
    init_user_boxes(user, config.get('COUCH_DB_URL'))

    user = model.User.by_email('berater@example.org')
    init_user_boxes(user, config.get('COUCH_DB_URL'))
