
from setuptools import setup

setup(name='arbor_nova_tasks',
      version='0.0.0',
      description='A girder_worker extension with arbor task examples',
      author='Kitware Inc.',
      author_email='kitware@kitware.com',
      license='Apache v2',
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: Apache Software License'
          'Natural Language :: English',
          'Programming Language :: Python'
      ],
      entry_points={
          'girder_worker_plugins': [
              'arbor_nova_tasks = arbor_nova_tasks:ArborNovaTasksGirderWorkerPlugin',
          ]
      },
      install_requires=[
          'girder_worker'
      ],
      packages=['arbor_nova_tasks'],
      zip_safe=False)
