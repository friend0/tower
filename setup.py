try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='World Engine',
    version='0.0.1',
    packages=['tests', 'tests.map_tests', 'tests.quaternion_tests', 'tests.web_service_tests',
              'tests.matlab_engine_tests', 'tests.message_passing_tests', 'world_engine', 'world_engine.utils',
              'world_engine.world', 'world_engine.world.mapping', 'world_engine.world.vehicles', 'world_engine.engine',
              'world_engine.engine.server', 'world_engine.engine.server.vrep', 'world_engine.engine.server.playground',
              'world_engine.engine.server.server_conf', 'world_engine.engine.server.web_services',
              'world_engine.engine.server.matlab_engine', 'world_engine.engine.server.message_passing',
              'world_engine.engine.dynamics', 'world_engine.engine.dynamics.rigid_body',
              'world_engine.engine.dynamics.quaternions', 'world_engine.engine.feedback',
              'world_engine.engine.controllers', 'world_engine.engine.controllers.pid', '', 'utils', 'world',
              'world.mapping', 'world.vehicles', 'engine', 'engine.server', 'engine.server.vrep',
              'engine.server.playground', 'engine.server.server_conf', 'engine.server.web_services',
              'engine.server.matlab_engine', 'engine.server.message_passing', 'engine.dynamics',
              'engine.dynamics.rigid_body', 'engine.dynamics.quaternions', 'engine.feedback', 'engine.controllers',
              'engine.controllers.pid'],
    package_dir={'': 'world_engine'},
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
    url='',
    license='MIT',
    author='Ryan A. Rodriguez',
    author_email='ryarodri@ucsc.edu',
    description=''
)

