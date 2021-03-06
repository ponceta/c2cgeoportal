# -*- coding: utf-8 -*-

# Copyright (c) 2013-2019, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

# pylint: disable=missing-docstring,attribute-defined-outside-init,protected-access


import json
import logging
import re
from unittest import TestCase

import transaction
from geoalchemy2 import WKTElement
from pyramid import testing
from tests.functional import cleanup_db, create_default_ogcserver, create_dummy_request, mapserv_url
from tests.functional import setup_common as setup_module  # noqa, pylint: disable=unused-import
from tests.functional import teardown_common as teardown_module  # noqa, pylint: disable=unused-import

LOG = logging.getLogger(__name__)


class TestEntryView(TestCase):

    def setup_method(self, _):
        # Always see the diff
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None  # pylint: disable=invalid-name
        self._tables = []

        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role, \
            RestrictionArea, Theme, LayerGroup, Functionality, Interface, \
            LayerWMS, OGCServer, FullTextSearch, OGCSERVER_TYPE_GEOSERVER, OGCSERVER_AUTH_GEOSERVER
        from c2cgeoportal_commons.models.static import User
        from sqlalchemy import Column, Table, types, func
        from sqlalchemy.ext.declarative import declarative_base
        from geoalchemy2 import Geometry

        cleanup_db()

        role1 = Role(name="__test_role1")
        user1 = User(username="__test_user1", password="__test_user1", settings_role=role1, roles=[role1])
        user1.email = "__test_user1@example.com"

        role2 = Role(name="__test_role2", extent=WKTElement(
            "POLYGON((1 2, 1 4, 3 4, 3 2, 1 2))", srid=21781
        ))
        user2 = User(username="__test_user2", password="__test_user2", settings_role=role2, roles=[role2])

        main = Interface(name="desktop")
        mobile = Interface(name="mobile")

        engine = DBSession.c2c_rw_bind
        engine.connect()

        a_geo_table = Table(
            "a_geo_table", declarative_base(bind=engine).metadata,
            Column("id", types.Integer, primary_key=True),
            Column("geom", Geometry("POINT", srid=21781)),
            schema="geodata"
        )

        self._tables = [a_geo_table]
        a_geo_table.drop(checkfirst=True)
        a_geo_table.create()

        ogcserver, _ = create_default_ogcserver()

        private_layer_edit = LayerWMS(name="__test_private_layer_edit", public=False)
        private_layer_edit.layer = "__test_private_layer"
        private_layer_edit.geo_table = "a_schema.a_geo_table"
        private_layer_edit.interfaces = [main, mobile]
        private_layer_edit.ogc_server = ogcserver

        public_layer2 = LayerWMS(name="__test_public_layer", layer="__test_public_layer_bis", public=True)
        public_layer2.interfaces = [main, mobile]
        public_layer2.ogc_server = ogcserver

        private_layer = LayerWMS(
            name="__test_private_layer", layer="__test_private_layer_bis", public=False)
        private_layer.interfaces = [main, mobile]
        private_layer.ogc_server = ogcserver

        interface_not_in_mapfile = Interface(name="interface_not_in_mapfile")
        public_layer_not_in_mapfile = LayerWMS(
            name="__test_public_layer_not_in_mapfile",
            layer="__test_public_layer_not_in_mapfile", public=True)
        public_layer_not_in_mapfile.interfaces = [interface_not_in_mapfile]
        public_layer_not_in_mapfile.ogc_server = ogcserver

        interface_notmapfile = Interface(name="interface_notmapfile")
        ogcserver_notmapfile = OGCServer(name="__test_ogc_server_notmapfile")
        ogcserver_notmapfile.url = mapserv_url + "?map=not_a_mapfile"
        public_layer_not_mapfile = LayerWMS(
            name="__test_public_layer_notmapfile", layer="__test_public_layer_notmapfile", public=True)
        public_layer_not_mapfile.interfaces = [interface_notmapfile]
        public_layer_not_mapfile.ogc_server = ogcserver_notmapfile

        interface_geoserver = Interface(name="interface_geoserver")
        ogcserver_geoserver = OGCServer(name="__test_ogc_server_geoserver")
        ogcserver_geoserver.url = mapserv_url
        ogcserver_geoserver.type = OGCSERVER_TYPE_GEOSERVER
        ogcserver_geoserver.auth = OGCSERVER_AUTH_GEOSERVER
        public_layer_geoserver = LayerWMS(
            name="__test_public_layer_geoserver", layer="__test_public_layer_geoserver", public=True
        )
        public_layer_geoserver.interfaces = [interface_geoserver]
        public_layer_geoserver.ogc_server = ogcserver_geoserver

        interface_no_layers = Interface(name="interface_no_layers")
        public_layer_no_layers = LayerWMS(name="__test_public_layer_no_layers", public=True)
        public_layer_no_layers.interfaces = [interface_no_layers]
        public_layer_no_layers.ogc_server = ogcserver

        group = LayerGroup(name="__test_layer_group")
        group.children = [
            private_layer_edit, public_layer2, public_layer_not_in_mapfile, public_layer_not_mapfile,
            public_layer_geoserver, public_layer_no_layers, private_layer
        ]
        theme = Theme(name="__test_theme")
        theme.children = [group]
        theme.interfaces = [
            main, interface_not_in_mapfile, interface_notmapfile, interface_geoserver, interface_no_layers
        ]

        functionality1 = Functionality(name="test_name", value="test_value_1")
        functionality2 = Functionality(name="test_name", value="test_value_2")
        theme.functionalities = [functionality1, functionality2]

        poly = "POLYGON((-100 0, -100 20, 100 20, 100 0, -100 0))"

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name="__test_ra1", description="", layers=[private_layer_edit, private_layer],
            roles=[role1], area=area
        )

        area = WKTElement(poly, srid=21781)
        RestrictionArea(
            name="__test_ra2", description="", layers=[private_layer_edit, private_layer],
            roles=[role2], area=area, readwrite=True
        )

        entry1 = FullTextSearch()
        entry1.label = "label1"
        entry1.layer_name = "layer1"
        entry1.ts = func.to_tsvector("french", "soleil travail")
        entry1.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry1.public = True

        entry2 = FullTextSearch()
        entry2.label = "label1"
        entry2.layer_name = "layer1"
        entry2.ts = func.to_tsvector("french", "soleil travail")
        entry2.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry2.public = True

        entry3 = FullTextSearch()
        entry3.label = "label1"
        entry3.layer_name = None
        entry3.ts = func.to_tsvector("french", "soleil travail")
        entry3.the_geom = WKTElement("POINT(-90 -45)", 21781)
        entry3.public = True

        DBSession.add_all([user1, user2, theme, entry1, entry2, entry3])
        DBSession.flush()

        self.role1_id = role1.id

        transaction.commit()

    def teardown_method(self, _):
        testing.tearDown()

        cleanup_db()

    #
    # login/logout tests
    #

    def test_login(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(params={
            "came_from": "/came_from",
        }, POST={
            "login": "__test_user1",
            "password": "__test_user1",
        })
        response = Entry(request).login()
        assert response.status_int == 302
        assert response.headers["Location"] == "/came_from"

        request = self._create_request_obj(POST={
            "login": "__test_user1",
            "password": "__test_user1",
        })
        response = Entry(request).login()
        assert response.status_int == 200
        assert json.loads(response.body.decode("utf-8")) == {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": False,
            "roles": [{
                "name": "__test_role1",
                "id": self.role1_id,
            }],
            "functionalities": {},
        }

        request = self._create_request_obj(POST={
            "login": "__test_user1",
            "password": "bad password",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.login)

    def test_logout_no_auth(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(path="/", params={
            "came_from": "/came_from"
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.logout)

    def test_logout(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(path="/")
        request.user = DBSession.query(User).filter_by(
            username="__test_user1"
        ).one()
        response = Entry(request).logout()
        assert response.status_int == 200
        assert response.body.decode("utf-8") == "true"

        request = self._create_request_obj(path="/")
        request.route_url = lambda url: "/dummy/route/url"
        request.user = DBSession.query(User).filter_by(
            username="__test_user1"
        ).one()
        response = Entry(request).logout()
        assert response.status_int == 200
        assert response.body.decode("utf-8") == "true"

    def test_reset_password(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(POST={
            "login": "__test_user1",
        })
        entry = Entry(request)
        _, username, password, _ = entry._loginresetpassword()

        request = self._create_request_obj(POST={
            "login": username,
            "password": password,
        })
        response = Entry(request).login()
        assert response.status_int == 200
        assert json.loads(response.body.decode("utf-8")) == {
            "success": True,
            "username": "__test_user1",
            "is_password_changed": False,
            "roles": [{
                "name": "__test_role1",
                "id": self.role1_id,
            }],
            "functionalities": {},
        }

        user = DBSession.query(User).filter(User.username == '__test_user1').first()
        self.assertIsNone(user.temp_password)
        self.assertIsNotNone(user.password)
        self.assertNotEqual(len(user.password), 0)

    #
    # viewer view tests
    #

    @staticmethod
    def _create_request_obj(username=None, params=None, **kwargs):
        if params is None:
            params = {}
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User

        request = create_dummy_request(**kwargs)
        request.static_url = lambda url: "/dummy/static/url"
        request.route_url = lambda url, **kwargs: mapserv_url
        request.interface_name = "desktop"
        request.params = params

        if username is not None:
            request.user = DBSession.query(User) \
                .filter_by(username=username).one()

        return request

    def _create_entry_obj(self, **kwargs):
        from c2cgeoportal_geoportal.views.entry import Entry

        return Entry(self._create_request_obj(**kwargs))

    @staticmethod
    def _get_filtered_errors(errors):
        regex = re.compile(
            r"The layer \'[a-z0-9_]*\' \([a-z0-9_]*\) is not defined in WMS capabilities from \'[a-z0-9_]*\'"
        )
        errors = [e for e in errors if not regex.match(e)]
        return set(errors)

    def test_theme(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.static import User
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated
        themes, errors = entry._themes()
        assert {e[:90] for e in errors} == set()
        assert len(themes) == 1
        groups = {g["name"] for g in themes[0]["children"]}
        assert groups == {
            "__test_layer_group",
        }
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        assert layers == {
            "__test_public_layer",
        }

        # authenticated
        request.params = {}
        request.user = DBSession.query(User).filter_by(username="__test_user1").one()
        themes, errors = entry._themes()
        assert {e[:90] for e in errors} == set()
        assert len(themes) == 1
        groups = {g["name"] for g in themes[0]["children"]}
        assert groups == {
            "__test_layer_group",
        }
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        assert layers == {
            "__test_private_layer_edit",
            "__test_public_layer",
            "__test_private_layer",
        }

    def test_no_layers(self):
        # mapfile error
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)
        request.params = {}

        from c2cgeoportal_geoportal.lib import caching
        caching.invalidate_region()
        themes, errors = entry._themes("interface_no_layers")
        assert themes == []
        assert {e[:90] for e in errors} == {
            "The layer '__test_public_layer_no_layers' do not have any layers",
        }

    def test_not_in_mapfile(self):
        # mapfile error
        from c2cgeoportal_geoportal.views.entry import Entry
        entry = Entry(self._create_request_obj())

        from c2cgeoportal_geoportal.lib import caching
        caching.invalidate_region()
        themes, errors = entry._themes("interface_not_in_mapfile")
        assert len(themes) == 1
        groups = {g["name"] for g in themes[0]["children"]}
        assert groups == {
            "__test_layer_group",
        }
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        assert layers == {
            "__test_public_layer_not_in_mapfile",
        }
        assert {e[:90] for e in errors} == {
            "The layer '__test_public_layer_not_in_mapfile' (__test_public_layer_not_in_mapfile) is not",
        }

    def test_notmapfile(self):
        # mapfile error
        from c2cgeoportal_geoportal.views.entry import Entry
        entry = Entry(self._create_request_obj())

        from c2cgeoportal_geoportal.lib import caching
        caching.invalidate_region()
        themes, errors = entry._themes("interface_notmapfile")
        assert len(themes) == 1
        groups = {g["name"] for g in themes[0]["children"]}
        assert groups == {
            "__test_layer_group",
        }
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        assert layers == {
            "__test_public_layer_notmapfile",
        }
        assert {e[:90] for e in errors} == {
            "The layer '__test_public_layer_notmapfile' (__test_public_layer_notmapfile) is not defined",
            "GetCapabilities from URL http://mapserver:8080/?map=not_a_mapfile&SERVICE=WMS&VERSION=1.1."
        }

    def test_theme_geoserver(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        request = self._create_request_obj()
        entry = Entry(request)

        # unautenticated v1
        themes, errors = entry._themes("interface_geoserver")
        assert {e[:90] for e in errors} == {
            "The layer '__test_public_layer_geoserver' (__test_public_layer_geoserver) is not defined i"
        }
        assert len(themes) == 1
        layers = {l["name"] for l in themes[0]["children"][0]["children"]}
        assert layers == {
            "__test_public_layer_geoserver",
        }

    def _create_entry(self):
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj()
        request.current_route_url = lambda **kwargs: "http://example.com/current/view"
        request.registry.settings.update({
            "layers": {
                "enum": {
                    "layer_test": {
                        "attributes": {
                            "label": None
                        }
                    }
                }
            },
            "api": {
                "ogc_server": "__test_ogc_server"
            }
        })
        request.matchdict = {
            "themes": ["theme"],
        }
        entry = Entry(request)
        request.user = None
        return entry, request

    def test_entry_points(self):
        entry, _ = self._create_entry()

        result = entry.apijs()
        assert set(result.keys()) == {"lang", "debug", "queryable_layers", "tiles_url", "url_params"}
        result = entry.xapijs()
        assert set(result.keys()) == {"lang", "debug", "queryable_layers", "tiles_url", "url_params"}
        result = entry.apihelp()
        assert set(result.keys()) == {"lang", "debug"}
        result = entry.xapihelp()
        assert set(result.keys()) == {"lang", "debug"}

    def _assert_has_error(self, errors, error):
        self.assertIn(error, errors)
        assert len([e for e in errors if e == error]) == 1, \
            "Error '{}' more than one time in errors:\n{!r}".format(error, errors)

    def test_loginchange_no_params(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={})
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_wrong_old(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "",
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_different(self):
        from pyramid.httpexceptions import HTTPBadRequest
        from c2cgeoportal_geoportal.views.entry import Entry

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "12345",
        })
        entry = Entry(request)
        self.assertRaises(HTTPBadRequest, entry.loginchange)

    def test_loginchange_good_is_password_changed(self):
        from c2cgeoportal_geoportal.views.entry import Entry
        from hashlib import sha1

        request = self._create_request_obj(username="__test_user1", params={
            "lang": "en"
        }, POST={
            "oldPassword": "__test_user1",
            "newPassword": "1234",
            "confirmNewPassword": "1234"
        })
        assert request.user.is_password_changed is False
        assert request.user._password == str(sha1("__test_user1".encode("utf-8")).hexdigest())
        entry = Entry(request)
        self.assertNotEqual(entry.loginchange(), None)
        assert request.user.is_password_changed is True
        assert request.user._password == str(sha1("1234".encode("utf-8")).hexdigest())

    def test_json_extent(self):
        from c2cgeoportal_commons.models import DBSession
        from c2cgeoportal_commons.models.main import Role

        role = DBSession.query(Role).filter(Role.name == "__test_role1").one()
        assert role.bounds is None

        role = DBSession.query(Role).filter(Role.name == "__test_role2").one()
        assert role.bounds == (1, 2, 3, 4)
