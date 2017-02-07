import os
import re
from setuptools import setup

# Get the version (borrowed from SQLAlchemy)
base_path = os.path.dirname(__file__)
with open(os.path.join(base_path, 'picklepipe', '__init__.py')) as fp:
    VERSION = re.compile(r'.*__version__ = \'(.*?)\'', re.S).match(fp.read()).group(1)


with open('README.rst') as f:
    readme = f.read()

with open('CHANGELOG.rst') as f:
    changes = f.read()


if __name__ == '__main__':
    setup(
        name='picklepipe',
        description='Python pickling and marshal protocol over any network interface.',
        long_description='\n\n'.join([readme, changes]),
        license='MIT',
        url='http://picklepipe.readthedocs.io',
        version=VERSION,
        author='Seth Michael Larson',
        author_email='sethmichaellarson@protonmail.com',
        maintainer='Seth Michael Larson',
        maintainer_email='sethmichaellarson@protonmail.com',
        install_requires=['monotonic',
                          'selectors2'],
        keywords=['picklepipe'],
        packages=['picklepipe'],
        zip_safe=False,
        classifiers=['Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Natural Language :: English',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.3',
                     'Programming Language :: Python :: 3.4',
                     'Programming Language :: Python :: 3.5',
                     'Programming Language :: Python :: 3.6']
    )
