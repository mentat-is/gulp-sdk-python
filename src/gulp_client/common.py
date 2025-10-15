import asyncio
import json
import multiprocessing
import os
from typing import Any

import requests
import websockets
from muty.log import MutyLogger
from gulp.api.collab.structs import GulpCollabFilter
from gulp.api.opensearch.filters import GulpIngestionFilter
from gulp_client.test_values import (
    TEST_CONTEXT_NAME,
    TEST_HOST,
    TEST_INDEX,
    TEST_OPERATION_ID,
    TEST_REQ_ID,
    TEST_WS_ID,
)
from gulp.api.ws_api import GulpWsAuthPacket
from gulp.structs import GulpPluginParameters


async def _ensure_test_users(
    admin_token: str = None,
    init_api: bool = False,
    log_request: bool = False,
    log_response: bool = False,
):
    """
    ensure that the test users exist
    """

    from gulp_client.user import GulpAPIUser

    if init_api:
        GulpAPICommon.get_instance().init(
            host=TEST_HOST,
            ws_id=TEST_WS_ID,
            req_id=TEST_REQ_ID,
            index=TEST_INDEX,
            log_request=log_request,
            log_response=log_response,
        )

    if not admin_token:
        admin_token = await GulpAPIUser.login_admin()
        assert admin_token

    # ensure deletion of test users if they exist
    try:
        await GulpAPIUser.user_delete(admin_token, "editor")
    except Exception:
        pass
    try:
        await GulpAPIUser.user_delete(admin_token, "ingest")
    except Exception:
        pass
    try:
        await GulpAPIUser.user_delete(admin_token, "power")
    except Exception:
        pass

    # create users
    res = await GulpAPIUser.user_create(
        admin_token, "editor", "editor", ["read", "edit"]
    )
    assert res["id"] == "editor"
    res = await GulpAPIUser.user_create(
        admin_token, "ingest", "ingest", ["read", "edit", "ingest"]
    )
    assert res["id"] == "ingest"
    res = await GulpAPIUser.user_create(
        admin_token, "power", "power", ["read", "edit", "delete"]
    )
    assert res["id"] == "power"


async def _ensure_test_operation(
    delete_data: bool = True, log_request: bool = False, log_response: bool = False
) -> None:
    """
    ensure that the test operation exists and its clean

    Args:
        delete_data: if True, delete the data in the operation on OpenSearch
    """
    GulpAPICommon.get_instance().init(
        host=TEST_HOST,
        ws_id=TEST_WS_ID,
        req_id=TEST_REQ_ID,
        index=TEST_INDEX,
        log_request=log_request,
        log_response=log_response,
    )
    from gulp_client.user import GulpAPIUser
    from gulp_client.operation import GulpAPIOperation

    admin_token = await GulpAPIUser.login_admin()
    assert admin_token

    # ensure test users exists
    await _ensure_test_users(admin_token)

    # this may fail if operation does not exist
    try:
        await GulpAPIOperation.operation_delete(
            admin_token, TEST_OPERATION_ID, delete_data=delete_data
        )
    except Exception as e:
        MutyLogger.get_instance().warning(
            f"probably operation {TEST_OPERATION_ID} does not exist, ignoring: {e}"
        )
    create_index: bool = True
    if not delete_data:
        # if we don't delete data, we don't want to create the index again
        create_index = False
    res = await GulpAPIOperation.operation_create(
        admin_token,
        TEST_OPERATION_ID,
        set_default_grants=True,
        create_index=create_index,
    )
    assert res["id"] == TEST_OPERATION_ID

    # grant test users access to the operation
    from gulp_client.object_acl import GulpAPIObjectACL

    await GulpAPIObjectACL.object_add_granted_user(
        admin_token, TEST_OPERATION_ID, "operation", "editor"
    )
    await GulpAPIObjectACL.object_add_granted_user(
        admin_token, TEST_OPERATION_ID, "operation", "power"
    )
    await GulpAPIObjectACL.object_add_granted_user(
        admin_token, TEST_OPERATION_ID, "operation", "guest"
    )
    await GulpAPIObjectACL.object_add_granted_user(
        admin_token, TEST_OPERATION_ID, "operation", "ingest"
    )


def _process_file_in_worker_process(
    host: str,
    ws_id: str,
    req_id: str,
    index: str,
    plugin: str,
    plugin_params: GulpPluginParameters,
    flt: GulpIngestionFilter,
    file_path: str,
    file_total: int,
):
    """
    process a file
    """

    async def _process_file_async():
        GulpAPICommon.get_instance().init(
            host=host, ws_id=ws_id, req_id=req_id, index=index
        )
        MutyLogger.get_instance().info(f"processing file: {file_path}")
        from gulp_client.user import GulpAPIUser

        ingest_token = await GulpAPIUser.login("ingest", "ingest")
        assert ingest_token

        # ingest the file
        from gulp_client.ingest import GulpAPIIngest

        await GulpAPIIngest.ingest_file(
            ingest_token,
            file_path=file_path,
            operation_id=TEST_OPERATION_ID,
            context_name=TEST_CONTEXT_NAME,
            plugin=plugin,
            flt=flt,
            plugin_params=plugin_params,
            file_total=file_total,
        )

    asyncio.run(_process_file_async())


async def _test_ingest_generic(
    files: list[str],
    plugin: str,
    check_ingested: int,
    check_processed: int = None,
    plugin_params: GulpPluginParameters = None,
    flt: GulpIngestionFilter = None,
) -> str:
    """
    for each file, spawn a process using multiprocessing and perform ingestion with the selected plugin

    :param files: list of files to ingest
    :param plugin: plugin to use
    :param check_ingested: number of ingested records to check
    :param check_processed: number of processed records to check
    :param plugin_params: plugin parameters
    :param flt: ingestion filter
    """
    # this must be called manually since we're in a worker process and the _setup() fixture has not been called there...
    GulpAPICommon.get_instance().init(
        host=TEST_HOST, ws_id=TEST_WS_ID, req_id=TEST_REQ_ID, index=TEST_INDEX
    )

    # for each file, spawn a process using multiprocessing
    for file in files:
        p = multiprocessing.Process(
            target=_process_file_in_worker_process,
            args=(
                TEST_HOST,
                TEST_WS_ID,
                TEST_REQ_ID,
                TEST_INDEX,
                plugin,
                plugin_params,
                flt,
                file,
                len(files),
            ),
        )
        p.start()

    # wait for all processes to finish
    await _test_ingest_ws_loop(
        check_ingested=check_ingested, check_processed=check_processed
    )


async def _test_ingest_ws_loop(
    check_ingested: int = None,
    check_processed: int = None,
    check_skipped: int = None,
    skip_checks: bool = False,
    success: bool = None,
):
    """
    open a websocket and wait for the ingestion to complete, optionally enforcing check of the number of ingested/processed records

    :param check_ingested: if not None, check the number of ingested records
    :param check_processed: if not None, check the number of processed records
    :param check_skipped: if not None, check the number of skipped records
    :param success: if not None, check if the ingestion was successful
    """
    _, host = TEST_HOST.split("://")
    ws_url = f"ws://{host}/ws"
    test_completed = False
    records_ingested = 0
    records_processed = 0
    records_skipped = 0

    async with websockets.connect(ws_url) as ws:
        # connect websocket
        p: GulpWsAuthPacket = GulpWsAuthPacket(token="monitor", ws_id=TEST_WS_ID)
        await ws.send(p.model_dump_json(exclude_none=True))

        # receive responses
        try:
            while True:
                response = await ws.recv()
                data = json.loads(response)
                # print(data)
                # wait for the stats update
                payload = data.get("payload", {})
                if (
                    payload
                    and data["type"] == "stats_update"
                    and payload["obj"]["req_type"] == "ingest"
                ):
                    # stats update
                    stats = payload["obj"]
                    stats_data = payload["obj"]["data"]
                    MutyLogger.get_instance().info(f"ingestion stats: {stats_data}")
                    records_ingested = stats_data.get("records_ingested", 0)
                    records_processed = stats_data.get("records_processed", 0)
                    records_skipped = stats_data.get("records_skipped", 0)

                    # perform checks
                    skipped_test_succeeded = True
                    processed_test_succeeded = True
                    ingested_test_succeeded = True
                    success_test_succeeded = True
                    if check_ingested is not None:
                        if records_ingested == check_ingested:
                            MutyLogger.get_instance().info(
                                "all %d records ingested!" % (check_ingested)
                            )
                            ingested_test_succeeded = True
                        else:
                            ingested_test_succeeded = False

                    if check_processed is not None:
                        if records_processed == check_processed:
                            MutyLogger.get_instance().info(
                                "all %d records processed!" % (check_processed)
                            )
                            processed_test_succeeded = True
                        else:
                            processed_test_succeeded = False

                    if check_skipped is not None:

                        if records_skipped == check_skipped:
                            MutyLogger.get_instance().info(
                                "all %d records skipped!" % (check_skipped)
                            )
                            skipped_test_succeeded = True
                        else:
                            skipped_test_succeeded = False

                    if success is not None:
                        if stats["status"] == "done":
                            MutyLogger.get_instance().info("success!")
                            success_test_succeeded = True
                        else:
                            success_test_succeeded = False

                    if skip_checks:
                        if stats["status"] != "ongoing":
                            MutyLogger.get_instance().info(
                                "request done, checks skipped, breaking the loop!"
                            )
                            test_completed = True
                            break

                    if (
                        ingested_test_succeeded
                        and processed_test_succeeded
                        and skipped_test_succeeded
                        and success_test_succeeded
                    ):
                        MutyLogger.get_instance().info(
                            "all tests succeeded, breaking the loop!"
                        )
                        test_completed = True
                        break

                    # check for failed/canceled
                    if stats["status"] == "failed" or stats["status"] == "canceled":
                        break

                # ws delay
                await asyncio.sleep(0.1)

        except websockets.exceptions.ConnectionClosed as ex:
            MutyLogger.get_instance().exception(ex)

    MutyLogger.get_instance().info(
        f"found_ingested={records_ingested} (requested={check_ingested}), found_processed={
            records_processed} (requested={check_processed}), found_skipped={records_skipped} (requested={check_skipped})"
    )
    assert test_completed
    MutyLogger.get_instance().info("_test_ingest_ws_loop succeeded!")


class GulpAPICommon:
    _instance: "GulpAPICommon" = None

    def __init__(self):
        pass

    def __new__(cls):
        """
        Create a new instance of the class.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def _initialize(self):
        MutyLogger.get_instance("gulp_test")

    def init(
        self,
        host: str,
        ws_id: str = None,
        req_id: str = None,
        index: str = None,
        log_request: bool = False,
        log_response: bool = False,
    ):
        """
        must be called before any other method
        """
        self.index = index
        self.ws_id = ws_id
        self.req_id = req_id
        self.host = host
        self._log_res = log_response
        self._log_req = log_request

    def _make_url(self, endpoint: str) -> str:
        return f"{self.host}/{endpoint}"

    def _log_request(self, method: str, url: str, params: dict):
        if not self._log_req:
            return
        if not params:
            params = {}
        MutyLogger.get_instance().debug(f"REQUEST {method} {url}")
        MutyLogger.get_instance().debug(f"REQUEST PARAMS: {params}")

    def _log_response(self, r: requests.Response):
        if not self._log_res:
            return
        MutyLogger.get_instance().debug(f"RESPONSE Status: {r.status_code}")
        MutyLogger.get_instance().debug(
            f"RESPONSE Body: {json.dumps(r.json(), indent=2)}"
        )

    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: dict,
        token: str = None,
        body: Any = None,
        files: dict = None,
        headers: dict = None,
        expected_status: int = 200,
    ) -> dict:
        """
        make request, verify status, return "data" member or {}
        params:
            files: dict of file objects, e.g. {'file': ('filename.txt', open('file.txt', 'rb'))}
        """
        url = self._make_url(endpoint)
        if headers:
            headers.update({"token": token})
        else:
            headers = {"token": token} if token else {}

        self._log_request(
            method,
            url,
            {"params": params, "body": body, "headers": headers, "files": files},
        )

        # handle file uploads and regular requests
        if files:
            # for file uploads, body data needs to be part of form-data
            data = body if body else None
            r = requests.request(
                method, url, headers=headers, params=params, files=files, data=data
            )
        elif method in ["POST", "PATCH", "PUT"] and body:
            r = requests.request(method, url, headers=headers, params=params, json=body)
        else:
            r = requests.request(method, url, headers=headers, params=params)

        self._log_response(r)
        MutyLogger.get_instance().debug("response status code: %d", r.status_code)
        assert r.status_code == expected_status

        return r.json().get("data") if r.status_code == 200 else {}

    async def object_delete(
        self,
        token: str,
        obj_id: str,
        api: str,
        operation_id: str = None,
        req_id: str = None,
        ws_id: str = None,
        expected_status: int = 200,
    ) -> dict:
        """
        common object deletion
        """
        MutyLogger.get_instance().info(
            f"Deleting object {obj_id}, operation_id={operation_id}, api={api}..."
        )
        params = {
            "obj_id": obj_id,
            "ws_id": ws_id or self.ws_id,
            "req_id": req_id or self.req_id,
        }
        if operation_id:
            params["operation_id"] = operation_id
        res = await self.make_request(
            "DELETE", api, params=params, token=token, expected_status=expected_status
        )
        return res

    async def object_get_by_id(
        self,
        token: str,
        obj_id: str,
        api: str,
        operation_id: str = None,
        req_id: str = None,
        expected_status: int = 200,
        **kwargs,
    ) -> dict:
        """
        common object get
        """
        MutyLogger.get_instance().info(
            f"Getting object {obj_id}, operation_id={operation_id}, api={api}..."
        )
        params = {
            "obj_id": obj_id,
            "req_id": req_id or self.req_id,
            **kwargs,
        }
        if operation_id:
            params["operation_id"] = operation_id

        res = await self.make_request(
            "GET",
            api,
            params=params,
            token=token,
            expected_status=expected_status,
        )
        return res

    async def object_list(
        self,
        token: str,
        api: str,
        operation_id: str = None,
        flt: GulpCollabFilter = None,
        req_id: str = None,
        expected_status: int = 200,
    ) -> list[dict]:
        """
        common object list
        """
        MutyLogger.get_instance().info(
            "Listing objects for operation_id=%s, flt=%s, : api=%s ..."
            % (operation_id, flt, api)
        )
        params = {"req_id": req_id or self.req_id}
        if operation_id:
            params["operation_id"] = operation_id

        res = await self.make_request(
            "POST",
            api,
            params=params,
            body=(
                flt.model_dump(by_alias=True, exclude_none=True, exclude_defaults=True)
                if flt
                else None
            ),
            token=token,
            expected_status=expected_status,
        )
        return res
