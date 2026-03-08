import asyncio
import json
import multiprocessing
import os
from typing import Any

import muty.string
import requests
import aiofiles
import websockets
from gulp_client.test_values import (
    TEST_CONTEXT_NAME,
    TEST_HOST,
    TEST_INDEX,
    TEST_OPERATION_ID,
    TEST_REQ_ID,
    TEST_WS_ID,
)
from muty.log import MutyLogger

from gulp.api.collab.stats import GulpIngestionStats, GulpRequestStats
from gulp.api.collab.structs import GulpCollabFilter
from gulp.api.collab_api import GulpCollab
from gulp.api.opensearch.filters import GulpIngestionFilter
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
        admin_token,
        "editor",
        "editor",
        ["read", "edit"],
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


async def _cleanup_test_operation():
    """
    cleanup (not delete) test_operation collab objects (and guest user data)
    """
    GulpAPICommon.get_instance().init(
        host=TEST_HOST, ws_id=TEST_WS_ID, req_id=TEST_REQ_ID, index=TEST_INDEX
    )
    from gulp_client.operation import GulpAPIOperation
    from gulp_client.user import GulpAPIUser

    admin_token = await GulpAPIUser.login_admin()
    guest_token = await GulpAPIUser.login("guest", "guest")

    assert admin_token
    assert guest_token
    await GulpAPIOperation.operation_cleanup(admin_token, TEST_OPERATION_ID)
    await GulpAPIUser.user_delete_data(guest_token)
    await GulpAPIUser.user_delete_data(admin_token)


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
    from gulp_client.operation import GulpAPIOperation
    from gulp_client.user import GulpAPIUser

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

    # start the ingest loop
    t = asyncio.create_task(_test_ingest_ws_loop(check_ingested=check_ingested, check_processed=check_processed))
    await asyncio.sleep(1)

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
    await t


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

    from gulp_client.user import GulpAPIUser

    admin_token = await GulpAPIUser.login_admin()
    assert admin_token

    async with websockets.connect(ws_url) as ws:
        # connect websocket
        p: GulpWsAuthPacket = GulpWsAuthPacket(token=admin_token, ws_id=TEST_WS_ID)
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
                    stats: GulpRequestStats = GulpRequestStats.from_dict(payload["obj"])
                    stats_data: GulpIngestionStats = GulpIngestionStats.model_validate(
                        payload["obj"]["data"]
                    )
                    MutyLogger.get_instance().info("stats: %s", stats)
                    records_ingested = stats_data.records_ingested
                    records_processed = stats_data.records_processed
                    records_skipped = stats_data.records_skipped

                    # perform checks
                    skipped_test_succeeded = True
                    processed_test_succeeded = True
                    ingested_test_succeeded = True
                    success_test_succeeded = True
                    if check_ingested is not None:
                        if records_ingested == check_ingested:
                            MutyLogger.get_instance().info(
                                "all %d records ingested!", check_ingested
                            )
                            ingested_test_succeeded = True
                        else:
                            ingested_test_succeeded = False

                    if check_processed is not None:
                        if records_processed == check_processed:
                            MutyLogger.get_instance().info(
                                "all %d records processed!", check_processed
                            )
                            processed_test_succeeded = True
                        else:
                            processed_test_succeeded = False

                    if check_skipped is not None:

                        if records_skipped == check_skipped:
                            MutyLogger.get_instance().info(
                                "all %d records skipped!", check_skipped
                            )
                            skipped_test_succeeded = True
                        else:
                            skipped_test_succeeded = False

                    if success is not None:
                        if stats.status == "done":
                            MutyLogger.get_instance().info("success!")
                            success_test_succeeded = True
                        else:
                            success_test_succeeded = False

                    if skip_checks:
                        if stats.status != "ongoing":
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
                    if stats.status in ["failed", "canceled"]:
                        MutyLogger.get_instance().error(
                            "ingestion failed/canceled, breaking the loop!"
                        )
                        break
                else:
                    # print other messages
                    if data["type"] != "docs_chunk":
                        # avoid flooding
                        MutyLogger.get_instance().debug(data)
                        # MutyLogger.get_instance().debug(muty.string.make_shorter(str(data, max_len=260)))
                    
                # ws delay
                await asyncio.sleep(0.1)

        except websockets.exceptions.ConnectionClosed as ex:
            MutyLogger.get_instance().exception(ex)

    MutyLogger.get_instance().info(
        "found_ingested=%s, requested=%s, found_processed=%s (requested=%s), found_skipped=%s (requested=%s)",
        records_ingested,
        check_ingested,
        records_processed,
        check_processed,
        records_skipped,
        check_skipped,
    )
    assert test_completed
    MutyLogger.get_instance().info("_test_ingest_ws_loop succeeded!")


async def _test_ai_report_ws_loop(
    ws_id: str = TEST_WS_ID,
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
    from gulp_client.user import GulpAPIUser

    admin_token = await GulpAPIUser.login_admin()
    assert admin_token
    async with websockets.connect(ws_url) as ws:
        # connect websocket
        p: GulpWsAuthPacket = GulpWsAuthPacket(token=admin_token, ws_id=ws_id)
        await ws.send(p.model_dump_json(exclude_none=True))

        # receive responses
        report = ""
        try:
            while True:
                response = await ws.recv()
                data = json.loads(response)

                if data["type"] == "ai_report_done":
                    # stats update
                    payload = data.get("payload", "")
                    report = payload
                    break
                if data["type"] == "ai_report_failed":
                    report = ""
                    break

                # ws delay
                await asyncio.sleep(0.1)

        except websockets.exceptions.ConnectionClosed as ex:
            MutyLogger.get_instance().exception(ex)
    if report:
        MutyLogger.get_instance().info("_test_ai_report_ws_loop succes")
        return report
    raise Exception()


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
        must be called before any other method.

        if log_request or log_response are True, the requests and/or responses will be logged
        if GULP_SDK_LOG_REQUEST or GULP_SDK_LOG_RESPONSE env vars are set to "1", they override the parameters
        """
        # check env first
        env_log_request = os.getenv("GULP_SDK_LOG_REQUEST", "0")
        env_log_response = os.getenv("GULP_SDK_LOG_RESPONSE", "0")
        if env_log_request == "1":
            log_request = True
        if env_log_response == "1":
            log_response = True

        self.index = index
        self.ws_id = ws_id
        self.req_id = req_id
        self.host = host
        self._log_res = log_response
        self._log_req = log_request

        # needed for sqlalchemy ORM objects
        GulpCollab.init_mappers()

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
        # allow body to be sent for DELETE as well (some endpoints accept a body with DELETE)
        elif method in ["POST", "PATCH", "PUT", "DELETE"] and body:
            r = requests.request(method, url, headers=headers, params=params, json=body)
        else:
            r = requests.request(method, url, headers=headers, params=params)

        self._log_response(r)
        MutyLogger.get_instance().debug("response status code: %d, expected=%d", r.status_code, expected_status)
        assert r.status_code == expected_status

        return r.json().get("data") if r.status_code == 200 else {}

    async def download_file_to_memory(
        self,
        endpoint: str,
        params: dict = None,
        token: str = None,
        headers: dict = None,
        expected_status: int = 200,
    ) -> bytes:
        """
        Download the response body from a GET request to `endpoint` and return it as bytes.

        Args:
            endpoint: API endpoint to send the GET request to
            params: query parameters to include in the GET request
            token: optional authentication token to include in the request headers
            headers: optional additional headers to include in the request
            expected_status: expected HTTP status code of the response (default: 200)
        Returns:
            The response content as bytes if the download was successful.
        """            
        # build url and headers like make_request
        url = self._make_url(endpoint)
        if headers:
            if token:
                headers.update({"token": token})
        else:
            headers = {"token": token} if token else {}

        # log the download request similar to make_request
        self._log_request("GET", url, {"params": params, "headers": headers})

        # perform the request
        r = requests.get(url, headers=headers, params=params)

        self._log_response(r)
        MutyLogger.get_instance().debug("response status code: %d, expected=%d", r.status_code, expected_status)
        assert r.status_code == expected_status

        return r.content
    
    async def download_file(
        self,
        endpoint: str,
        local_path: str,
        params: dict = None,
        token: str = None,
        headers: dict = None,
        expected_status: int = 200,
    ) -> str:
        """
        Download the response body from a GET request to `endpoint` and save it to
        `local_path`.

        Args:
            endpoint: API endpoint to send the GET request to
            local_path: local file path to save the downloaded content
            params: query parameters to include in the GET request
            token: optional authentication token to include in the request headers
            headers: optional additional headers to include in the request
            expected_status: expected HTTP status code of the response (default: 200)
        
        Returns:
            The `local_path` where the file was saved if the download was successful.
        """
        # build url and headers like make_request
        url = self._make_url(endpoint)
        if headers:
            if token:
                headers.update({"token": token})
        else:
            headers = {"token": token} if token else {}

        # log the download request similar to make_request
        self._log_request("GET", url, {"params": params, "headers": headers})

        # perform the request with streaming
        r = requests.get(url, headers=headers, params=params, stream=True)

        # log status without attempting to decode JSON (may be binary)
        if self._log_res:
            MutyLogger.get_instance().debug(f"RESPONSE Status: {r.status_code}")

        MutyLogger.get_instance().debug("response status code: %d, expected=%d", r.status_code, expected_status)
        assert r.status_code == expected_status

        # write to file asynchronously
        # note: requests is still synchronous, but we stream bytes into the
        # destination without blocking the event loop for file I/O.
        async with aiofiles.open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    await f.write(chunk)

        return local_path

    async def upload_files(
        self,
        endpoint: str,
        file_paths: list[str],
        params: dict = None,
        token: str = None,
        headers: dict = None,
        expected_status: int = 200,
    ) -> dict:
        """
        Upload one or more files to a POST endpoint.

        This convenience wraps :meth:`make_request` by constructing a files
        dictionary from the provided ``file_paths``.  The keys are generated as
        ``file0``, ``file1``, etc., with each value being a ``(filename,
        fileobj)`` tuple.  All files are closed after the request completes.

        Parameters are the same as :meth:`make_request` except ``body`` is not
        used.  ``params`` will be passed as query parameters, and ``token``/``headers``
        are handled the same way as in :meth:`make_request`.
        """
        # prepare file objects
        fobjs = []
        files = {}
        for idx, path in enumerate(file_paths):
            f = open(path, "rb")
            fobjs.append(f)
            files[f"file{idx}"] = (os.path.basename(path), f)

        try:
            res = await self.make_request(
                "POST",
                endpoint,
                params=params or {},
                token=token,
                files=files,
                headers=headers,
                expected_status=expected_status,
            )
        finally:
            # ensure all file handles are closed
            for f in fobjs:
                try:
                    f.close()
                except Exception:
                    pass

        return res

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
