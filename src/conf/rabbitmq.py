# coding=utf-8
#
# $Id: $
#
# NAME:         rabbitmq.py
#
# AUTHOR:       Nick Whalen <nickw@mindstorm-networks.net>
# COPYRIGHT:    2012 by Nick Whalen
# LICENSE:
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# DESCRIPTION:
#   Example RabbitMQ config for the RPC client/server
#

HOST = 'rabbitmq-01'
PORT = 5672
VHOST = '/'
USERNAME = 'guest'
PASSWORD = 'guest'
DEFAULT_EXCHANGE = ''