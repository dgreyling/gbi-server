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

import csv as csvlib
from cStringIO import StringIO


def log_spec_to_csv(logs, csv_headers=[]):
    out = StringIO()
    writer = csvlib.writer(out, delimiter=",")

    # write headers to csv
    writer.writerow(csv_headers)

    # add logs to csv
    for log in logs:
        writer.writerow([
            log.time,
            log.action,
            log.format,
            log.srs,
            log.mapping,
            log.source,
            log.layer,
            log.zoom_level_start,
            log.zoom_level_end,
            log.refreshed,
            log.geometry_as_geojson,
        ])

    out.seek(0)
    return out.read()
