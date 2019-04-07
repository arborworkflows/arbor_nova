
from setuptools import setup

setup(name='arbor_tasks_tasks',
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
              'arbor_tasks = arbor_tasks:ArborTasksPlugin',
          ]
      },
      install_requires=[
          'girder_worker'
      ],
      packages=['arbor_gw_tasks'],
      zip_safe=False)
