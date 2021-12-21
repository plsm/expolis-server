#!/usr/bin/env python3
import getpass
import os.path
import shutil
import stat
import subprocess
import tempfile
from typing import List

import yaml

DATABASE = 'sensor_data'
ROLE_ADMIN = 'expolis_admin'
ROLE_APP = 'expolis_app'
ROLE_PHP = 'expolis_php'


def create_expolis_user ():
    run_command ([
        '/sbin/adduser',
        '--no-create-home',
        '--disabled-login',
        '--disabled-password',
        'expolis',
        'expolis'
    ])


def setup_tree_folder_structure ():
    print ('Creating tree folder structure...')
    folders = [
        '/opt/expolis/bin',
        '/opt/expolis/etc',
        '/opt/expolis/etc/osrm',
        '/opt/expolis/etc/osrm/lib',
        '/var/lib/expolis',
        '/var/lib/expolis/osrm',
        '/var/log/expolis',
    ]
    for a_folder in folders:
        print (a_folder)
        os.makedirs (a_folder, mode=0o744, exist_ok=True)
    print ('Done!')


def copy_model_files ():
    print ('Copying model files...')
    files = [
        'data.py',
        'interpolation_method.py',
        'period.py',
        'resolution.py',
        'aggregation.py',
    ]
    for a_file in files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/model/' + a_file
            ),
            '/opt/expolis/bin'
        )


def copy_utility_files ():
    print ('Copying utility files...')
    files = [
        'log.py',
        'database.py',
    ]
    for a_file in files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/util/' + a_file
            ),
            '/opt/expolis/bin'
        )


def copy_cron_files ():
    print ('Copying cron files...')
    files = [
        # main scripts
        'jobs_daily.py',
        'jobs_hourly.py',
        'jobs_weekly.py',
        # job scripts
        'aggregate_data_daily.py',
        'aggregate_data_hourly.py',
        'download_routing_data.py',
        'interpolate_data_daily.py',
        'manage_old_subscription_outputs.py',
        'manage_subscriptions_daily.py',
        'manage_subscriptions_hourly.py',
        'update_routing_data.py',
        # support modules
        'command.py',
        'interpolation_period.py',
    ]
    for a_file in files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/cron/' + a_file
            ),
            '/opt/expolis/bin'
        )


def setup_cron_scripts ():
    print ('Setup cron...')
    schedules = [
        'daily',
        'hourly',
        'weekly',
    ]
    for a_schedule in schedules:
        python_file = '/opt/expolis/bin/jobs_{s}.py'.format (s=a_schedule)
        script_file = '/etc/cron.{s}/expolis_{s}'.format (s=a_schedule)
        os.chmod (
            python_file,
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IROTH)
        os.symlink (
            python_file,
            script_file
        )


def copy_init_files ():
    print ('Copying python init files...')
    files = [
        # main scripts
        'mqtt_interface.py',
        'osrm_server.py',
        # support modules
        'daemon.py',
        'missing_data.py',
    ]
    for a_file in files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/init/' + a_file
            ),
            '/opt/expolis/bin'
        )
    files = [
        # init scripts
        'expolis_mqtt_interface.sh',
        'expolis_osrm_server.sh',
    ]
    for a_file in files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/init/' + a_file
            ),
            '/etc/init.d/' + a_file
        )


def setup_init_scripts ():
    print ('Setup init scripts...')
    services = [
        'expolis_osrm_server.sh',
        'expolis_mqtt_interface.sh',
    ]
    for a_service in services:
        os.chmod (
            '/etc/init.d/{s}'.format (s=a_service),
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IROTH)
        run_command (
            '/sbin/update-rc.d {s} defaults'.format (s=a_service).split (' ')
        )


def install_osrm ():
    print ('Installing OSRM...')
    print ('...installing dependencies')
    save_dir = os.getcwd ()
    # noinspection SpellCheckingInspection
    run_command ('/usr/bin/apt install build-essential git cmake pkg-config libbz2-dev libxml2-dev libzip-dev '
                 'libboost-all-dev lua5.2 liblua5.2-dev libtbb-dev'.split (' '))
    run_command ('/usr/bin/apt install curl'.split (' '))
    os.chdir ('/tmp')
    run_command ('/usr/bin/git clone https://github.com/Project-OSRM/osrm-backend'.split (' '))
    print ('...building OSRM')
    os.chdir ('/tmp/osrm-backend')
    os.makedirs (
        'build',
        mode=0o760,
        exist_ok=True,)
    os.chdir ('/tmp/osrm-backend/build')
    run_command (['/usr/bin/cmake', '..'])
    run_command (['/usr/bin/cmake', '--build', '.'])
    run_command (['/usr/bin/cmake', '--build', '.', '--target', 'install'])
    os.chdir (save_dir)


def init_osrm_config ():
    config = {
        'map_url': 'https://download.bbbike.org/osm/bbbike/Lisbon/Lisbon.osm.pbf',
        'map_path': '/var/lib/expolis/osrm/Lisbon.osm.pbf',
        'mutex': '/expolis-osrm',
        'routing': [
            {
                'profile': '/opt/expolis/etc/osrm/normal-bicycle.lua',
                'folder': '/var/lib/expolis/osrm/profile-normal-bicycle',
                'port': 30001,
                'depends_pollution': False,
            },
            {
                'profile': '/opt/expolis/etc/osrm/normal-car.lua',
                'folder': '/var/lib/expolis/osrm/profile-normal-car',
                'port': 30002,
                'depends_pollution': False,
            },
            {
                'profile': '/opt/expolis/etc/osrm/normal-foot.lua',
                'folder': '/var/lib/expolis/osrm/profile-normal-foot',
                'port': 30003,
                'depends_pollution': False,
            },
            {
                'profile': '/opt/expolis/etc/osrm/pollution-bicycle.lua',
                'folder': '/var/lib/expolis/osrm/profile-pollution-bicycle',
                'port': 30011,
                'depends_pollution': True,
            },
            {
                'profile': '/opt/expolis/etc/osrm/pollution-car.lua',
                'folder': '/var/lib/expolis/osrm/profile-pollution-car',
                'port': 30012,
                'depends_pollution': True,
            },
            {
                'profile': '/opt/expolis/etc/osrm/normal-foot.lua',
                'folder': '/var/lib/expolis/osrm/profile-pollution-foot',
                'port': 30013,
                'depends_pollution': True,
            },
        ]
    }
    with open ('/opt/expolis/etc/config-osrm', 'w') as fd:
        yaml.safe_dump (config, fd)
    run_command ([
        '/usr/bin/curl',
        config ['map_url'],
        '--silent',
        '--show-error',
        '--output', config ['map_path']
    ])
    for a_routing in config ['routing']:
        os.makedirs (
            name=a_routing ['folder'],
            mode=0o760,
            exist_ok=True,
        )
        head, tail = os.path.split (a_routing ['profile'])
        shutil.copy (
            os.path.join (
                source_folder,
                'src/lua-profiles/' + tail
            ),
            head,
        )
        os.symlink (
            src=config ['map_path'],
            dst=os.path.join (
                a_routing ['folder'],
                os.path.basename (config ['map_path']))
        )
    print ('Copying LUA library...')
    lua_profiles_lib = os.path.join (source_folder, 'src/lua-profiles/lib')
    for file in os.listdir (lua_profiles_lib):
        print (file)
        shutil.copy (
            os.path.join (lua_profiles_lib, file),
            '/opt/expolis/etc/osrm/lib'
        )


def create_raster_image_for_osrm ():
    with open ('/var/lib/expolis/osrm/pollution.raster', 'w') as fd_pollution:
        for x in range (551):
            for y in range (651):
                fd_pollution.write ('0 ')
            fd_pollution.write ('\n')


def download_osrm_data ():
    with open ('/opt/expolis/etc/config-osrm', 'r') as fd_config_osrm:
        config = yaml.safe_load (fd_config_osrm)
    print ('Downloading OSM data...')
    run_command ([
        '/usr/bin/curl',
        config ['map_url'],
        '--silent',
        '--show-error',
        '--output', config ['map_path']
    ])
    for a_routing in config ['routing']:
        if a_routing ['depends_pollution']:
            continue
        # path to the symbolic link in the folder where this profile files are stored
        map_path = os.path.join (a_routing ['folder'], os.path.basename (config ['map_path']))
        print ('Processing LUA profile {} in folder {}'.format (
            a_routing ['profile'],
            a_routing ['folder'],
        ))
        run_command ([
            '/usr/local/bin/osrm-extract',
            map_path,
            '--profile', a_routing ['profile'],
        ])
        run_command ([
            '/usr/local/bin/osrm-partition',
            map_path,
        ])
        run_command([
            '/usr/local/bin/osrm-customize',
            map_path,
        ])
        run_command([
            '/usr/local/bin/osrm-contract',
            map_path,
        ])


def setup_mail_configuration ():
    password = getpass.getpass ('Password for google account? ')
    with open ('/opt/expolis/etc/account-mail', 'w') as fd:
        fd.write (password)


def copy_website_files ():
    print ('Copying website files...')
    conf_files = [
        'apache2.conf',
        'ports.conf',
        'sites-enabled_000-default.conf',
    ]
    for a_file in conf_files:
        shutil.copy (
            os.path.join (source_folder, 'src/website/conf/' + a_file),
            '/etc/apache2')
        print ('  {} => /etc/apache2'.format (a_file))
    html_files = [
        'expolis.css',
        'index.en.html',
        'index.pt.html',
        'unsubscribe.en.php',
        'unsubscribe.pt.php',
    ]
    for a_file in html_files:
        shutil.copy (os.path.join (source_folder, 'src/website/html/' + a_file), '/var/www/html')
        print ('  {} => /var/www/html'.format (a_file))


def copy_bin_files ():
    bin_files = [
        'default_sensor_data.py',
        'new_sensor_data.py',
        'update_website.py',
        'control_panel.py',
    ]
    for a_file in bin_files:
        shutil.copy (
            os.path.join (
                source_folder,
                'src/expolis/bin/' + a_file
            ),
            '/opt/expolis/bin',
        )
        python_file = '/opt/expolis/bin/' + a_file
        os.chmod (
            python_file,
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IROTH,
        )
        os.symlink (
            python_file,
            '/usr/bin/expolis_' + a_file,
        )


def create_database ():
    print ('Creating database...')
    # noinspection SpellCheckingInspection
    commands = [
        '/usr/bin/sudo -u postgres createuser {} --pwprompt'.format (ROLE_ADMIN),
        '/usr/bin/sudo -u postgres createuser {}'.format (ROLE_APP),
        '/usr/bin/sudo -u postgres createuser {}'.format (ROLE_PHP),
        '/usr/bin/sudo -u postgres createdb -O {} {}'.format (ROLE_ADMIN, DATABASE),
    ]
    for a_command in commands:
        run_command (
            command_line=a_command.split (' ')
        )
    run_command (
        [
            '/usr/bin/sudo',
            '-u', 'postgres',
            'psql',
            '-U', 'postgres',
            '-d', DATABASE
        ],
        pipe_input='CREATE EXTENSION postgis;\n'
    )
    fd_pg_hba_conf = tempfile.NamedTemporaryFile (
        prefix='pg_hba_',
        suffix='.conf',
        mode='w',
        delete=False
    )
    fd_pg_hba_conf.write ('''
# Database administrative login by Unix domain socket
local  all         postgres                 peer
# ExpoLIS login
local  {database}  {role_admin}             md5
local  {database}  {role_app}               trust
local  {database}  {role_php}               trust
host   {database}  {role_app}    0.0.0.0/0  trust
host   {database}  {role_app}    ::0/0      trust
'''.format (
        database=DATABASE,
        role_admin=ROLE_ADMIN,
        role_app=ROLE_APP,
        role_php=ROLE_PHP,
    ))
    fd_pg_hba_conf.close ()
    # noinspection SpellCheckingInspection
    commands = [
        'sudo cp {} /etc/postgresql/13/main/pg_hba.conf'.format (fd_pg_hba_conf.name),
        'sudo chown postgres:postgres /etc/postgresql/13/main/pg_hba.conf',
        'sudo -u postgres pg_ctlcluster 13 main reload'
    ]
    for index, a_command in enumerate (commands):
        print ('Configure Authentication {}/{}'.format (index + 1, len (commands)),)
        run_command (
            a_command.split (' ')
        )
    print ('Setup database')
    run_command ([
        '/usr/bin/sudo',
        '-u', 'postgres',
        'psql',
        '-U', ROLE_ADMIN,
        '-d', DATABASE,
        '--file', os.path.join (source_folder, 'src/database/setup_database.sql')
    ])
    with open ('/opt/expolis/etc/config-database', 'w') as fd:
        fd.write ('{}\n{}\n{}\n'.format (
            DATABASE,
            ROLE_ADMIN,
            getpass.getpass ('Password of ExpoLIS database administrator? ')
        ))
    print ('Created database')


def initialise_sensor_data ():
    with open ('/opt/expolis/etc/sensor_data', 'w') as fd:
        sensor_data = [
        ]
        yaml.safe_dump (sensor_data, fd)


def install_interpolator_binaries ():
    # noinspection SpellCheckingInspection
    run_command (
        command_line=[
            '/usr/bin/g++',
            '-I' + os.path.join (source_folder, 'interpolator/common'),
            '-I' + os.path.join (source_folder, 'interpolator/nr'),
            '-Wall',
            os.path.join (source_folder, 'interpolator/kriging/main_kriging.cpp'),
            os.path.join (source_folder, 'interpolator/common/data.cpp'),
            os.path.join (source_folder, 'interpolator/common/log.cpp'),
            os.path.join (source_folder, 'interpolator/common/options.cpp'),
            '-o', '/opt/expolis/bin/interpolator-kriging',
            '-lm',
            '-lboost_program_options'
        ],
    )


def run_command (command_line: List [str], pipe_input: str = None, ) -> None:
    """
    Run the command with the given command line arguments
    :param command_line: the command line arguments
    :param pipe_input: If not None, a pipe is created to the process, and this parameter is written to its
     standard input
    """
    if pipe_input is None:
        process = subprocess.Popen (command_line)
    else:
        process = subprocess.Popen (
            command_line,
            stdin=subprocess.PIPE,
            universal_newlines=True
        )
        process.communicate (pipe_input)
    process.wait ()


if __name__ == '__main__':
    source_folder = os.path.dirname (os.path.abspath (__file__))
    create_expolis_user ()
    setup_tree_folder_structure ()
    copy_model_files ()
    copy_utility_files ()
    copy_cron_files ()
    setup_cron_scripts ()
    copy_init_files ()
    setup_init_scripts ()
    create_database ()
    initialise_sensor_data ()
    install_osrm ()
    init_osrm_config ()
    create_raster_image_for_osrm ()
    download_osrm_data ()
    setup_mail_configuration ()
    copy_website_files ()
    copy_bin_files ()
    install_interpolator_binaries ()
