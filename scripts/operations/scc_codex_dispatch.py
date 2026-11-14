"""Start the next SCC continuation in a saved Codex desktop project."""

import json
import subprocess
from collections.abc import Callable
from itertools import count
from pathlib import Path

CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")
MODEL = "gpt-6-astra"
EFFORT = "ultra"


def dispatch(
    project_id: str,
    cwd: Path,
    title: str,
    prompt: str,
    record_thread: Callable[[str], None],
) -> str:
    with subprocess.Popen(
        [CODEX, "app-server"],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
    ) as server:
        assert server.stdin is not None and server.stdout is not None
        ids = count(1)
        completed_turns = {}

        def send(message):
            server.stdin.write(json.dumps(message) + "\n")
            server.stdin.flush()

        def messages():
            for line in server.stdout:
                message = json.loads(line)
                if "method" in message and "id" in message:
                    send(
                        {
                            "id": message["id"],
                            "error": {
                                "code": -32601,
                                "message": "Unattended SCC client.",
                            },
                        }
                    )
                elif message.get("method") == "turn/completed":
                    terminal = message["params"]
                    turn = terminal["turn"]
                    completed_turns[terminal["threadId"], turn["id"]] = turn["status"]
                yield message

        stream = messages()

        def request(method, params):
            request_id = next(ids)
            send({"id": request_id, "method": method, "params": params})
            for message in stream:
                if "method" not in message and message.get("id") == request_id:
                    if "error" in message:
                        detail = message["error"]["message"]
                        raise RuntimeError(f"Codex {method}: {detail}")
                    return message["result"]
            raise RuntimeError(f"Codex disconnected during {method}")

        try:
            request(
                "initialize",
                {
                    "clientInfo": {"name": "pose-embed-scc", "version": "1"},
                    "capabilities": {"experimentalApi": True},
                },
            )
            send({"method": "initialized"})
            project = request("project/read", {"projectId": project_id})["project"]
            roots = project["roots"]
            if len(roots) != 1:
                raise RuntimeError(
                    "Expected one working directory for the Codex project"
                )
            project_root = roots[0]["path"]
            started = request(
                "thread/start",
                {
                    "projectId": project_id,
                    # Older desktop builds group project chats by this directory.
                    "cwd": project_root,
                    "model": MODEL,
                    "config": {"model_reasoning_effort": EFFORT},
                },
            )
            thread = started["thread"]
            thread_id = thread["id"]
            if (
                thread["projectId"] != project_id
                or thread["cwd"] != project_root
                or started["model"] != MODEL
                or started["reasoningEffort"] != EFFORT
            ):
                raise RuntimeError(
                    "Codex did not apply the project, directory or model"
                )
            request("thread/name/set", {"threadId": thread_id, "name": title})
            record_thread(thread_id)
            turn = request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": prompt}],
                    "model": MODEL,
                    "effort": EFFORT,
                },
            )["turn"]
            key = (thread_id, turn["id"])
            while key not in completed_turns:
                if next(stream, None) is None:
                    raise RuntimeError(
                        f"Codex disconnected before {thread_id} finished"
                    )
            status = completed_turns[key]
            if status != "completed":
                raise RuntimeError(f"Codex thread {thread_id} turn ended: {status}")
            return thread_id
        finally:
            # Keep the stdio server alive until the accepted turn has ended.
            server.terminate()
