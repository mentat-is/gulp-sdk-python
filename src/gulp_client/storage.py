from gulp.api.collab.structs import GulpCollabFilter
from gulp_client.common import GulpAPICommon


class GulpAPIStorage:
    """
    bindings to call gulp's storage related API endpoints
    """
    
    @staticmethod
    async def storage_list_files(
        token: str,
        operation_id: str = None,
        context_id: str = None,
        continuation_token: str = None,
        max_results: int = 100,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        params = {
            "operation_id": operation_id,
            "context_id": context_id,
            "continuation_token": continuation_token,
            "max_results": max_results,
            "req_id": req_id or api_common.req_id,
        }

        res = await api_common.make_request(
            "GET",
            "storage_list_files",
            params=params,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def storage_delete_by_id(
        token: str,
        operation_id: str,
        storage_id: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        params = {
            "operation_id": operation_id,
            "storage_id": storage_id,
            "req_id": req_id or api_common.req_id,
        }

        res = await api_common.make_request(
            "DELETE",
            "storage_delete_by_id",
            params=params,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def storage_delete_by_tags(
        token: str,
        operation_id: str = None,
        context_id: str = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        params = {
            "operation_id": operation_id,
            "context_id": context_id,
            "req_id": req_id or api_common.req_id,
        }

        res = await api_common.make_request(
            "DELETE",
            "storage_delete_by_tags",
            params=params,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def storage_file_get_by_id(
        token: str,
        operation_id: str,
        storage_id: str,
        local_path: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> str:
        """
        Download a file from the filestore by its ``storage_id``.

        This corresponds to the ``storage_file_get_by_id_handler`` server
        endpoint which returns a ``FileResponse`` streaming the object
        contents.  The client method simply issues a GET request and streams
        the response into ``local_path``.  ``token`` and ``req_id`` are
        passed as query parameters as usual.
        """
        api_common = GulpAPICommon.get_instance()

        params = {
            "operation_id": operation_id,
            "storage_id": storage_id,
            "req_id": req_id or api_common.req_id,
        }

        # reuse the helper in common for streaming download via GET
        return await api_common.download_file(
            "storage_get_file_by_id",
            local_path,
            params=params,
            token=token,
            expected_status=expected_status,
        )

