import io
import os

from gulp_client.common import GulpAPICommon

from gulp.api.collab.structs import GulpCollabFilter
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
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """Get stored query by ID"""
        api_common = GulpAPICommon.get_instance()
        return await api_common.object_get_by_id(
            token=token,
            obj_id=obj_id,
            req_id=req_id,
            api="request_get_by_id",
            expected_status=expected_status,
        )

    @staticmethod
    async def request_cancel(
        token: str,
        req_id_to_cancel: str,
        expire_now: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "req_id_to_cancel": req_id_to_cancel,
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
    async def object_delete_bulk(
        token: str,
        operation_id: str,
        obj_type: str,
        flt: GulpCollabFilter,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "obj_type": obj_type,
            "req_id": req_id or api_common.req_id,
        }
        body = flt.model_dump(exclude_none=True)
        
        res = await api_common.make_request(
            "DELETE",
            "object_delete_bulk",
            params=params,
            token=token,
            body=body,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def request_set_completed(
        token: str,
        req_id_to_complete: str,
        failed: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "req_id_to_complete": req_id_to_complete,
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

    # plugin administration -------------------------------------------------

    @staticmethod
    async def plugin_upload(
        token: str,
        file_paths: list[str],
        plugin_type: str = "default",
        fail_if_exists: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """Upload one or more plugin files.

        ``file_paths`` is a list of local filesystem paths.  The files will be
        posted under the ``files`` form field which matches the server handler
        signature.  ``plugin_type`` and ``fail_if_exists`` are translated into
        query parameters.
        """
        api_common = GulpAPICommon.get_instance()

        params = {
            "plugin_type": plugin_type,
            "fail_if_exists": fail_if_exists,
            "req_id": req_id or api_common.req_id,
        }

        # build files list; using a list of tuples allows multiple entries with
        # the same field name (``files``).
        files: list[tuple] = []
        fobjs: list = []
        try:
            for path in file_paths:
                f = open(path, "rb")
                fobjs.append(f)
                files.append(("files", (os.path.basename(path), f, "application/octet-stream")))

            res = await api_common.make_request(
                "POST",
                "plugin_upload",
                params=params,
                token=token,
                files=files,
                expected_status=expected_status,
            )
        finally:
            for f in fobjs:
                try:
                    f.close()
                except Exception:
                    pass
        return res

    @staticmethod
    async def plugin_delete(
        token: str,
        filename: str,
        plugin_type: str = "default",
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "filename": filename,
            "plugin_type": plugin_type,
            "req_id": req_id or api_common.req_id,
        }
        return await api_common.make_request(
            "DELETE",
            "plugin_delete",
            params=params,
            token=token,
            body=None,
            expected_status=expected_status,
        )

    @staticmethod
    async def plugin_download(
        token: str,
        filename: str,
        local_path: str,
        plugin_type: str = "default",
        req_id: str = None,
        expected_status: int = 200,
    ) -> str:
        api_common = GulpAPICommon.get_instance()
        params = {
            "filename": filename,
            "plugin_type": plugin_type,
            "req_id": req_id or api_common.req_id,
        }
        return await api_common.download_file(
            "plugin_download",
            local_path,
            params=params,
            token=token,
            expected_status=expected_status,
        )

    # config administration -------------------------------------------------

    @staticmethod
    async def config_upload(
        token: str,
        file_path: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {"req_id": req_id or api_common.req_id}
        f = open(file_path, "rb")
        try:
            files = {"file": (os.path.basename(file_path), f, "application/json")}
            res = await api_common.make_request(
                "POST",
                "config_upload",
                params=params,
                token=token,
                files=files,
                expected_status=expected_status,
            )
        finally:
            try:
                f.close()
            except Exception:
                pass
        return res

    @staticmethod
    async def config_download(
        token: str,
        local_path: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> str:
        api_common = GulpAPICommon.get_instance()
        params = {"req_id": req_id or api_common.req_id}
        return await api_common.download_file(
            "config_download",
            local_path,
            params=params,
            token=token,
            expected_status=expected_status,
        )

    # mapping file administration -------------------------------------------------

    @staticmethod
    async def mapping_file_upload(
        token: str,
        file_path: str,
        fail_if_exists: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "fail_if_exists": fail_if_exists,
            "req_id": req_id or api_common.req_id,
        }
        f = open(file_path, "rb")
        try:
            files = {"file": (os.path.basename(file_path), f, "application/json")}
            res = await api_common.make_request(
                "POST",
                "mapping_file_upload",
                params=params,
                token=token,
                files=files,
                expected_status=expected_status,
            )
        finally:
            try:
                f.close()
            except Exception:
                pass
        return res

    @staticmethod
    async def mapping_file_download(
        token: str,
        filename: str,
        local_path: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> str:
        api_common = GulpAPICommon.get_instance()
        params = {
            "filename": filename,
            "req_id": req_id or api_common.req_id,
        }
        return await api_common.download_file(
            "mapping_file_download",
            local_path,
            params=params,
            token=token,
            expected_status=expected_status,
        )

    @staticmethod
    async def mapping_file_delete(
        token: str,
        filename: str,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "filename": filename,
            "req_id": req_id or api_common.req_id,
        }
        return await api_common.make_request(
            "DELETE",
            "mapping_file_delete",
            params=params,
            token=token,
            body=None,
            expected_status=expected_status,
        )

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
        return res
