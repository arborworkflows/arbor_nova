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

* In virtualenv **girder** run the following commands, it doesn't matter where you run them from:

.. code-block:: bash

    $ pip install --pre girder[plugins]
    $ girder build

* These commands need to be run in the **girder** virtualenv from specific locations.

.. code-block:: bash

    $ cd arbor_nova/girder_worker_tasks    
    $ pip install -e .                     # install gw tasks for producer
    $ cd ../../arbor_nova/girder_plugin
    $ pip install -e .                     # install girder plugin
    $ girder serve                         # start serving girder
 

* In virtualenv **gw** run the following command, it doesn't matter where you run it from:

.. code-block:: bash

    $ pip install --pre girder-worker

* These commands need to be run in the **gw** virtualenv from a specific location

.. code-block:: bash

    $ cd arbor_nova/girder_worker_tasks    
    $ pip install -e .                     # install gw tasks for consumer
    $ girder-worker                        # start girder-worker


Features
--------

Installs a REST endpoint for launching a GW job. The endpoint will take in a csv file id,
and an output item id, then call the GW job. The GW job will download the csv file, append
a new column to each line, then upload the resulting file to the output item.


TODO
----

* Should we have to enable the jobs or other dependent plugins? how to get those enabled automatically?
* Need to cleanup the output file on the GW task side. Is there a way to do that automatically?
