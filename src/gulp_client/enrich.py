import json
import os
from typing import Any, Optional

import muty.crypto
import muty.file
import requests
from gulp_client.common import GulpAPICommon
from muty.log import MutyLogger

from gulp.api.opensearch.filters import GulpQueryFilter
from gulp.api.opensearch.structs import GulpQueryParameters
from gulp.structs import GulpMappingParameters, GulpPluginParameters


class GulpAPIEnrich:
    """
    bindings to call gulp's enrich related API endpoints
    """

    @staticmethod
    async def enrich_single_id(
        token: str,
        operation_id: str,
        doc_id: str,
        fields: dict,
        plugin: str,
        plugin_params: GulpPluginParameters = None,
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "doc_id": doc_id,
            "plugin": plugin,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = {
            "plugin_params": plugin_params.model_dump(exclude_none=True) if plugin_params else None,
            "fields": fields,
        }
        res = await api_common.make_request(
            "POST",
            "enrich_single_id",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def enrich_documents(
        token: str,
        operation_id: str,
        fields: dict,
        plugin: str,
        plugin_params: GulpPluginParameters = None,
        flt: GulpQueryFilter = None,
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "plugin": plugin,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = {
            "fields": fields,
            "plugin_params": (
                plugin_params.model_dump(by_alias=True, exclude_none=True)
                if plugin_params
                else None
            ),
            "flt": (
                flt.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)
                if flt
                else None
            ),
        }
        res = await api_common.make_request(
            "POST",
            "enrich_documents",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def tag_documents(
        token: str,
        operation_id: str,
        tags: list[str],
        flt: GulpQueryFilter = None,
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = {
            "tags": tags,
            "flt": (
                flt.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)
                if flt
                else None
            ),
        }
        res = await api_common.make_request(
            "POST",
            "tag_documents",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def update_documents(
        token: str,
        operation_id: str,
        data: dict[str, Any],
        flt: GulpQueryFilter = None,
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = {
            "data": data,
            "flt": (
                flt.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)
                if flt
                else None
            ),
        }
        res = await api_common.make_request(
            "POST",
            "update_documents",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def tag_single_id(
        token: str,
        operation_id: str,
        doc_id: str,
        tags: list[str],
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "doc_id": doc_id,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = tags
        res = await api_common.make_request(
            "POST",
            "tag_single_id",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def update_single_id(
        token: str,
        operation_id: str,
        doc_id: str,
        data: dict[str, Any],
        expected_status: int = 200,
        req_id: str = None,
        ws_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "doc_id": doc_id,
            "req_id": req_id or api_common.req_id,
            "ws_id": ws_id or api_common.ws_id,
        }
        body = data
        res = await api_common.make_request(
            "POST",
            "update_single_id",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res

    @staticmethod
    async def enrich_remove(
        token: str,
        operation_id: str,
        flt: GulpQueryFilter = None,
        expected_status: int = 200,
        req_id: str = None,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        params = {
            "operation_id": operation_id,
            "req_id": req_id or api_common.req_id,
        }
        body = flt.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True) if flt else None        
        res = await api_common.make_request(
            "POST",
            "enrich_remove",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )
        return res
