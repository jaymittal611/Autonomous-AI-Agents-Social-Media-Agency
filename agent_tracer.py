import json
import os
from datetime import datetime
from typing import List, Dict, Any

TRACE_FILE_JSON = "agent_trace.json"
TRACE_FILE_MD = "agent_trace.md"

class AgentTracer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentTracer, cls).__new__(cls)
            cls._instance.traces = []
        return cls._instance

    def log_message(self, sender: str, receiver: str, action: str, content: str, metadata: Dict[str, Any] = None):
        """Records an inter-agent message turn."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "sender": sender,
            "receiver": receiver,
            "action": action,
            "content": content.strip(),
            "metadata": metadata or {}
        }
        self.traces.append(entry)
        self._write_to_disk(entry)

    def _write_to_disk(self, entry: Dict[str, Any]):
        # 1. Update JSON trace file
        with open(TRACE_FILE_JSON, "w", encoding="utf-8") as f:
            json.dump(self.traces, f, indent=2)

        # 2. Append to clean Markdown transcript
        with open(TRACE_FILE_MD, "a", encoding="utf-8") as f:
            f.write(f"### [{entry['timestamp']}] **{entry['sender']}** ➔ **{entry['receiver']}**\n")
            f.write(f"*Action:* `{entry['action']}`\n\n")
            f.write(f"> {entry['content'].replace(chr(10), chr(10) + '> ')}\n\n")
            f.write("---\n\n")

    def get_traces(self) -> List[Dict[str, Any]]:
        return self.traces

    def clear(self):
        self.traces.clear()
        if os.path.exists(TRACE_FILE_JSON):
            os.remove(TRACE_FILE_JSON)
        if os.path.exists(TRACE_FILE_MD):
            os.remove(TRACE_FILE_MD)

tracer = AgentTracer()