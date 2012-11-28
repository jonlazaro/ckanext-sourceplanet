from setuptools import setup, find_packages
import sys
import os

version = '0.1'

setup(
    name='ckanext-sourceplanet',
    version=version,
    description="Sourceplanet integration plugin for CKAN.",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Jon Lazaro',
    author_email='jlazaro@deusto.es',
    url='http://www.morelab.deusto.es/',
        license='GPL',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        namespace_packages=['ckanext', 'ckanext.sourceplanet'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
                # -*- Extra requirements: -*-
        ],
    entry_points=
    """
    [ckan.plugins]
    sourceplanet=ckanext.sourceplanet.plugin:SourceplanetDatasetForm

    #[ckan.forms]
    #example_form=ckanext.sourceplanet.package_form:get_example_fieldset
    """,
)
