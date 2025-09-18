import os

from muty.log import MutyLogger

from gulp.api.opensearch.filters import GulpQueryFilter
from gulp_client.common import GulpAPICommon
from gulp_client.user import GulpAPIUser


class GulpAPIDb:
    """
    bindings to call gulp's db related API endpoints
    """

    @staticmethod
    async def opensearch_list_index(
        token: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> list[dict]:
        api_common = GulpAPICommon.get_instance()
        res = await api_common.make_request(
            "GET",
            "opensearch_list_index",
            params={
                "req_id": req_id or api_common.req_id,
            },
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def opensearch_delete_index(
        token: str,
        index: str,
        delete_operation: bool = True,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "index": index,
            "delete_operation": delete_operation,
            "req_id": req_id or api_common.req_id,
        }

        res = await api_common.make_request(
            "DELETE",
            "opensearch_delete_index",
            params=params,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def opensearch_rebase_by_query(
        token: str,
        operation_id: str,
        offset_msec: int,
        script: str = None,
        flt: GulpQueryFilter = None,
        req_id: str = None,
        ws_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "offset_msec": offset_msec,
            "ws_id": ws_id or api_common.ws_id,
            "req_id": req_id or api_common.req_id,
        }

        body = {}
        if flt:
            body["flt"] = flt.model_dump(exclude_none=True)
        if script:
            body["script"] = script

        res = await api_common.make_request(
            "POST",
            "opensearch_rebase_by_query",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res
