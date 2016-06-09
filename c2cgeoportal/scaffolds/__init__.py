# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014, Camptocamp SA
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


import re
import subprocess
import os
import json
import requests
import yaml
from six import string_types

from pyramid.scaffolds.template import Template
from pyramid.compat import input_
from c2cgeoportal.lib.bashcolor import colorize, GREEN


class BaseTemplate(Template):  # pragma: no cover
    """
    A class that can be used as a base class for c2cgeoportal scaffolding
    templates.

    Greatly inspired from ``pyramid.scaffolds.template.PyramidTemplate``.
    """

    def pre(self, command, output_dir, vars):
        """
        Overrides ``pyramid.scaffold.template.Template.pre``, adding
        several variables to the default variables list. Also prevents
        common misnamings (such as naming a package "site" or naming a
        package logger "root").
        """

        ret = Template.pre(self, command, output_dir, vars)

        if vars["package"] == "site":
            raise ValueError(
                "Sorry, you may not name your package 'site'. "
                "The package name 'site' has a special meaning in "
                "Python.  Please name it anything except 'site'.")

        package_logger = vars["package"]
        if package_logger == "root":
            # Rename the app logger in the rare case a project
            # is named "root"
            package_logger = "app"
        vars["package_logger"] = package_logger

        return ret

    def out(self, msg):
        print(msg)

    def _args_to_vars(self, args, vars):
        for arg in args:
            m = re.match("(.+)=(.*)", arg)
            if m:
                vars[m.group(1)] = m.group(2)


class TemplateCreate(BaseTemplate):  # pragma: no cover
    _template_dir = "create"
    summary = "Template used to create a c2cgeoportal project"

    def pre(self, command, output_dir, vars):
        """
        Overrides the base template, adding the "srid" variable to
        the variables list.
        """

        self._args_to_vars(command.args, vars)

        self._get_vars(vars, "package", "Get a package name: ")
        self._get_vars(vars, "apache_vhost", "The Apache vhost name: ")
        self._get_vars(
            vars, "srid",
            "Spatial Reference System Identifier (e.g. 21781): ", int,
        )
        srid = vars["srid"]
        extent = self._epsg2bbox(srid)
        self._get_vars(
            vars, "extent",
            "Extent (minx miny maxx maxy): in EPSG: {srid} projection, default is "
            "[{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}]: ".format(srid=srid, bbox=extent)
            if extent else
            "Extent (minx miny maxx maxy): in EPSG: {srid} projection: ".format(srid=srid)
        )
        match = re.match(r"(\d+)[,; ] *(\d+)[,; ] *(\d+)[,; ] *(\d+)", vars["extent"])
        if match is not None:
            extent = [match.group(n + 1) for n in range(4)]
        vars["extent"] = ", ".join(extent)
        vars["extent_mapserver"] = " ".join(extent)
        vars["extent_viewer"] = json.dumps(extent)

        return BaseTemplate.pre(self, command, output_dir, vars)

    def _get_vars(self, vars, name, prompt, type=None):
        """
        Set an attribute in the vars dict.
        """

        value = vars.get(name)

        if value is None:
            value = input_(prompt).strip()

        if type is not None:
            try:
                type(value)
            except ValueError:
                exit("The attribute {} is not a {}".format(name, type))

        vars[name] = value

    def post(self, command, output_dir, vars):
        """
        Overrides the base template class to print the next step.
        """

        if os.name == 'posix':
            for file in ("post-restore-code", "pre-restore-database.mako"):
                dest = os.path.join(output_dir, "deploy/hooks", file)
                subprocess.check_call(["chmod", "+x", dest])

        self.out("\nContinue with:")
        self.out(colorize(
            ".build/venv/bin/pcreate -s c2cgeoportal_update ../{vars[project]} "
            "package={vars[package]} srid={vars[srid]}".format(vars=vars),
            GREEN
        ))

        return BaseTemplate.post(self, command, output_dir, vars)

    def _epsg2bbox(self, srid):
        try:
            r = requests.get("http://epsg.io/?format=json&q={}".format(srid))
            bbox = r.json()["results"][0]["bbox"]
            r = requests.get(
                "http://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[1]},{bbox[0]}"
                .format(srid=srid, bbox=bbox)
            )
            r1 = r.json()[0]
            r = requests.get(
                "http://epsg.io/trans?s_srs=4326&t_srs={srid}&data={bbox[3]},{bbox[2]}"
                .format(srid=srid, bbox=bbox)
            )
            r2 = r.json()[0]
            return [r1["x"], r2["y"], r2["x"], r1["y"]]
        except IndexError:
            print("Unable to get the bbox")
            return None


class TemplateUpdate(BaseTemplate):  # pragma: no cover
    _template_dir = "update"
    summary = "Template used to update a c2cgeoportal project"

    def pre(self, command, output_dir, vars):
        """
        Overrides the base template
        """

        if os.path.exists("project.yaml"):
            with open("project.yaml", "r") as f:
                project = yaml.load(f)
                if "template_vars" in project:
                    for key, value in project["template_vars"].items():
                        vars[key] = \
                            value.encode("utf-8") \
                            if isinstance(value, string_types) \
                            else value

        self._args_to_vars(command.args, vars)

        return BaseTemplate.pre(self, command, output_dir, vars)

    def post(self, command, output_dir, vars):
        if os.name == 'posix':
            dest = os.path.join(output_dir, ".whiskey/action_hooks/pre-build.mako")
            subprocess.check_call(["chmod", "+x", dest])
        """
        Overrides the base template class to print "Welcome to c2cgeoportal!"
        after a successful scaffolding rendering.
        """

        self.out(colorize("\nWelcome to c2cgeoportal!", GREEN))

        return BaseTemplate.post(self, command, output_dir, vars)