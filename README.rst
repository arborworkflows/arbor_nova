==========
arbor_nova
==========

Arbor easy-mode apps for Girder 3.

Installation
------------

This is descriptive rather than prescriptive, but it is what has been tested.

* Do this work with Python3
* Have two virtualenvs, one for girder named `girder` and one for girder-worker named `gw`.
* Install mongo and rabbitmq

* In virtualenv `girder` run the following commands, it doesn't matter where you run them from:
  * `pip install --pre girder[plugins]`
  * `girder build`
* These commands need to be run in the `girder` virtualenv from specific locations.
  * from `arbor_nova/girder_plugin` run `pip install -e .`        # install girder plugin
  * from `arbor_nova/girder_worker_tasks` run `pip install -e .`  # install gw tasks for producer
* Run Girder, some variant of `girder serve`
* Enable the arbor_nova plugin in Girder
* TODO: should we have to enable the jobs or other dependent plugins? how to get those automatically?


* In virtualenv `gw` run the following commands, it doesn't matter where you run them from:
  * `pip install --pre girder-worker`
* This command needs to be run in the `gw` virtualenv from a specific locations
  * from `arbor_nova/girder_worker_tasks` run `pip install -e .`  # install gw tasks for consumer
* Start girder-worker by running `girder-worker` 


Features
--------

* TODO
