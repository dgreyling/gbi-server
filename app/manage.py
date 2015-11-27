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

from scriptine.shell import sh

from flask.ext.script import Manager, Server

from gbi_server import create_app
from gbi_server.model import fixtures
from gbi_server.extensions import db

manager = Manager(create_app)

#############################
# Babel commands
#############################
@manager.command
def babel_init_lang(lang):
    "Initialize new language."
    sh('pybabel init -i ../app/gbi_server/translations/messages.pot -d gbi_server/translations -l %s' % (lang,))


@manager.command
def babel_refresh():
    "Extract messages and update translation files."
    sh('pybabel extract -F ../app/babel.cfg -k lazy_gettext -k _l -o ../app/gbi_server/translations/messages.pot ../app/gbi_server ../app/gbi_server/model ../app/gbi_server/lib')
    sh('pybabel update -i ../app/gbi_server/translations/messages.pot -d ../app/gbi_server/translations')


@manager.command
def babel_compile():
    "Compile translations."
    sh('pybabel compile -d ../app/gbi_server/translations')


@manager.command
def create_db():
    db.drop_all()
    db.create_all()

@manager.command
def fixtures():
    "Creates database tables with fixtures"
    db.drop_all()
    db.create_all()

    from gbi_server.model import fixtures
    db.session.add_all(fixtures.all())
    db.session.commit()
    with manager. app.test_request_context():
        fixtures.init_couchdb(manager.app.config)

manager.add_command("runserver", Server(threaded=True))

if __name__ == '__main__':
    manager.run()
