FROM camptocamp/geomapfish-qgisserver:gmf2.4-qgis3.4

COPY requirements.txt /tmp/

RUN python3 -m pip install --requirement /tmp/requirements.txt

COPY geomapfish.yaml /etc/qgisserver/geomapfish.yaml
COPY multiple_ogc_server.yaml /etc/qgisserver/multiple_ogc_server.yaml
COPY ./functional /acceptance_tests/functional

ENV PYTHONPATH /var/www/plugins:/usr/local/share/qgis/python/

RUN mkdir -p /pytest && chmod 777 /pytest
WORKDIR /pytest

CMD ["py.test", "--verbose", "--color=yes", "--cov=geomapfish_qgisserver", "/acceptance_tests"]
