ARG NETBOX_VARIANT=v3.4

FROM registry.tangience.net/netbox/netbox:${NETBOX_VARIANT}

USER root

# Remove pre-installed plugin
RUN rm -rf /usr/local/lib/python3.10/site-packages/netbox_metatype_importer

RUN mkdir -pv /plugins/netbox-metatype-importer
COPY . /plugins/netbox-metatype-importer

RUN python3 /plugins/netbox-metatype-importer/setup.py develop
RUN cp -rf /plugins/netbox-metatype-importer/netbox_metatype_importer/ /usr/local/lib/python3.10/site-packages/netbox_metatype_importer

USER $USER
