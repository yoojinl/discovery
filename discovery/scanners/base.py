# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseScanner(object):

    cli_opts = []

    def __init__(self, config):
        self.config = config

    @abc.abstractproperty
    def name(self):
        """Uniq scanner name."""

    @abc.abstractproperty
    def version(self):
        """Version of scanner."""

    @abc.abstractmethod
    def run():
        """Define logic, how scanner should be started."""
