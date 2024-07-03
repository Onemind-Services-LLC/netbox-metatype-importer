from setuptools import find_packages, setup

setup(
    name='netbox-metatype-importer',
    version='0.4.0',
    description='Easily import Device and Module types from GitHub repo',
    long_description='Import MetaTypes into NetBox',
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
