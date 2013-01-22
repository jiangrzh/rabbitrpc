# coding=utf-8
#
# $Id: $
#
# NAME:         test_rabbitrpcclient.py
#
# AUTHOR:       Nick Whalen <nickw@mindstorm-networks.net>
# COPYRIGHT:    2013 by Nick Whalen
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
#   Tests rabbitrpcclient
#

import pytest
import mock
from lib.rabbitrpc import rabbitrpcclient


class Test_Init(object):
    """
    Tests RabbitRPCClient's __init__ method.
    """

    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'
        self.timeout = 7000

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()

        self.rpc = self.localrpc.RabbitRPCClient(self.queue, reply_timeout=self.timeout)
    #---

    def test_CreatesLoggerInstance(self):
        """
        Tests that __init__ creates a logger instance.

        """
        called = self.localrpc.logging.getLogger.called
        assert called == True
    #---

    def test_SetsReplyTimeoutInSeconds(self):
        """
        Tests that __init__ sets the reply timeout, in seconds.

        """
        assert self.rpc._reply_timeout == (self.timeout/1000)
    #---

    def test_SetsQueueName(self):
        """
        Tests that __init__ sets the incoming rpc queue.

        """
        assert self.rpc.queue == self.queue
    #---

    def test_ReplyQueueDefaultsToNone(self):
        """
        Tests that __init__ sets reply_queue to None by default.

        """
        assert self.rpc.reply_queue is None
    #---

    def test_SetsReplyQueueIfProvided(self):
        """
        Tests that __init__ sets reply_queue to the provided value, if available.

        """
        queue = 'Test123'
        rpc = self.localrpc.RabbitRPCClient(self.queue, reply_queue=queue, reply_timeout=self.timeout)
        assert rpc.reply_queue == queue
        #---

    def test_SetsExchangeToProvidedParamIfExists(self):
        """
        Tests that __init__ sets the exchange to what was passed in, if something was passed in.

        """
        exchange = 'BobXchange'
        rpc = rabbitrpcclient.RabbitRPCClient(self.queue, exchange=exchange)

        assert rpc.exchange == exchange
    #---

    def test_SetsExchangeToDefaultIfNonePassedIn(self):
        """
        Tests that __init__ sets the exchange to the default (in the config file) if an exchange was not passed in.

        """
        exchange = 'DefaultExchange'
        rabbitrpcclient.config.DEFAULT_EXCHANGE = mock.MagicMock(return_value=exchange)
        rpc = rabbitrpcclient.RabbitRPCClient(self.queue, exchange=exchange)

        assert rpc.exchange == exchange
    #---

    def test_CallsConnectionSetup(self):
        """
        Tests that __init__ calls the connection setup.

        """
        self.rpc._configureConnection.assert_called_once_with()
    #---

    def test_CallsConnect(self):
        """
        Tests that __init__ calls the connection method.

        """
        self.rpc._connect.assert_called_once_with()
    #---
#---

class Test_Send(object):
    """
    Tests RabbitRPCClient's send method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'
        self.rpc_data = {'bob':'barker'}
        self.pickled_rpc_data = "(dp1" \
                                    "S'bob'" \
                                    "p2" \
                                    "S'barker'" \
                                    "p3" \
                                    "s."
        self.uuid = 'thisisnotauuid'
        self.basic_props = {'prop':'value'}

        # Holy mocks Batman
        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()
        self.localrpc.RabbitRPCClient._startReplyConsumer = mock.MagicMock()
        self.localrpc.RabbitRPCClient._replyWaitLoop = mock.MagicMock()
        self.localrpc.cPickle.dumps = mock.MagicMock(return_value=self.pickled_rpc_data)
        self.localrpc.uuid.uuid4 = mock.MagicMock(return_value=self.uuid)
        self.localrpc.pika.BasicProperties = mock.MagicMock(return_value=self.basic_props)

        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
        self.rpc.channel = mock.MagicMock()
        self.rpc_reply = self.rpc.send(self.rpc_data)
    #---

    def test_PicklesRPCData(self):
        """
        Tests that send pickles the incoming RPC data.

        """
        self.localrpc.cPickle.dumps.assert_called_once_with(self.rpc_data)
    #---

    def test_StartsReplyConsumerIfExpectReplyIsTrue(self):
        """
        Tests that send starts the reply consumer if expect_reply is True

        """
        called = self.rpc._startReplyConsumer.called
        assert called == True
    #---

    def test_CreatesACorrelationIDIfExpectReplyIsTrue(self):
        """
        Tests that send creates a correlation id to use in the RabbitMQ transaction if expect_reply is `True`.

        """
        called = self.localrpc.uuid.uuid4.called
        assert called == True
    #---

    def test_SetsPublishPropsIfExpectReplyIsTrue(self):
        """
        Tests that send sets additional properties (reply_to, correlation_id) for basic_publish if expect_reply is
        `True`.

        """
        self.localrpc.pika.BasicProperties.assert_called_once_with(reply_to=self.rpc.reply_queue,
                                                                   correlation_id=self.uuid)
    #---

    def test_PublishesTheRPCData(self):
        """
        Tests that send publishes the RPC data with the correct settings.

        """
#        print self.rpc.channel.basic_publish.mock_calls
        self.rpc.channel.basic_publish.assert_called_once_with(exchange=self.rpc.exchange, routing_key=self.queue,
                                                               body=self.pickled_rpc_data, properties=self.basic_props)

    #---

    def test_WaitsForAReplyIfExpectReplyIsTrue(self):
        """
        Tests that send

        """
        called = self.rpc._replyWaitLoop.called
        assert called == True
    #---

    def test_ReturnsTheRPCResponseIfExpectReplyIsTrue(self):
        """
        Tests that send returns the RPC response if expect reply is true.

        """
        expected_reply = 'No'
        self.rpc._rpc_reply = expected_reply
        reply = self.rpc.send(self.rpc_data)

        assert expected_reply == reply
    #---
#---

class Test_startReplyConsumer(object):
    """
    Tests RabbitRPCClient's _startReplyConsumer method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()

        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
        self.rpc.channel = mock.MagicMock()
        self.rpc._startReplyConsumer()
        #---

    def test_InitializesQueueConsumerWithCorrectParams(self):
        """
        Tests that _startReplyConsumer initializes the consumer with the proper parameters

        """
        self.rpc.channel.basic_consume.assert_called_once_with(self.rpc._consumerCallback, queue=self.rpc.reply_queue,
                                                               no_ack=True)
    #---
#---

class Test_replyWaitLoop(object):
    """
    Tests RabbitRPCClient's _replyWaitLoop method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()

        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
        self.rpc.connection = mock.MagicMock()
        self.rpc._rpc_reply = 'Yes' # Kills the loop, or the test will never finish
        self.rpc._replyWaitLoop()
    #---

    def test_AddsReplyTimeout(self):
        """
        Tests that _replyWaitLoop adds a timeout to stop the loop after a set amount of time.

        """
        self.rpc.connection.add_timeout.assert_called_once_with(self.rpc._reply_timeout, self.rpc._timeoutElapsed)
    #---

    def test_ProcessesDataEvents(self):
        """
        Tests that _replyWaitLoop processes events for the consumer.

        """
        # This kills off the while loop so the test does not hang, I really don't like this.
        def loop_killer():
            self.rpc._rpc_reply = 'Yes'

        self.rpc._rpc_reply = None
        self.rpc.connection.process_data_events = mock.MagicMock(side_effect=loop_killer)

        self.rpc._replyWaitLoop()
        called = self.rpc.connection.process_data_events.called

        assert called == True
    #---
#---

class Test_consumerCallback(object):
    """
    Tests RabbitRPCClient's _consumerCallback method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'
        self.body = 'iamsopickled'
        self.correlation_id = 'something'
        self.rpc_data = ('i','am','so','pickled')

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()
        self.localrpc.cPickle.loads = mock.MagicMock(return_value=self.rpc_data)
        self.props = mock.MagicMock()


        self.reply_to = 'bob.bob'
        type(self.props).correlation_id = mock.PropertyMock(return_value = self.correlation_id)

        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
        self.rpc.correlation_id = self.correlation_id
        self.rpc._consumerCallback('', '', self.props, self.body)
    #---

    def test_SetsRPCReplyOnMatchedCorrelationID(self):
        """
        Tests that _consumerCallback sets _rpc_reply when it matches the correlation id.

        """
        assert self.rpc._rpc_reply == self.rpc_data
    #---

    def test_DoesNotSetRPCReplyOnNonMatchedCorrelationID(self):
        """
        Tests that _consumerCallback does not set _rpc_reply the correlation ids do not match.

        """
        self.rpc._rpc_reply = None
        self.rpc.correlation_id = 'bob'

        self.rpc._consumerCallback('', '', self.props, self.body)
        assert self.rpc._rpc_reply != self.rpc_data
    #---

    def _UnPicklesRPCResults(self):
        """
        Tests that _consumerCallback un-pickles the RPC results.

        """
        self.rpc._consumerCallback('', '', self.props, self.body)
        self.localrpc.cPickle.loads.assert_called_once_with(self.body)
    #---
    def test_UnPicklesRPCResults(self): self._reload_cPickle(self._UnPicklesRPCResults)

    def _reload_cPickle(self, test_method):
        """
        Wraps a test method that uses cPickle mocking so it doesn't screw up other tests.
        """
        cpickle = reload(rabbitrpcclient.cPickle)
        self.localrpc.cPickle = cpickle
        self.localrpc.cPickle.loads = mock.MagicMock(return_value=self.rpc_data)

        try:
            test_method()
        except Exception:
            raise
        finally:
            self.localrpc.cPickle = reload(rabbitrpcclient.cPickle)
    #---
#---

class Test_Connect(object):
    """
    Tests the _connect method.

    """
    def setup_method(self, method):
        """
        Setup tests

        :param method:

        """
        self.connection_params = {'none':None}
        self.queue = 'daQueue'

        self.localrpc = reload(rabbitrpcclient)
        self.callback = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()

        self.channel = mock.MagicMock()
        self.connection = mock.MagicMock()
        self.connection.channel.return_value=self.channel
        self.localrpc.pika.BlockingConnection = mock.MagicMock(return_value=self.connection)
        self.BlockingConnection = self.localrpc.pika.BlockingConnection

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient.connection_params = self.connection_params

        # _connect is called by the constructor
        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
    #---

    def test_UsesBlockingConnection(self):
        """
        Tests that _connect calls pika.BlockingConnection.

        """
        self.BlockingConnection.assert_called_once_with(self.connection_params)
    #---

    def test_RaisesConnectionErrorIfConnectionProblem(self):
        """
        Tests that _connect raises ConnectionError if there is a problem connecting to RabbitMQ.

        """
        self.BlockingConnection.side_effect = rabbitrpcclient.AMQPConnectionError

        with pytest.raises(rabbitrpcclient.ConnectionError):
            self.rpc._connect()
    #---

    def test_CreatesChannelOnConnection(self):
        """
        Tests that _connect creates a new channel on the connection.

        """
        self.connection.channel.assert_called_once_with()
    #---

    def test_DeclaresQueueExclusive(self):
        """
        Tests that _connect declares a durable queue.

        """
        self.channel.queue_declare.assert_called_once_with(exclusive=True)
    #---

    def test_AllowsOverrideOfQueueName(self):
        """
        Tests that _connect allows the queue name to be overridden with the value passed into the class' constructor.

        """
        self.channel.queue_declare.reset_mock()
        queue = 'someQueue'
        self.rpc.reply_queue = queue
        self.rpc._connect()
        self.channel.queue_declare.assert_called_once_with(exclusive=True, **{'queue': queue})
    #---
#---

class Test_connect(object):
    """
    Tests RabbitRPCClient's _connect method.

    """
    def setup_method(self, method):
        """
        Test Setup

        :param method:

        """
        self.localrpc = reload(rabbitrpcclient)
        self.queue = 'testRPC'

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._configureConnection = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()

        self.rpc = self.localrpc.RabbitRPCClient(self.queue)
    #---

    def test_(self):
        """


        """
    #---
#---

class Test_ConfigureConnection(object):
    """
    Tests the _configureConnection method.
    """
    def setup_method(self, method):
        """
        Setup Tests

        :param method:

        """
        self.host = 'hostname'
        self.port = 1234
        self.vhost = 'b/b'
        self.creds = {'bob':'barker'}
        self.username = 'bob'
        self.password = 'barker'

        self.connection_settings = {
            'host': self.host,
            'port': self.port,
            'virtual_host': self.vhost,
            'credentials': self.creds
        }

        self.localrpc = reload(rabbitrpcclient)
        self.localrpc.pika.PlainCredentials = mock.MagicMock(return_value=self.creds)
        self.PlainCredentials = self.localrpc.pika.PlainCredentials
        self.localrpc.pika.ConnectionParameters = mock.MagicMock(return_value=self.connection_settings)
        self.ConnectionParameters = self.localrpc.pika.ConnectionParameters

        self.localrpc.config.HOST = self.host
        self.localrpc.config.PORT = self.port
        self.localrpc.config.VHOST = self.vhost
        self.localrpc.config.USERNAME = self.username
        self.localrpc.config.PASSWORD = self.password

        self.localrpc.logging = mock.MagicMock()
        self.localrpc.RabbitRPCClient._connect = mock.MagicMock()

        # _configureConnection is called in the constructor
        self.rpc = self.localrpc.RabbitRPCClient('')
    #---

    def test_CreatesPlainCredentialsObject(self):
        """
        Tests that _connect sets a prefetch_count of 1 for basic_qos.

        """
        self.PlainCredentials.assert_called_once_with(self.username, self.password)
    #---

    def test_UsesProperValuesFromConfigFile(self):
        """
        Tests that _connect sets a prefetch_count of 1 for basic_qos.

        """
        self.ConnectionParameters.assert_called_once_with(**self.connection_settings)
    #---

    def test_SetsConnectionParameters(self):
        """
        Tests that _connect sets the class' connection parameters.

        """
        assert self.rpc.connection_params == self.connection_settings
    #---
#---
