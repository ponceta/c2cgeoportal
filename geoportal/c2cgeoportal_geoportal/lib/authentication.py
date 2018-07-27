# -*- coding: utf-8 -*-

# Copyright (c) 2014-2018, Camptocamp SA
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


from pyramid.authentication import AuthTktAuthenticationPolicy, \
    BasicAuthAuthenticationPolicy
from pyramid_multiauth import MultiAuthenticationPolicy

from c2cgeoportal_geoportal.resources import defaultgroupsfinder


def create_authentication(settings):
    timeout = settings.get("authtkt_timeout")
    timeout = None if timeout is None else int(timeout)
    reissue_time = settings.get("reissue_time")
    reissue_time = None if reissue_time is None else int(reissue_time)
    cookie_authentication_policy = AuthTktAuthenticationPolicy(
        settings["authtkt_secret"],
        callback=defaultgroupsfinder,
        cookie_name=settings["authtkt_cookie_name"],
        timeout=timeout, max_age=timeout, reissue_time=reissue_time,
        hashalg="sha512", http_only=True, secure=True,
    )
    basic_authentication_policy = BasicAuthAuthenticationPolicy(c2cgeoportal_check)
    policies = [cookie_authentication_policy, basic_authentication_policy]
    return MultiAuthenticationPolicy(policies)


def c2cgeoportal_check(username, password, request):  # pragma: no cover
    if request.registry.validate_user(request, username, password):
        return defaultgroupsfinder(username, request)
    return None
