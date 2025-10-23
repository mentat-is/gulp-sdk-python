import io
import os

from gulp_client.common import GulpAPICommon
from gulp.plugin import GulpUiPluginMetadata


class GulpAPIUtility:
    """
    bindings to call gulp's utility related API endpoints
    """

    @staticmethod
    async def server_status(
        token: str,
        gulp_only: bool = True,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        res = await api_common.make_request(
            "GET",
            "server_status",
            params={"gulp_only": gulp_only, "req_id": req_id or api_common.req_id},
            token=token,
            expected_status=expected_status,
        )

        return res

    @staticmethod
    async def request_get_by_id(
        token: str,
        obj_id: str,
        operation_id: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """Get stored query by ID"""
        api_common = GulpAPICommon.get_instance()
        return await api_common.object_get_by_id(
            token=token,
            obj_id=obj_id,
            operation_id=operation_id,
            req_id=req_id,
            api="request_get_by_id",
            expected_status=expected_status,
        )

    @staticmethod
    async def request_cancel(
        token: str,
        req_id_to_cancel: str,
        operation_id: str,
        status: str = "canceled",
        expire_now: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "req_id_to_cancel": req_id_to_cancel,
            "operation_id": operation_id,
            "status": status,
            "expire_now": expire_now,
            "req_id": req_id or api_common.req_id,
        }
        res = await api_common.make_request(
            "PATCH",
            "request_cancel",
            params=params,
            token=token,
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def request_delete(
        token: str,
        operation_id: str,
        obj_id: str = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "req_id": req_id or api_common.req_id,
        }
        if obj_id:
            params["obj_id"] = obj_id

        res = await api_common.make_request(
            "DELETE",
            "request_delete",
            params=params,
            token=token,
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def request_set_completed(
        token: str,
        req_id_to_complete: str,
        operation_id: str,
        failed: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "req_id_to_complete": req_id_to_complete,
            "operation_id": operation_id,
            "failed": failed,
            "req_id": req_id or api_common.req_id,
        }
        res = await api_common.make_request(
            "PATCH",
            "request_set_completed",
            params=params,
            token=token,
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def request_list(
        token: str,
        operation_id: str = None,
        running_only: bool = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        res = await api_common.make_request(
            "GET",
            "request_list",
            {
                "operation_id": operation_id,
                "running_only": running_only,
                "req_id": req_id or api_common.req_id,
            },
            token=token,
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def plugin_list(
        token: str, req_id: str = None, expected_status: int = 200
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        res = await api_common.make_request(
            "GET",
            "plugin_list",
            {"req_id": req_id or api_common.req_id},
            token=token,
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def ui_plugin_list(req_id: str = None, expected_status: int = 200) -> dict:
        api_common = GulpAPICommon.get_instance()
        res = await api_common.make_request(
            "GET",
            "ui_plugin_list",
            {"req_id": req_id or api_common.req_id},
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def ui_plugin_get(
        plugin: str, req_id: str = None, expected_status: int = 200
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        res = await api_common.make_request(
            "GET",
            "ui_plugin_get",
            {"plugin": plugin, "req_id": req_id or api_common.req_id},
            body=None,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def version(
        token: str, req_id: str = None, expected_status: int = 200
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        """Get gulp version"""
        res = await api_common.make_request(
            "GET",
            "version",
            params={"req_id": req_id or api_common.req_id},
            token=token,
            body=None,
            expected_status=expected_status,
        )

        return res

    @staticmethod
    async def mapping_file_list(
        token: str, req_id: str = None, expected_status: int = 200
    ) -> dict:
        api_common = GulpAPICommon.get_instance()

        res = await api_common.make_request(
            "GET",
            "mapping_file_list",
            params={"req_id": req_id or api_common.req_id},
            token=token,
            body=None,
            expected_status=expected_status,
        )

        return res
