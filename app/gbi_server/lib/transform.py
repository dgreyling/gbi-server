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

from mapproxy.srs import SRS
from mapproxy.util.coverage import BBOXCoverage

def transform_features(from_srs, to_srs, features):
    """
    Transform list of `features`. Modifies `features` in-place.
    """
    from_srs = SRS(from_srs)
    to_srs = SRS(to_srs)
    for feature in features:
        transform_geojson(from_srs, to_srs, feature)

    return features

def transform_bbox(from_srs, to_srs, bbox):
    """
    Transform list of `features`. Modifies `features` in-place.
    """
    bbox_coverage = BBOXCoverage(bbox, SRS(from_srs))
    coverage_transformed = bbox_coverage.transform_to(SRS(to_srs))
    return coverage_transformed.bbox

def transform_geojson(from_srs, to_srs, geojson):
    """
    Transform `geojson` geometries. Modifies `geojson` in-place.
    """
    from_srs = SRS(from_srs)
    to_srs = SRS(to_srs)

    feature_type = geojson.get('type', 'Feature')
    if feature_type == 'FeatureCollection':
        for feature in geojson['features']:
            feature['geometry']['coordinates'] = _transform_coordinates(
                from_srs, to_srs, feature['geometry']['coordinates'])
    elif feature_type == 'Feature':
        geojson['geometry']['coordinates'] = _transform_coordinates(
            from_srs, to_srs, geojson['geometry']['coordinates'])
    else:
        geojson['coordinates'] = _transform_coordinates(
            from_srs, to_srs, geojson['coordinates'])

    return geojson

def _transform_coordinates(from_srs, to_srs, coordinates):
    if coordinates and isinstance(coordinates[0], (tuple, list)):
        return [_transform_coordinates(from_srs, to_srs, coords) for coords in coordinates]

    return from_srs.transform_to(to_srs, coordinates)


if __name__ == '__main__':
    import json
    import sys

    from_srs = 'EPSG:4326'
    to_srs = 'EPSG:3857'
    if len(sys.argv) > 1 and sys.argv[1] == '--towgs':
        from_srs, to_srs = to_srs, from_srs

    input = json.load(sys.stdin)
    output = transform_geojson(from_srs, to_srs, input)
    print json.dumps(output, indent=2)