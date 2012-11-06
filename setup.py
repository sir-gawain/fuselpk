from setuptools import setup, find_packages
import sys, os

version = '0.1'

requirements = [
          'fuse-python >=0.2',
      ]

# python-ldap compilation and installation
# is so boring under *bsdsystems ...
try:
    import ldap
except ImportError:
    requirements.append('python-ldap')
    
setup(name='fuselpk',
      version=version,
      description="LDAP Public Key filesystem for openssh",
      long_description=open('README'),
      classifiers=['Operating System :: Unix',
                   'Topic :: System :: Filesystems'], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='ldap ssh authentication fuse',
      author='Fr\xc3\xa9d\xc3\xa9ric Dupr\xc3\xa9 (Alterway group)',
      author_email='frederic.dupre@gmail.com',
      url='',
      license='GPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requirements,
      entry_points={
        'console_scripts': [
            'fuselpk = fuselpk.main:start',
            ],
      },
      )
