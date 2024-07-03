# Netbox DeviceType/ModuleType Import Plugin
[NetBox](https://github.com/netbox-community/netbox) plugin for easy import DeviceType and ModuleType from [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library). This is the continuation of the [Netbox DeviceType Import Plugin](https://github.com/k01ek/netbox-devicetype-importer) app.

## Description
The plugin uses [GitHub GraphQL API](https://docs.github.com/en/graphql) to load DeviceType and ModuleType from [NetBox Device Type Library](https://github.com/netbox-community/devicetype-library). The plugin loads only file tree representation from GitHub repo and shows it as a table with vendor and model columns. DeviceType definitions files are loaded when you try to import selected models.
To use GraphQL API you need to set GitHub personal access token in plugin settings. How to create the token, see ["Creating a personal access token."](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token)

## Compatibility

| NetBox Version | Plugin Version |
|:--------------:|:--------------:|
|     3.4.x      |     0.0.x      |
|     3.5.x      |     0.1.x      |
|     3.6.x      |     0.2.x      |
|     3.7.x      |     0.3.x      |
|     4.0.x      |     0.4.x      |

## Installation

* Install NetBox as per NetBox documentation
* Add to local_requirements.txt:
  * `netbox-metatype-importer`
* Install requirements: `./venv/bin/pip install -r local_requirements.txt`
* Add to PLUGINS in NetBox configuration:
  * `'netbox_metatype_importer',`
* Run migration: `./venv/bin/python netbox/manage.py migrate`

## Configuration

The following options are available in the configuration file:

- `branch`
  - __Type__: `String`
  - __Description__: Branch of the NetBox Device Type Library repo
  - __Default__: `master`
- `github_token`
  - __Type__: `String`
  - __Description__: GitHub personal access token
- `repo`
  - __Type__: `String`
  - __Description__: Name of the NetBox Device Type Library repo
  - __Default__: `devicetype-library`
- `repo_owner`
  - __Type__: `String`
  - __Description__: Owner of the NetBox Device Type Library repo
  - __Default__: `netbox-community`
