#!/usr/bin/env python3

import os.path
import posix_ipc
from typing import TextIO
import yaml

import command
import log


def main (fd_log: TextIO):
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd_config_osrm:
        config = yaml.safe_load (fd_config_osrm)
    mutex = posix_ipc.Semaphore (
        name=config ['mutex'],
    )
    mutex.acquire ()
    command.run_command (
        command_line=[
            '/usr/bin/curl',
            config ['map_url'],
            '--silent',
            '--show-error',
            '--output', config ['map_path']
        ],
        fd_log=fd_log,
    )
    mutex.release ()
    for a_routing in config ['routing']:
        if a_routing ['depends_pollution']:
            continue
        # path to the symbolic link in the folder where this profile files are stored
        map_path = os.path.join (a_routing ['folder'], os.path.basename (config ['map_path']))
        log.log (fd_log, 'Processing LUA profile {} in folder {}'.format (
            a_routing ['profile'],
            a_routing ['folder'],
        ))
        command.run_command (
            command_line=[
                '/usr/local/bin/osrm-extract',
                map_path,
                '--profile', a_routing ['profile']
            ],
            fd_log=fd_log,
        )
        command.run_command (
            command_line=[
                '/usr/local/bin/osrm-partition',
                map_path,
            ],
            fd_log=fd_log,
        )
        command.run_command(
            command_line=[
                '/usr/local/bin/osrm-customize',
                map_path,
            ],
            fd_log=fd_log
        )
        command.run_command(
            command_line=[
                '/usr/local/bin/osrm-contract',
                map_path,
            ],
            fd_log=fd_log
        )


with open ('/var/log/expolis/download-routing-data', 'a') as fd:
    log.log (fd, 'start')
    main (fd)
    log.log (fd, 'end')
