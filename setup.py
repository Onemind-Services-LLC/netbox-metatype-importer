import codecs
import os.path

from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

setup(
    name='netbox-metatype-importer',
    version='0.0.1',
    description='Import MetaTypes from github repo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/k01ek/netbox-metatype-importer',
    author='Abhimanyu Saharan',
    author_email='asaharan@onemindservices.com',
    maintainer='Prince Kumar',
    maintainer_email='pkumar@onemindservices.com',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ]
)
