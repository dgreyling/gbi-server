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

"""
Dummy implementations for parcel search classes to allow testing of search
service without databases.
"""

from contextlib import contextmanager
from collections import namedtuple
from shapely.geometry import asShape

class DummyCoverage(object):
    def coverage(self, token):
        if token == 'invalid':
            return None
        return asShape(dummy_clip['features'][0]['geometry'])

class DummyEngine(object):

    @contextmanager
    def connect(self):
        yield self

    def execute(self, query):
        dummyrow = namedtuple('dummyrow', ('identifier', 'geometry'))
        for f in dummy_parcels['features']:
            yield dummyrow(f['properties']['id'], asShape(f['geometry']).wkt)


dummy_clip = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            875113.2048941795,
                            6420079.770471452
                        ],
                        [
                            874248.5110117028,
                            6419993.778814631
                        ],
                        [
                            874234.1790689,
                            6419716.694587098
                        ],
                        [
                            874659.3600387367,
                            6419592.484416135
                        ],
                        [
                            875466.7261499988,
                            6420232.644528024
                        ],
                        [
                            876369.6385466165,
                            6417843.987394109
                        ],
                        [
                            873235.7203869238,
                            6417882.205908254
                        ],
                        [
                            872891.7537596425,
                            6421742.275836656
                        ],
                        [
                            876235.873747117,
                            6421971.586921509
                        ],
                        [
                            875113.2048941795,
                            6420079.770471452
                        ]
                    ]
                ]
            }
        }
    ]
}


dummy_parcels = {
  "type": "FeatureCollection",
  "features": [
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              874375.1098397995,
              6419808.657886755
            ],
            [
              874375.1098397995,
              6419875.540286506
            ],
            [
              874462.892989472,
              6419875.540286506
            ],
            [
              874462.892989472,
              6419808.657886755
            ],
            [
              874375.1098397995,
              6419808.657886755
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-010-00023/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              874149.3817406459,
              6419983.029857529
            ],
            [
              874158.936369181,
              6419931.673729149
            ],
            [
              874230.5960831984,
              6419940.034029118
            ],
            [
              874264.0372830748,
              6420006.91642887
            ],
            [
              874259.2599688071,
              6420022.442700236
            ],
            [
              874149.3817406459,
              6419983.029857529
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-010-00021/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              874314.1990828865,
              6420407.016498799
            ],
            [
              874320.1707257202,
              6420261.308413627
            ],
            [
              874690.4125814778,
              6420262.502742195
            ],
            [
              874818.2057381407,
              6420288.777970671
            ],
            [
              874832.5376809436,
              6420372.380970359
            ],
            [
              874514.8462821357,
              6420401.0448559625
            ],
            [
              874314.1990828865,
              6420407.016498799
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-020-00013/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              874409.745368242,
              6420641.104897921
            ],
            [
              874320.1707257202,
              6420428.514413001
            ],
            [
              874809.8454381716,
              6420387.907241724
            ],
            [
              874746.5460241233,
              6420532.420998328
            ],
            [
              874635.4734673958,
              6420601.692055215
            ],
            [
              874468.2674680228,
              6420644.687883621
            ],
            [
              874409.745368242,
              6420641.104897921
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-020-00014/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              873851.9939274747,
              6420466.732927143
            ],
            [
              874119.523526471,
              6420246.976470826
            ],
            [
              874310.616097185,
              6420261.308413627
            ],
            [
              874301.0614686497,
              6420409.405155933
            ],
            [
              874028.754555383,
              6420418.959784469
            ],
            [
              873851.9939274747,
              6420466.732927143
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-020-00015/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              874855.2299237156,
              6420368.797984656
            ],
            [
              874838.5093237803,
              6420323.413499114
            ],
            [
              874852.8412665832,
              6420134.70958553
            ],
            [
              875043.9338372945,
              6420464.344270011
            ],
            [
              874924.5009806006,
              6420385.518584591
            ],
            [
              874855.2299237156,
              6420368.797984656
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072500-020-00016/000"
      }
    },
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              871181.4752517599,
              6420729.485211875
            ],
            [
              871105.0382234748,
              6420309.081556307
            ],
            [
              871277.0215371182,
              6420165.762128271
            ],
            [
              871410.786336615,
              6419745.358472706
            ],
            [
              871821.6353636489,
              6419850.4593865955
            ],
            [
              872404.4677043235,
              6420547.9472697
            ],
            [
              872595.5602750375,
              6420853.695382841
            ],
            [
              871181.4752517599,
              6420729.485211875
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "id": "072501-011-00974/000"
      }
    }
  ]
}
