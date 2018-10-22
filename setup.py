# {{{ CDDL HEADER
#
# This file and its contents are supplied under the terms of the
# Common Development and Distribution License ("CDDL"), version 1.0.
# You may only use this file in accordance with the terms of version
# 1.0 of the CDDL.
#
# A full copy of the text of the CDDL should have accompanied this
# source. A copy of the CDDL is also available via the Internet at
# http://www.illumos.org/license/CDDL.
# }}}

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENCE') as f:
    licence = f.read()

setup(
    name='zap',
    version='0.1.0',
    description='OmniOS zone management',
    long_description=readme,
    author='OmniOS Community Edition (OmniOSce) Association',
    author_email='sa@omniosce.org',
    url='https://github.com/citrus-it/zap',
    license=licence,
    packages=find_packages(exclude=('tests', 'docs'))
)

