# ExpoLIS Server

This repository contains the sensor database, the html server, and the open service routing machine.  The source code in this repository is from the repositories expolis-database and expolis-routing-service.  The development and testining history is available in these two repositories.

# Requirements

    sudo apt install python3 python3-pip
    sudo apt install postgresql-13 postgis
    sudo apt install apache2
    pip3 install python-daemon
    pip3 install posix-ipc
    pip3 install yaml
    pip3 install psutil
    pip3 install psycopg2-binary
    pip3 install paho-mqtt

Alternative to using `pip3 install`

    sudo apt install python3-daemon python3-yaml python3-posix-ipc python3-psutil python3-psycopg2


# Data Model

![Overview of the data model](doc/entity-relation-database.png)

* table `interpolation_M_D_P` uses data stored in table `aggregation_avg_D_P_R`, with  is used by the mobile app to show

# Structure

Postgresql tables and functions used by the different cron and init scripts:

| dir  | script                 | table                      | function                                   |
|------|------------------------|----------------------------|--------------------------------------------|
| cron | aggregate_data_daily   |                            | aggregate_Statistic_Period_Resolution_Data |
| cron | aggregate_data_hourly  |                            | aggregate_Statistic_Period_Resolution_Data |
| cron | download_routing_data  |                            |                                            |
| cron | interpolate_data_daily | aggregation, interpolation |                                            |
| cron | update_routing_data    | interpolation              |                                            |
| init | mqtt_interface         | node_sensors               | insert_measurements                        |
| init | osrm_server            |                            |                                            |

Cron scripts

| period | script                          |
|--------|---------------------------------|
| hourly | aggregate_data_hourly           |
|        | manage_old_subscription_outputs |
|        | manage_subscriptions_hourly     |
| daily  | aggregate_data_daily            |
|        | manage_subscriptions_daily      |
|        | interpolate_data_daily          |
|        | update_routing_data             |
| weekly | download_routing_data           |
