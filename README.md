# Netbox DeviceType Import Plugin
[NetBox](https://github.com/netbox-community/netbox) plugin for easy import DeviceType and ModuleType from [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library). This is the continuation of the [Netbox DeviceType Import Plugin](https://github.com/k01ek/netbox-devicetype-importer) app.

## Description
The plugin uses [GitHub GraphQL API](https://docs.github.com/en/graphql) to load DeviceType and ModuleType from [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library). The plugin loads only file tree representation from GitHub repo and shows it as a table with vendor and model columns. DeviceType definitions files are loaded when you try to import selected models.
To use GraphQL API you need to set GitHub personal access token in plugin settings. How to create the token, see ["Creating a personal access token."](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)

## Compatibility

This plugin in compatible with [NetBox](https://netbox.readthedocs.org/) 3.0 and later

## Installation

The plugin is available as a Python package in pypi and can be installed with pip

```
pip install git+https://github.com/Onemind-Services-LLC/netbox-metatype-importer.git
```
Enable the plugin in [NetBox Configuration](https://netbox.readthedocs.io/en/stable/configuration/)
```
PLUGINS = ['netbox_metatype_importer']
```

## Configuration
Put your GitHub personal access token to [NetBox plugins config](https://netbox.readthedocs.io/en/stable/configuration/optional-settings/#plugins_config)
```
PLUGINS_CONFIG = {
    'netbox_metatype_importer': {
        'github_token': '<YOUR-GITHUB-TOKEN>'
    }
}
```

## Future 
* Import device images from GitHub repo

