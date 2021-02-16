from setuptools import setup, find_packages
import versioneer

requirements = [
    # package requirements go here
]

setup(
    name='intake-salesforce',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Intake driver to load Salesforce data",
    license="BSD",
    author="Sophia Yang",
    url='https://github.com/sophiamyang/intake-salesforce',
    packages=find_packages(),
    entry_points={
        'intake.drivers': [
            'salesforce_catalog = intake_salesforce.core:SalesforceCatalog',
            'salesforce_table = intake_salesforce.core:SalesforceTableSource',
            ]
    },
    install_requires=[
        'simple_salesforce',
        'intake',
        'pandas'
    ],
    keywords='intake-salesforce',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)
