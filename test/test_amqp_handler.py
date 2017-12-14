#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2014 Wieland Hoffmann
# License: MIT, see LICENSE for details
import mock
import unittest

from amqp import Message as Amqp_Message
from logging import basicConfig, CRITICAL
from sir.amqp import handler
from sir.amqp.message import Message
from sir.schema import SCHEMA


# Some tests test exception handle which usually generates annoying "no handler
# configured for logger ..." messages
basicConfig(level=CRITICAL)


class AmqpTestCase(unittest.TestCase):

    def setUp(self):
        self.entity_type = "artist"
        self.id_string = "42"
        self.routing_key = "rk"
        self.message = Amqp_Message(
            body='{"_table": "%s", "id": "%s"}' % (self.entity_type, self.id_string),
            channel=mock.Mock(),
            application_headers={},
        )

        self.message.delivery_info = {"routing_key": self.routing_key}

        self.delivery_tag = object()
        self.message.delivery_tag = self.delivery_tag

        db_session_patcher = mock.patch("sir.amqp.handler.db_session")
        self.addCleanup(db_session_patcher.stop)
        db_session_patcher.start()


class CallbackWrapperTest(AmqpTestCase):

    def test_ack(self):
        def wrapped_f(*args, **kwargs):
            pass

        f = handler.callback_wrapper(wrapped_f)
        f(mock.Mock(), self.message, "search.index")
        self.message.channel.basic_ack.assert_called_once_with(self.delivery_tag)

    def test_reject_on_exception(self):
        def wrapped_f(*args, **kwargs):
            raise ValueError()

        f = handler.callback_wrapper(wrapped_f)
        f(mock.Mock(), self.message, "search.index")
        self.message.channel.basic_reject.assert_called_once_with(
            self.delivery_tag,
            requeue=False)
        self.message.channel.basic_publish.assert_called_once_with(
            self.message,
            exchange="search.retry",
            routing_key=self.routing_key)
        self.assertEqual(
            self.message.application_headers["mb-retries"],
            handler._DEFAULT_MB_RETRIES - 1)
        self.assertFalse(self.message.channel.basic_ack.called)

    def test_search_failed_on_mb_retries_zero(self):
        def wrapped_f(*args, **kwargs):
            raise ValueError()

        self.message.application_headers["mb-retries"] = 0
        f = handler.callback_wrapper(wrapped_f)
        f(mock.Mock(), self.message, "search.index")
        self.message.channel.basic_reject.assert_called_once_with(
            self.delivery_tag,
            requeue=False)
        self.message.channel.basic_publish.assert_called_once_with(
            self.message,
            exchange="search.failed",
            routing_key=self.routing_key)
        self.assertEqual(
            self.message.application_headers["mb-retries"],
            0)


class HandlerTest(AmqpTestCase):

    def setUp(self):
        super(HandlerTest, self).setUp()
        handler.solr_connection = mock.Mock()
        handler.solr_version_check = mock.Mock()

        handler.SCHEMA = {self.entity_type: None}

        solr_version_check_patcher = mock.patch("sir.amqp.handler.solr_version_check")
        self.addCleanup(solr_version_check_patcher.stop)
        solr_version_check_patcher.start()

        self.handler = handler.Handler()
        self.handler.cores[self.entity_type] = mock.Mock()

    def test_delete_callback(self):
        entity_gid = u"90d7709d-feba-47e6-a2d1-8770da3c3d9c"
        self.message = Amqp_Message(
            body='{"_table": "%s", "gid": "%s"}' % (self.entity_type, entity_gid),
            channel=mock.Mock(),
            application_headers={},
        )
        self.message.delivery_tag = self.delivery_tag
        self.message.delivery_info = {"routing_key": self.routing_key}
        self.handler.delete_callback(self.message, "search.delete")

        self.handler.cores[self.entity_type].delete.assert_called_once_with(entity_gid)

    def test_handler_checks_solr_version(self):
        handler.solr_version_check.assert_called_once_with(self.entity_type)

    def test_index_by_fk(self):
        columns = {'id': '1',
                   'area': '2',
                   'type': '3'}
        parsed_message = Message(1, 'area_alias', columns, 'delete')
        handler.SCHEMA = SCHEMA
        handler.multiprocess_live_index = mock.MagicMock()
        self.handler = handler.Handler()
        for entity_type, entity in SCHEMA.items():
            self.handler.cores[entity_type] = mock.Mock()
            entity.build_entity_query = mock.MagicMock()
        self.handler._index_by_fk(parsed_message)
        calls = self.handler.db_session().execute.call_args_list
        self.assertEqual(len(calls), 6)
        actual_queries = [str(call[0][0]) for call in calls]
        expected_queries = [
            'SELECT musicbrainz.place.id AS musicbrainz_place_id \n'
            'FROM musicbrainz.place JOIN musicbrainz.area ON musicbrainz.area.id = musicbrainz.place.area \n'
            'WHERE musicbrainz.area.id = :id_1',
            'SELECT musicbrainz.label.id AS musicbrainz_label_id \n'
            'FROM musicbrainz.label JOIN musicbrainz.area ON musicbrainz.area.id = musicbrainz.label.area \n'
            'WHERE musicbrainz.area.id = :id_1',
            'SELECT musicbrainz.artist.id AS musicbrainz_artist_id \n'
            'FROM musicbrainz.artist JOIN musicbrainz.area ON musicbrainz.area.id = musicbrainz.artist.end_area \n'
            'WHERE musicbrainz.area.id = :id_1',
            'SELECT musicbrainz.artist.id AS musicbrainz_artist_id \n'
            'FROM musicbrainz.artist JOIN musicbrainz.area ON musicbrainz.area.id = musicbrainz.artist.area \n'
            'WHERE musicbrainz.area.id = :id_1',
            'SELECT musicbrainz.artist.id AS musicbrainz_artist_id \n'
            'FROM musicbrainz.artist JOIN musicbrainz.area ON musicbrainz.area.id = musicbrainz.artist.begin_area \n'
            'WHERE musicbrainz.area.id = :id_1',
            'SELECT musicbrainz.area.id AS musicbrainz_area_id \n'
            'FROM musicbrainz.area \n'
            'WHERE musicbrainz.area.id = :id_1']

        self.assertEqual(expected_queries, actual_queries)
