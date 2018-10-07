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

import os, sys, getopt
from pprint import pprint

import zadm.zone as zone

debug = False

def usage(str = None):
    if str:
        print(str)

    print('''
Syntax: zadm [-z <zone>] command [options]
    list
    show

''')
    sys.exit(0)

def list_zones(z, args):
    zones = zone.list()
    if not zones:
        return
    zones.sort(key = lambda x: x.name)
    width = max(len(z.name) for z in zones) + 1

    format = "{:<" + str(width) + "} {:<6} {:<11}"
    print(format.format('NAME', 'TYPE', 'STATUS'))
    for z in zones:
        print(format.format(z.name, z.brand, z.state))

def show_zone(name, args):
    if name is None:
        usage('No zone specified.')

    z = zone.load(name)

    f = "{:<20} {}"
    fr = "{:>20} {}"
    if not args or "name" in args:
        print(f.format('name', z.name))
    if not args or "brand" in args:
        print(f.format('Brand (type)', z.brand))
    if not args or "path" in args:
        print(f.format('Path', z.zonepath))
    if not args or "autoboot" in args:
        print(f.format('Auto-boot', z.autoboot))
    for n in z.nics:
        if not args or "nic" in args or "nic." + n['name'] in args:
            print(f.format('Network interface', n['name']))
            if n['address']:
                print(fr.format('..address', n['address']))
            if n['gw']:
                print(fr.format('..gateway', n['gw']))
    for a in z.attrs:
        if not args or "attr" in args or "attr." + a['name'] in args:
            print(f.format(a['name'], a['value']))

def create_zone(name, args):
    z = zone.create(name, 'sparse')
    #print(z.xmlstring())
    z.save()

def dump_zone(name, args):
    """ Debug function to dump parsed zone configuration """
    if name is None:
        usage('No zone specified.')

    z = zone.load(name)
    pprint(vars(z))

def rewrite_zone(name, args):
    """ Internal debug function to load and save a zone """
    if name is None:
        usage('No zone specified.')

    z = zone.load(name)
    z.save()

cmds = {
    "list":         [list_zones],
    "show":         [show_zone],
    "create":       [create_zone],
    "dump":         [dump_zone],
    "_rewrite":     [rewrite_zone],
}

if __name__ == "__main__":
    import warnings
    warnings.simplefilter('error')

    tzone = None

    # Global options handling

    try:
        opts, pargs = getopt.getopt(sys.argv[1:], "z:d",
            ["debug=", "zone="])
    except getopt.GetoptError as e:
        usage("illegal global option -- {0}".format(e.opt))

    for opt, arg in opts:
        if opt == "-d" or opt == "--debug":
            debug = True
        elif opt == "-z" or opt == "--zone":
            tzone = arg

    cmd = 'list'
    if pargs:
        cmd = pargs.pop(0)

    if cmd not in cmds: usage()

    func = cmds[cmd][0]
    func(tzone, pargs)

# Vim hints
# vim:ts=4:sw=4:et:fdm=marker
