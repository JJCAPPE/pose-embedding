import importlib.util
import io
import json
from contextlib import nullcontext
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize("disconnect", [False, True])
def test_dispatch_records_the_project_chat_before_starting_a_turn(
    monkeypatch, tmp_path, disconnect
):
    spec = importlib.util.spec_from_file_location(
        "scc_codex_dispatch", "scripts/operations/scc_codex_dispatch.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    sent = []
    project_root = str(tmp_path / "project")

    class Input(io.StringIO):
        def write(self, data):
            sent.append(json.loads(data))
            return super().write(data)

    responses = [
        {"id": 1, "result": {}},
        {
            "id": 2,
            "result": {"project": {"roots": [{"path": project_root}]}},
        },
        {
            "id": 3,
            "result": {
                "thread": {"id": "chat", "projectId": "project", "cwd": project_root},
                "model": "gpt-6-astra",
                "reasoningEffort": "ultra",
            },
        },
        {"id": 4, "result": {}},
        {"id": 5, "result": {"turn": {"id": "turn"}}},
    ]
    if not disconnect:
        responses.insert(
            4,
            {
                "method": "turn/completed",
                "params": {
                    "threadId": "chat",
                    "turn": {"id": "turn", "status": "completed"},
                },
            },
        )
    server = SimpleNamespace(
        stdin=Input(),
        stdout=io.StringIO("".join(json.dumps(line) + "\n" for line in responses)),
        terminate=lambda: sent.append("terminated"),
    )
    monkeypatch.setattr(
        helper.subprocess, "Popen", lambda *a, **kw: nullcontext(server)
    )

    def record_thread(thread_id):
        sent.append(("recorded", thread_id))

    def run():
        return helper.dispatch(
            "project", tmp_path, "SCC job ended", "handoff", record_thread
        )

    if disconnect:
        with pytest.raises(RuntimeError, match="disconnected before chat finished"):
            run()
    else:
        assert run() == "chat"
    assert sent[2]["method"] == "project/read"
    assert sent[2]["params"] == {"projectId": "project"}
    assert sent[3]["params"]["projectId"] == "project"
    assert sent[3]["params"]["cwd"] == project_root
    assert sent[4]["params"]["name"] == "SCC job ended"
    assert sent[5] == ("recorded", "chat")
    assert sent[6]["method"] == "turn/start"
    assert sent[6]["params"] == {
        "threadId": "chat",
        "input": [{"type": "text", "text": "handoff"}],
        "model": "gpt-6-astra",
        "effort": "ultra",
    }
    assert sent[7:] == ["terminated"]
