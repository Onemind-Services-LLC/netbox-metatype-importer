ARG NETBOX_VARIANT=v4.2

FROM netboxcommunity/netbox:${NETBOX_VARIANT}

RUN mkdir -pv /plugins/netbox-metatype-importer
COPY . /plugins/netbox-metatype-importer

RUN /opt/netbox/venv/bin/python3 /plugins/netbox-metatype-importer/setup.py develop
RUN cp -rf /plugins/netbox-metatype-importer/netbox_metatype_importer/ /opt/netbox/venv/lib/python3.12/site-packages/netbox_metatype_importer
