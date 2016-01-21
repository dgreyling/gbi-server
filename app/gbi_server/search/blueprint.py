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

from flask import Blueprint, request, jsonify

from shapely.geometry import asShape
from shapely import geometry

from gbi_server.extensions import db
from gbi_server.model import User, SearchLog, SearchLogGeometry

search = Blueprint("search", __name__)

MAX_DIST = 500

@search.route('/search/<token>/query', methods=['GET', 'POST'])
def query(token):
    from gbi_server.extensions import parcel_search
    q = parcel_search.new_query()

    fc = request.json
    if fc:
        # build intersection from POSTed GeoJSON
        geom = geometry_from_feature_collection(fc)
        q.intersection(geom, 4326)
    elif 'lat' in request.args and 'lon' in request.args:
        # find within `dist` of lon/lat
        dist = min(float(request.args.get('dist', '5')), MAX_DIST)
        lon = float(request.args['lon'])
        lat = float(request.args['lat'])
        q.near((lon, lat), 4326, dist=dist)
    elif 'ids' in request.args:
        # find list of ids
        q.ids(i.strip() for i in request.args['ids'].split(','))
    else:
        return jsonify(message="not a valid query"), 400

    features = parcel_search.search(q, token)

    if features:
        db.session.add(search_log_from_features(token, features))
        db.session.commit()

    return jsonify({
        "type": "FeatureCollection",
        "features": features,
    })


def search_log_from_features(token, features):
    user = User.by_authproxy_token(token)
    sl = SearchLog(user=user)
    for f in features:
        g = SearchLogGeometry(
            identifier=f['properties']['id'],
            geometry='SRID=3857;' + asShape(f['geometry']).wkt,
        )
        sl.geometries.append(g)

    return sl

def geometry_from_feature_collection(feature_collection):
    polygons = []
    if 'features' in feature_collection:
        for feature in feature_collection['features']:
            g = feature['geometry']
            if g['type'] == 'Polygon':
                polygons.append(asShape(g))

    if polygons:
        mp = geometry.MultiPolygon(polygons)
        if not mp.is_valid:
            mp = mp.buffer(0)
        return mp
