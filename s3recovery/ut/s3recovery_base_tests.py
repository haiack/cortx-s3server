'''
 COPYRIGHT 2020 SEAGATE LLC

 THIS DRAWING/DOCUMENT, ITS SPECIFICATIONS, AND THE DATA CONTAINED
 HEREIN, ARE THE EXCLUSIVE PROPERTY OF SEAGATE TECHNOLOGY
 LIMITED, ISSUED IN STRICT CONFIDENCE AND SHALL NOT, WITHOUT
 THE PRIOR WRITTEN PERMISSION OF SEAGATE TECHNOLOGY LIMITED,
 BE REPRODUCED, COPIED, OR DISCLOSED TO A THIRD PARTY, OR
 USED FOR ANY PURPOSE WHATSOEVER, OR STORED IN A RETRIEVAL SYSTEM
 EXCEPT AS ALLOWED BY THE TERMS OF SEAGATE LICENSES AND AGREEMENTS.

 YOU SHOULD HAVE RECEIVED A COPY OF SEAGATE'S LICENSE ALONG WITH
 THIS RELEASE. IF NOT PLEASE CONTACT A SEAGATE REPRESENTATIVE
 http://www.seagate.com/contact

 Original author: Amit Kumar  <amit.kumar@seagate.com>
 Original creation date: 08-July-2020
'''
#!/usr/bin/python3.6

import mock
import unittest

from s3recovery.s3recoverybase import S3RecoveryBase

from s3backgrounddelete.eos_core_index_api import EOSCoreIndexApi
from s3backgrounddelete.eos_list_index_response import EOSCoreListIndexResponse
from s3backgrounddelete.eos_core_error_respose import EOSCoreErrorResponse

class S3RecoveryBaseTestCase(unittest.TestCase):

    @mock.patch.object(EOSCoreIndexApi, 'list')
    def test_list_index_empty(self, mock_list):
        # Tests 'list_index' when index is empty
        mockS3RecoveryBase = S3RecoveryBase()
        # setup mock
        mock_res = \
            '{"Delimiter":"","Index-Id":"mock-index-id","IsTruncated":"false",\
                "Keys":null,"Marker":"","MaxKeys":"1000","NextMarker":"","Prefix":""}'
        mock_list.return_value = True, EOSCoreListIndexResponse(mock_res.encode())

        keys = mockS3RecoveryBase.list_index('global_index_id')

        self.assertEqual(keys, None)

    @mock.patch.object(EOSCoreIndexApi, 'list')
    @mock.patch.object(EOSCoreListIndexResponse, 'get_index_content')
    def test_list_index_not_empty(self, mock_get_index_content, mock_list):
        # Tests 'list_index' when index is not empty
        mockS3RecoveryBase = S3RecoveryBase()
        # setup mock
        mock_json_res = '{}'
        mock_list.return_value = True, EOSCoreListIndexResponse(
            mock_json_res.encode("utf-8")
            )
        mock_get_index_content.return_value = {
            "Delimiter":"",
            "Index-Id":"mock-index-id",
            "IsTruncated":"false",
            "Keys":[
                {"Key":"key-1","Value":"value-1"},
                {"Key":"key-2","Value":"value-2"}
            ],
            "Marker":"",
            "MaxKeys":"1000",
            "NextMarker":"",
            "Prefix":""
        }
        keys_list = mockS3RecoveryBase.list_index('global_index_id')

        self.assertNotEqual(keys_list, None)
        self.assertEqual(len(keys_list), 2)

    @mock.patch.object(EOSCoreIndexApi, 'list')
    def test_list_index_failed(self, mock_list):
        # Tests 'list_index' when EOSCoreIndexApi.list returned False
        mockS3RecoveryBase = S3RecoveryBase()

        # setup mock
        mock_list.return_value = False, EOSCoreErrorResponse(
            500,
            "",
            "InternalServerError"
        )
        with self.assertRaises(SystemExit) as cm:
            mockS3RecoveryBase.list_index('global_index_id')

        self.assertEqual(cm.exception.code, 1)

    @mock.patch.object(EOSCoreIndexApi, 'list')
    @mock.patch.object(EOSCoreListIndexResponse, 'get_index_content')
    def test_initiate_list_called(self, mock_get_index_content, mock_list):
        # Test 'initiate' function for EOSCoreIndexApi.list called or not
        mockS3RecoveryBase = S3RecoveryBase()

        # setup mock
        mock_res = '{}'
        mock_list.return_value = True, EOSCoreListIndexResponse(mock_res.encode())
        mock_get_index_content.return_value = {
            "Delimiter":"",
            "Index-Id":"mock-index-id",
            "IsTruncated":"false",
            "Keys":[{"Key":"key-1","Value":"value-1"}],
            "Marker":"",
            "MaxKeys":"1000",
            "NextMarker":"","Prefix":""
        }
        mockS3RecoveryBase.initiate(
            'global_index',
            'global_index_id',
            'global_index_id_replica'
        )
        self.assertEqual(mock_list.call_count, 2)

    def test_parse_index_list_response_none_data(self):
        # Test parse_index_list_response when argument passed is None
        mockS3RecoveryBase = S3RecoveryBase()
        ret_dict = mockS3RecoveryBase.parse_index_list_response(None)

        self.assertDictEqual(ret_dict, {})

    def test_parse_index_list_response_empty_data(self):
        # Test parse_index_list_response when argument passed is empty
        key_list = []
        mockS3RecoveryBase = S3RecoveryBase()
        ret_dict = mockS3RecoveryBase.parse_index_list_response(key_list)

        self.assertDictEqual(ret_dict, {})

    def test_parse_index_list_response_success(self):
        # Test parse_index_list_response when argument passed is valid
        key_list = [
            {"Key":"key-1","Value":"value-1"},
            {"Key":"key-2","Value":"value-2"}
        ]
        mockS3RecoveryBase = S3RecoveryBase()
        ret_dict = mockS3RecoveryBase.parse_index_list_response(key_list)

        self.assertEqual(len(ret_dict), 2)

    def test_merge_keys_none_args(self):
        # Test merge_keys when the arguments passed are None
        mockS3RecoveryBase = S3RecoveryBase()

        ret_list = mockS3RecoveryBase.merge_keys('global_index_id', None, None)
        self.assertEqual(len(ret_list), 0)

    def test_merge_keys_same_content(self):
        # Test merge_keys when both data and replica dict have same keys
        data_dict = {
            "key1": "value1",
            "key2": "value2"
        }
        replica_dict = {
            "key1": "value1",
            "key2": "value2"
        }
        mockS3RecoveryBase = S3RecoveryBase()
        ret_list = mockS3RecoveryBase.merge_keys(
            'global_index_id',
            data_dict,
            replica_dict
        )

        self.assertEqual(len(ret_list), 2)

    def test_merge_keys_diff_content(self):
        # Test merge_keys when both data and replica have different keys
        data_dict = {
            "key1": "value1",
            "key2": "value2"
        }
        replica_dict = {
            "key1": "value1",
            "key3": "value3"
        }
        mockS3RecoveryBase = S3RecoveryBase()

        ret_list = mockS3RecoveryBase.merge_keys(
            'global_index_id',
            data_dict,
            replica_dict
        )
        self.assertEqual(len(ret_list), 3)

    def test_perform_validation_data_is_none(self):
        # Test perform_validation when data_to_restore is None
        mock_item_replica = '{"key1": "value1"}'
        mock_union_result = dict()

        mockS3RecoveryBase = S3RecoveryBase()
        mockS3RecoveryBase.perform_validation(
            'key1',
            None,
            mock_item_replica,
            mock_union_result
        )
        self.assertEqual(len(mock_union_result), 1)
        self.assertDictEqual(mock_union_result, {'key1': '{"key1": "value1"}'})

    def test_perform_validation_replica_is_none(self):
        # Test perform_validation when item_replica is None
        mock_data_to_restore = '{"key1": "value1"}'
        mock_union_result = dict()

        mockS3RecoveryBase = S3RecoveryBase()
        mockS3RecoveryBase.perform_validation(
            'key1',
            mock_data_to_restore,
            None,
            mock_union_result
        )
        self.assertEqual(len(mock_union_result), 1)
        self.assertDictEqual(mock_union_result, {'key1': '{"key1": "value1"}'})

    def test_perform_validation_all_none(self):
        # Test perform_validation when both data & item_replica are None
        mock_union_result = dict()

        mockS3RecoveryBase = S3RecoveryBase()
        mockS3RecoveryBase.perform_validation(
            'key1',
            None,
            None,
            mock_union_result
        )
        self.assertEqual(len(mock_union_result), 0)

    def test_perform_validation_corrupt_data(self):
        # Test perform_validation when data_to_restore is corrupt
        mock_data_to_restore = "Invalid-JSON"
        mock_item_replica = '{"key1": "value1"}'
        mock_union_result = dict()
        mockS3RecoveryBase = S3RecoveryBase()

        mockS3RecoveryBase.perform_validation(
            'key1',
            mock_data_to_restore,
            mock_item_replica,
            mock_union_result
        )
        self.assertEqual(len(mock_union_result), 1)
        self.assertDictEqual(mock_union_result, {'key1': '{"key1": "value1"}'})

    def test_perform_validation_all_corrupt(self):
        # Test perform_validation when both data_to_restore and item_replica are corrupt
        mock_data_to_restore = "Invalid-JSON"
        mock_item_replica = "Invalid-JSON"
        mock_union_result = dict()
        mockS3RecoveryBase = S3RecoveryBase()

        mockS3RecoveryBase.perform_validation(
            'key1',
            mock_data_to_restore,
            mock_item_replica,
            mock_union_result
        )

        self.assertEqual(len(mock_union_result), 0)

    def test_perform_validation_success(self):
        # Test perfrom_validation when both data_to_restore and item_replica are valid JSON
        mock_data_to_restore = \
            '{\"account_id\":\"123\",\"account_name\":\"amit-vc\"\
                ,\"create_timestamp\":\"2020-06-16T05:45:41.000Z\"\
                    ,\"location_constraint\":\"us-west-2\"}'
        mock_item_replica = \
            '{\"account_id\":\"123\",\"account_name\":\"amit-vc\"\
                ,\"create_timestamp\":\"2020-06-16T05:50:41.000Z\"\
                    ,\"location_constraint\":\"us-west-2\"}'
        mock_union_result = dict()
        mockS3RecoveryBase = S3RecoveryBase()

        mockS3RecoveryBase.perform_validation(
            'my-bucket1',
            mock_data_to_restore,
            mock_item_replica,
            mock_union_result
        )
        self.assertEqual(len(mock_union_result), 1)

         # This is mock_item_replica as its create_timestamp is greater
         # than mock_data_to_restore
        expected_union_result = {
            'my-bucket1': '{"account_id":"123","account_name":"amit-vc"\
                ,"create_timestamp":"2020-06-16T05:50:41.000Z"\
                    ,"location_constraint":"us-west-2"}'
        }
        self.assertDictEqual(mock_union_result, expected_union_result)

