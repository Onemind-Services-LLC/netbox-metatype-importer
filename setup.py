import os

from setuptools import find_packages, setup

description = "Easily import Device and Module types from GitHub repo"

readme = os.path.join(os.path.dirname(__file__), 'README.md')

with open(readme) as fh:
    long_description = fh.read()

setup(
    name='netbox-metatype-importer',
    version='0.7.0',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Onemind-Services-LLC/netbox-metatype-importer',
    author='Abhimanyu Saharan',
    author_email='asaharan@onemindservices.com',
    maintainer='Prince Kumar',
    maintainer_email='pkumar@onemindservices.com',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Programming Language :: Python :: 3',
    ],
)
