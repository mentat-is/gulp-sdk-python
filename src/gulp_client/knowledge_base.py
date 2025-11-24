import json
import os
from gulp.api.collab.structs import GulpCollabFilter
from gulp_client.common import GulpAPICommon

import muty.crypto


class GulpAPIKB:

    @staticmethod
    async def create_kb(
        token: str,
        name: str,
        description: str = None,
        is_folder: bool = False,
        parent_id: str = None,
        attachments: list[dict] = None,
        tags: list[str] = None,
        glyph_id: str = None,
        private: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """Create a new knowledge base entry"""
        api_common = GulpAPICommon.get_instance()

        params = {
            "name": name,
            "glyph_id": glyph_id,
            "private": private,
            "req_id": req_id,
        }

        body = {
            "description": description,
            "is_folder": is_folder,
            "parent_id": parent_id,
            "attachments": attachments,
            "tags": tags,
        }

        res = await api_common.make_request(
            "PUT",
            "/create_kb",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )

        return res

    @staticmethod
    async def update_kb(
        token: str,
        obj_id: str,
        name: str,
        description: str = None,
        attachments: list[dict] = None,
        tags: list[str] = None,
        glyph_id: str = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """update an existing knowledge base entry"""
        api_common = GulpAPICommon.get_instance()

        params = {
            "obj_id": obj_id,
            "name": name,
            "glyph_id": glyph_id,
            "req_id": req_id,
        }

        body = {
            "description": description,
            "attachments": attachments,
            "tags": tags,
        }

        res = await api_common.make_request(
            "POST",
            "/update_kb",
            params=params,
            body=body,
            token=token,
            expected_status=expected_status,
        )

        return res

    @staticmethod
    async def delete_kb(
        token: str,
        obj_id: str,
        ws_id: str = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """Delete a knowledge base entry"""

        api_common = GulpAPICommon.get_instance()
        return await api_common.object_delete(
            token=token,
            obj_id=obj_id,
            api="/delete_kb",
            req_id=req_id,
            ws_id=ws_id,
            expected_status=expected_status,
        )

    @staticmethod
    async def move_kb(
        token: str, obj_id: str, parent_id: str = None, req_id: str = None
    ) -> dict:
        """Move a knowledge base entry(file or folder) from folder to another folder"""

        api_common = GulpAPICommon.get_instance()

        params = {"obj_id": obj_id, "parent_id": parent_id, "req_id": req_id}
        res = await api_common.make_request(
            "POST", "/move_kb", params=params, token=token
        )

        return res

    @staticmethod
    async def get_kb_by_id(
        token: str, obj_id: str, req_id: str = None, expected_status: int = 200
    ) -> dict:
        """Get a specific knowledge base entry"""

        api_common = GulpAPICommon.get_instance()

        return await api_common.object_get_by_id(
            token=token,
            obj_id=obj_id,
            api="get_kb_by_id",
            expected_status=expected_status,
        )

    @staticmethod
    async def get_kb_list(
        token: str,
        flt: GulpCollabFilter = None,
        req_id: str = None,
        show_tree: bool = False,
        expected_status: int = 200,
    ) -> list[dict]:
        """List stored queries"""
        api_common = GulpAPICommon.get_instance()
        params = {"req_id": req_id}
        body = {"flt": flt, "show_tree": show_tree}

        return await api_common.make_request(
            method="POST",
            endpoint="get_kb_list",
            token=token,
            params=params,
            body=body,
            expected_status=expected_status,
        )

    @staticmethod
    async def upload_kb_from_file(
        token: str,
        name: str,
        file_path: str,
        ws_id: str,
        parent_id: str = None,
        attachments: list[dict] = None,
        tags: list[str] = None,
        glyph_id: str = None,
        private: bool = False,
        req_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        api_common = GulpAPICommon.get_instance()
        total_size = os.path.getsize(file_path)

        params = {
            "name": name,
            "ws_id": ws_id,
            "glyph_id": glyph_id,
            "private": private,
            "req_id": req_id,
        }

        payload = {
            "parent_id": parent_id,
            "attachments": attachments,
            "tags": tags,
        }

        f = open(file_path, "rb")
        files = {
            "payload": ("payload.json", json.dumps(payload), "application/json"),
            "f": (os.path.basename(file_path), f, "application/octet-stream"),
        }

        headers = {"size": str(total_size), "continue_offset": str(0)}

        return await api_common.make_request(
            method="POST",
            endpoint="upload_kb_file",
            token=token,
            params=params,
            files=files,
            headers=headers,
            expected_status=expected_status,
        )
