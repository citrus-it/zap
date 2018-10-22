#!/usr/bin/python3

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

# Copyright 2018 OmniOS Community Edition (OmniOSce) Association.

import os, sys, subprocess
from pprint import pprint
import xml.etree.ElementTree as etree

statemap = {
    'installed':    'stopped',
}

class Zone(object):
    rootattribs = [ 'zonepath', 'brand', 'autoboot', 'ip-type' ]
    def __init__(self, name, state=None):
        self.name = name
        self.state = state
        try:
            self.state = statemap[self.state]
        except KeyError:
            pass

        self.xml = os.path.join(os.sep, 'etc', 'zones', name + '.xml')
        self.clean = True

        try:
            self.cfg = etree.parse(self.xml)
            self.root = self.cfg.getroot()
            self._attribs()
            self._nics()
            self._attrs()
        except FileNotFoundError:
            # Initialise empty zone
            self.root = etree.Element('zone')
            self.root.set('ip-type', 'exclusive')
            self.root.set('brand', type(self).__name__[:-4])
            self.root.set('autoboot', 'false')
            self.cfg = etree.ElementTree(self.root)
            etree.dump(self.cfg)
            self.clean = False

    def _attribs(self):
        for a in self.rootattribs:
            setattr(self, a, self.root.get(a))

    def _nics(self):
        self.nics = []
        if getattr(self, 'ip-type') != 'exclusive':
            return

        for n in self.root.findall('./network[@physical]'):
            self.nics.append({
                'name':     n.get('physical'),
                'address':  n.get('allowed-address'),
                'gw':       n.get('defrouter'),
            })

    def _attrs(self):
        self.attrs = []

        for a in self.root.findall('./attr[@name]'):
            self.attrs.append({
                'name':     a.get('name'),
                'value':    a.get('value'),
            })

    def touch(self):
        self.clean = False

    def set_attrib(self, a, v):
        """Set an attribute on the root node, returning the old value"""
        if a not in self.rootattribs:
            return None
        ret = self.root.get(a)
        self.root.set(a, v)
        self.touch()
        return ret

    def xmlstring(self):
        return etree.tostring(self.root)

    def validate(self):
        for a in self.rootattribs:
            if not self.root.get(a):
                print("Zone validation failed,", a, "is missing")
                return False

    def save(self):
        if not self.validate():
            return False
        if self.clean:
            return True
        with open(self.xml + ".new", 'wb') as f:
            f.write(b'<?xml version="1.0"?>\n')
            f.write(b'<!DOCTYPE zone PUBLIC "-//Sun Microsystems Inc//DTD Zones//EN" "file:///usr/share/lib/xml/dtd/zonecfg.dtd.1">\n')
            f.write(self.xmlstring())
            f.write(b'\n')
        os.rename(self.xml + ".new", self.xml)
        os.chmod(self.xml, 0o644)
        return True

    def poweroff(self):
        raise Exception('No poweroff method for this zone brand')

    def reset(self):
        raise Exception('No reset method for this zone brand')

    def nmi(self):
        raise Exception('No nmi method for this zone brand')

class ipkgZone(Zone):
    pass

class lipkgZone(ipkgZone):
    pass

class sparseZone(lipkgZone):
    pass

class vmZone(Zone):
    pass

class bhyveZone(vmZone):
    def exists(self):
        return os.access('/dev/vmm/{}'.format(self.name), os.W_OK)

    def ctl(self, cmd):
        if not self.exists():
            print("{} is not running.".format(self.name))
            return 0
        subprocess.run(['/usr/sbin/bhyvectl', '--vm={}'.format(self.name), cmd])
        return 1

    def poweroff(self):
        self.ctl('--force-poweroff')

    def reset(self):
        self.ctl('--force-reboot')

    def nmi(self):
        self.ctl('--inject-nmi')

class kvmZone(vmZone):
    pass

def load(name, state=None):
    try:
        cfg = etree.parse(os.path.join(os.sep, 'etc', 'zones', name + '.xml'))
        root = cfg.getroot()
    except FileNotFoundError:
        return None

    brand = root.get('brand')
    try:
        constructor = globals()[brand + "Zone"]
        return constructor(name, state)
    except KeyError:
        raise KeyError('Unknown brand')

def create(name, brand):
    if load(name):
        raise FileExistsError('Zone already exists')
    try:
        constructor = globals()[brand + "Zone"]
        return constructor(name)
    except KeyError:
           raise KeyError('Unknown brand')

def list():
    ret = subprocess.run(['/usr/sbin/zoneadm', 'list', '-pc'],
        stdout=subprocess.PIPE)
    zones = []
    for line in ret.stdout.splitlines():
        _, name, state, _, _, brand, _ = str(line).split(":", 6)
        if name == "global":
            continue
        try:
            zones.append(load(name, state))
        except KeyError:
            #print("WARNING: Unhandled zone brand", brand)
            pass

    return zones


# Vim hints
# vim:ts=4:sw=4:et:fdm=marker
