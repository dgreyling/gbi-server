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

# -:- encoding: utf8 -:-
from os import path as p
from flask.ext.babel import lazy_gettext as _l

class DefaultConfig(object):
    """
    Default configuration
    """

    TESTING = False

    DEBUG = True

    # config for pagination
    USER_PER_PAGE = 2

    WTF_I18N_ENABLED = True

    SESSION_COOKIE_NAME = 'gbi_server_session'

    # allow access to admin URLs without authentication
    # (e.g. for testing with curl)
    ADMIN_PARTY = False

    # change this in your production settings !!!

    SECRET_KEY = "verysecret"

    # keys for localhost. Change as appropriate.

    SQLALCHEMY_DATABASE_URI = 'postgresql://igreen:igreen@127.0.0.1:5432/igreen'
    SQLALCHEMY_ECHO = False
    # from warning: SQLALCHEMY_TRACK_MODIFICATIONS adds significant overhead and will be disabled by default in the future.
    # TODO check if tracking is required
    SQLALCHEMY_TRACK_MODIFICATIONS=True

    ACCEPT_LANGUAGES = ['de']

    ASSETS_DEBUG = True
    ASSETS_BUNDLES_CONF = p.join(p.dirname(__file__), 'asset_bundles.yaml')

    LOG_DIR = p.abspath(p.join(p.dirname(__file__), '../../var/log'))
    DEBUG_LOG = 'debug.log'
    ERROR_LOG = 'error.log'

    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300

    BCRYPT_LOG_ROUNDS = 10

    MAIL_SERVER = "localhost"
    MAIL_USERNAME = 'gbi_server@example.org'
    MAIL_PASSWORD = 'XXXXX'
    MAIL_DEBUG = DEBUG
    MAIL_DEFAULT_SENDER = "GeoBox Server <gbi_server@example.org>"

    TINYOWS_NAME = "TinyOWS Server"
    TINYOWS_TITLE = "TinyOWS Server - Demo Service"
    TINYOWS_BIN = "/usr/local/bin/tinyows"
    TINYOWS_SCHEMA_DIR = "/usr/local/share/tinyows/schema/"
    TINYOWS_LOG_FILE = "/tmp/tinyows.log"
    TINYOWS_LOG_LEVEL = "7"
    TINYOWS_NS_PREFIX = "tows"
    TINYOWS_NS_URI = "http://www.tinyows.org/"

    TINYOWS_TMP_CONFIG_DIR = "/tmp/tinyows"
    TEMP_PG_HOST = "127.0.0.1"
    TEMP_PG_DB = "wfs_tmp"
    TEMP_PG_USER = "igreen"
    TEMP_PG_PASSWORD = "igreen"
    TEMP_PG_PORT = "5432"

    USER_READONLY_LAYER = "florlp"
    USER_READONLY_LAYER_TITLE = "FLOrlp"
    USER_WORKON_LAYER = "baselayer"
    USER_WORKON_LAYER_TITLE ="Basis Layer"

    COUCH_DB_URL = "http://127.0.0.1:5984"
    # user name and password for db admin that is allowed to
    # create new user boxes
    COUCH_DB_ADMIN_USER = 'admin'
    COUCH_DB_ADMIN_PASSWORD = 'secure'

    AUTHPROXY_CACHE_DIR = "/tmp/authproxy"

    MAPPROXY_SRS = ['EPSG:25832']
    MAPPROXY_YAML_DIR = "/tmp/"

    GBI_CLIENT_DOWNLOAD_URL = "http://download.omniscale.de/geobox/dist/setup-geobox-0.2.7.exe"

    STATIC_PAGES_DIR = p.join(p.dirname(__file__), '..', 'pages')
    USERMANUAL_FILENAME = 'usermanual-gbi-server.pdf'

    # enable/disable document boxes (CUSTOMER/CONSULTANT)
    FEATURE_DOC_BOXES = True
    # enable/disable area boxes
    FEATURE_AREA_BOXES = True

    # enable WFS editor
    FEATURE_EDITOR = True

    # allow CUSTOMER accounts
    FEATURE_CUSTOMER_USERS = True
    # allow CONSULTANT accounts
    FEATURE_CONSULTANT_USERS = True

    SALUTATIONS = [
        ('mr', _l(u'mr')),
        ('mrs', _l(u'mrs')),
    ]

    FEDERAL_STATES = [
        ('BW', _l(u'Baden-Wuerttemberg')),
        ('BY', _l(u'Bavaria')),
        ('BE', _l(u'Berlin')),
        ('BB', _l(u'Brandenburg')),
        ('HB', _l(u'Bremen')),
        ('HH', _l(u'Hamburg')),
        ('HE', _l(u'Hesse')),
        ('MV', _l(u'Mecklenburg Western Pomerania')),
        ('NI', _l(u'Lower Saxony')),
        ('NW', _l(u'Northrhine-Westphalia')),
        ('RP', _l(u'Rhineland Palatinate')),
        ('SL', _l(u'Saarland')),
        ('SN', _l(u'Saxony')),
        ('ST', _l(u'Saxony-Anhalt')),
        ('SH', _l(u'Schleswig Holstein')),
        ('TH', _l(u'Thuringia')),
    ]

    PORTAL_PREFIX = "DEFAULT"
    PORTAL_TITLE = "Unconfigured GeoBox-Server"


class SystemConfig(object):
    # name of the databases on the server
    # will be suffixed by the user id
    AREA_BOX_NAME = 'gbi_flaechenbox'
    UPLOAD_BOX_NAME = 'gbi_uploadbox'
    DOWNLOAD_BOX_NAME = 'gbi_downloadbox'
    FILE_BOX_NAME = 'gbi_filebox'

    # name of the databases on the client
    AREA_BOX_NAME_LOCAL = 'flaechen-box'
    UPLOAD_BOX_NAME_LOCAL = 'upload-box'
    DOWNLOAD_BOX_NAME_LOCAL = 'download-box'
    FILE_BOX_NAME_LOCAL = 'filebox'