"""
Ollama Runner — Streams code generation from Ornith via Ollama API.

Handles:
  - Streaming POST /api/chat with httpx
  - Stripping <thinking>...</thinking> blocks (Qwen/Ornith reasoning traces)
  - Extracting the LAST ```python or ``` code block from output
  - Telemetry: TTFT, prompt eval speed, eval count/duration
  - MockStreamClient for offline testing of binary search logic
"""

import re
import json
import time
import httpx


OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "maxwell1500/ornith-35b:q4_K_M"


class OllamaStreamClient:
    """Streams code generation from Ornith via Ollama, stripping reasoning traces."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.ttft = 0.0
        self.total_duration = 0.0
        self.prompt_eval_count = 0
        self.prompt_eval_duration = 0.0
        self.eval_count = 0
        self.eval_duration = 0.0

    @property
    def prompt_eval_speed(self) -> float:
        """Tokens per second during prompt evaluation."""
        if self.prompt_eval_duration > 0:
            return self.prompt_eval_count / self.prompt_eval_duration
        return 0.0

    @property
    def eval_speed(self) -> float:
        """Tokens per second during generation."""
        if self.eval_duration > 0:
            return self.eval_count / self.eval_duration
        return 0.0

    def generate(self, prompt: str, level: int,
                 model_name: str = DEFAULT_MODEL) -> str:
        """
        Send a prompt to Ollama and extract the code from the response.

        Args:
            prompt: The task prompt.
            level: The skill level (1-10), used for logging.
            model_name: The Ollama model tag.

        Returns:
            Extracted code string.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {
                "num_ctx": 8192,
                "temperature": 0.3,
                "top_p": 0.9,
            }
        }

        content_parts = []
        thinking_parts = []
        first_token_time = None
        start_time = time.monotonic()

        with httpx.Client(timeout=180.0) as client:
            with client.stream("POST", url, json=payload) as response:
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg = chunk.get("message", {})
                    content_delta = msg.get("content", "")
                    thinking_delta = msg.get("thinking", "")

                    # Track first meaningful token from either field
                    if (content_delta or thinking_delta) and first_token_time is None:
                        first_token_time = time.monotonic()

                    # Accumulate both content and thinking (Ornith may put code in either)
                    if content_delta:
                        content_parts.append(content_delta)
                    if thinking_delta:
                        thinking_parts.append(thinking_delta)

                    # Check for done signal with metrics
                    if chunk.get("done", False):
                        self.total_duration = chunk.get("total_duration", 0) / 1e9
                        self.prompt_eval_count = chunk.get("prompt_eval_count", 0)
                        self.prompt_eval_duration = chunk.get("prompt_eval_duration", 0) / 1e9
                        self.eval_count = chunk.get("eval_count", 0)
                        self.eval_duration = chunk.get("eval_duration", 0) / 1e9

        if first_token_time is not None:
            self.ttft = first_token_time - start_time

        full_text = "".join(content_parts)
        # Also include thinking content — Ornith may put code in thinking field
        # when it does not emit the </think> separator
        if thinking_parts:
            thinking_text = "".join(thinking_parts)
            # If content is empty, use thinking directly
            if not full_text.strip():
                full_text = thinking_text
            else:
                full_text = thinking_text + "\n" + full_text
        return self._extract_code(full_text)

    @staticmethod
    def _extract_code(text: str) -> str:
        """
        Strip thinking blocks and extract the LAST code block from model output.

        Steps:
        1. Strip <thinking>...</thinking> blocks
        2. Strip  thinking ...  response markers
        3. Find the last ```python or ``` fenced code block
        4. Return code content (or full stripped text if no code block)
        """
        if not text:
            return ""

        # Strip <thinking>...</thinking> (Qwen/Ornith reasoning format)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = re.sub(r'<response>', '', text)
        text = re.sub(r'</response>', '', text)
        # Also strip  thinking ...  response markers (alternative format)
        text = re.sub(r'  thinking[^<]*?  response', '', text, flags=re.DOTALL)

        # Normalize line endings
        text = text.replace('\r\n', '\n')

        # Find the LAST fenced code block
        code_blocks = re.findall(r'```(\w+)?\s*\n(.*?)\n\s*```', text, flags=re.DOTALL)

        if code_blocks:
            # Take the last block
            lang, code = code_blocks[-1]
            return code.strip()

        # Fallback: return the full stripped text
        return text.strip()


# ─── Mock Pass/Fail Code for Each Level ──────────────────────────────────────

def _make_pass_level1() -> str:
    """Level 1: parse_malformed_json — working implementation."""
    return """import json
import re


def parse_malformed_json(json_str: str, keys: list[str]) -> dict:
    # Replace single quotes with double quotes (but not already double-quoted)
    s = re.sub(r"(?<!\\\\)'(?=(?:[^'\\\\]|\\\\.)*')", '"', json_str)
    # Add quotes around bare keys (word chars before colon)
    s = re.sub(r'(\\s*)(\\w+)(\\s*):', r'\\1"\\2"\\3:', s)
    # Remove trailing commas before closing braces/brackets
    s = re.sub(r',(\\s*[}\\]])', r'\\1', s)
    data = json.loads(s)
    result = {}
    for key in keys:
        parts = key.split('.')
        val = data
        try:
            for p in parts:
                val = val[p]
            result[key] = val
        except (KeyError, TypeError, IndexError):
            pass
    return result
"""


def _make_fail_level1() -> str:
    """Level 1: parse_malformed_json — always fails."""
    return """import json
import re


def parse_malformed_json(json_str: str, keys: list[str]) -> dict:
    raise NotImplementedError("Mock fail for level 1")
"""


def _make_pass_level2() -> str:
    """Level 2: sanitize_and_respond — working implementation."""
    return """import re


def sanitize_and_respond(param: str) -> tuple:
    # Strip HTML tags
    sanitized = re.sub(r'<[^>]+>', '', param)
    sanitized = sanitized.strip()
    if not sanitized:
        return (400, {"error": "Empty parameter"})
    # Check for non-alphanumeric (except whitespace)
    remaining = re.sub(r'\\s+', '', sanitized)
    if not remaining.isalnum():
        return (400, {"error": "Invalid parameter"})
    return (200, {"message": f"Hello, {sanitized}!", "param": sanitized})
"""


def _make_fail_level2() -> str:
    """Level 2: sanitize_and_respond — always fails."""
    return """import re


def sanitize_and_respond(param: str) -> tuple:
    raise NotImplementedError("Mock fail for level 2")
"""


def _make_pass_level3() -> str:
    """Level 3: create_schema_and_query — working implementation."""
    return """import sqlite3


def create_schema_and_query(db_path: str) -> list:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create tables
    c.execute("CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    c.execute("CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, author_id INTEGER REFERENCES authors(id), year INTEGER)")
    # Insert authors
    c.execute("INSERT INTO authors (name) VALUES ('J.K. Rowling')")
    c.execute("INSERT INTO authors (name) VALUES ('George R.R. Martin')")
    c.execute("INSERT INTO authors (name) VALUES ('Terry Pratchett')")
    # Insert books
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('Harry Potter and the Philosopher\\'s Stone', 1, 1997)")
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('Harry Potter and the Chamber of Secrets', 1, 1998)")
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('A Game of Thrones', 2, 1996)")
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('A Clash of Kings', 2, 1998)")
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('Mort', 3, 1987)")
    c.execute("INSERT INTO books (title, author_id, year) VALUES ('Guards! Guards!', 3, 1989)")
    conn.commit()
    # JOIN query
    c.execute("SELECT books.title, authors.name, books.year FROM books JOIN authors ON books.author_id = authors.id")
    rows = c.fetchall()
    conn.close()
    return rows
"""


def _make_fail_level3() -> str:
    """Level 3: create_schema_and_query — always fails."""
    return """import sqlite3


def create_schema_and_query(db_path: str) -> list:
    raise NotImplementedError("Mock fail for level 3")
"""


def _make_pass_level4() -> str:
    """Level 4: fetch_with_retry — working async implementation."""
    return """import asyncio


async def fetch_with_retry(fetch_func, max_retries: int = 3) -> dict:
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await fetch_func()
        except Exception as e:
            last_exc = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    raise last_exc
"""


def _make_fail_level4() -> str:
    """Level 4: fetch_with_retry — always fails."""
    return """import asyncio


async def fetch_with_retry(fetch_func, max_retries: int = 3) -> dict:
    raise NotImplementedError("Mock fail for level 4")
"""


def _make_pass_level5() -> str:
    """Level 5: validate_jwt — working implementation."""
    return """import jwt
import time


def validate_jwt(token: str, secret: str = "secret") -> tuple:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return (200, {"user": payload["sub"]})
    except jwt.ExpiredSignatureError:
        return (403, {"error": "Token expired"})
    except jwt.PyJWTError:
        return (401, {"error": "Invalid signature"})
"""


def _make_fail_level5() -> str:
    """Level 5: validate_jwt — always fails."""
    return """import jwt


def validate_jwt(token: str, secret: str = "secret") -> tuple:
    raise NotImplementedError("Mock fail for level 5")
"""


def _make_pass_level6() -> str:
    """Level 6: manage_session — working implementation."""
    return """import json


def manage_session(redis_client, user_id: str, new_session_data: dict = None) -> dict:
    key = f"session:{user_id}"
    if new_session_data is not None:
        redis_client.set(key, json.dumps(new_session_data), ex=300)
        return {"user_id": user_id, "data": new_session_data, "cached": False}
    raw = redis_client.get(key)
    if raw is not None:
        return {"user_id": user_id, "data": json.loads(raw), "cached": True}
    return {"user_id": user_id, "data": None, "cached": False}
"""


def _make_fail_level6() -> str:
    """Level 6: manage_session — always fails."""
    return """import json


def manage_session(redis_client, user_id: str, new_session_data: dict = None) -> dict:
    raise NotImplementedError("Mock fail for level 6")
"""


def _make_pass_level7() -> str:
    """Level 7: ThreadSafeQueue — working implementation."""
    return """import threading
import queue
from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    item: Any
    worker_id: int


class ThreadSafeQueue:
    def __init__(self):
        self._queue = queue.Queue()
        self._lock = threading.Lock()

    def add_item(self, item: Any) -> None:
        self._queue.put(item)

    def _process(self, item: Any) -> Any:
        return item

    def process_all(self, num_workers: int = 4) -> list[Result]:
        results = []
        results_lock = threading.Lock()

        def worker(worker_id):
            while True:
                try:
                    item = self._queue.get_nowait()
                except queue.Empty:
                    break
                processed = self._process(item)
                with results_lock:
                    results.append(Result(item=processed, worker_id=worker_id))
                self._queue.task_done()

        threads = []
        for i in range(num_workers):
            t = threading.Thread(target=worker, args=(i,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return results
"""


def _make_fail_level7() -> str:
    """Level 7: ThreadSafeQueue — always fails."""
    return """import threading
import queue
from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    item: Any
    worker_id: int


class ThreadSafeQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def add_item(self, item: Any) -> None:
        self._queue.put(item)

    def _process(self, item: Any) -> Any:
        return item

    def process_all(self, num_workers: int = 4) -> list[Result]:
        raise NotImplementedError("Mock fail for level 7")
"""


def _make_pass_level8() -> str:
    """Level 8: distributed_lock and release_lock — working implementation."""
    # Use a non-triple-quoted approach for the Lua script to avoid nesting issues
    lua_script = (
        'if redis.call("GET", KEYS[1]) == ARGV[1] then\n'
        '    redis.call("DEL", KEYS[1])\n'
        '    return 1\n'
        'else\n'
        '    return 0\n'
        'end\n'
    )
    return (
        'import os\n'
        '\n'
        '\n'
        'DISTRIBUTED_LOCK_SCRIPT = """\n'
        + lua_script +
        '"""\n'
        '\n'
        '\n'
        'def distributed_lock(redis_client, lock_name: str, timeout: int = 10) -> bool:\n'
        '    value = os.urandom(16).hex()\n'
        '    result = redis_client.set(lock_name, value, nx=True, ex=timeout)\n'
        '    if result:\n'
        '        distributed_lock._last_value = value\n'
        '        return True\n'
        '    return False\n'
        '\n'
        '\n'
        'def release_lock(redis_client, lock_name: str, lock_value: str) -> bool:\n'
        '    try:\n'
        '        result = redis_client.eval(DISTRIBUTED_LOCK_SCRIPT, 1, lock_name, lock_value)\n'
        '        return bool(result)\n'
        '    except Exception:\n'
        '        # Fallback for fakeredis that may not support eval\n'
        '        current = redis_client.get(lock_name)\n'
        '        if current is not None and current == lock_value:\n'
        '            redis_client.delete(lock_name)\n'
        '            return True\n'
        '        return False\n'
    )


def _make_fail_level8() -> str:
    """Level 8: distributed_lock and release_lock — always fails."""
    return """import os


def distributed_lock(redis_client, lock_name: str, timeout: int = 10) -> bool:
    raise NotImplementedError("Mock fail for level 8")


def release_lock(redis_client, lock_name: str, lock_value: str) -> bool:
    raise NotImplementedError("Mock fail for level 8")
"""


def _make_pass_level9() -> str:
    """Level 9: encode_frame and decode_frame — working implementation."""
    return """import os
import struct


def encode_frame(payload: bytes, opcode: int = 1) -> bytes:
    frame = bytearray()
    # FIN bit (1) | RSV (000) | Opcode (4 bits)
    first_byte = 0x80 | opcode
    frame.append(first_byte)
    # Masked (1) | Payload length
    length = len(payload)
    if length < 126:
        frame.append(0x80 | length)
    elif length < 65536:
        frame.append(0x80 | 126)
        frame.extend(struct.pack(">H", length))
    else:
        frame.append(0x80 | 127)
        frame.extend(struct.pack(">Q", length))
    # Masking key (4 random bytes)
    mask = os.urandom(4)
    frame.extend(mask)
    # Masked payload
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    frame.extend(masked)
    return bytes(frame)


def decode_frame(data: bytes) -> dict:
    first_byte = data[0]
    fin = (first_byte >> 7) & 1
    opcode = first_byte & 0x0F
    second_byte = data[1]
    masked = (second_byte >> 7) & 1
    length = second_byte & 0x7F
    offset = 2
    if length == 126:
        length = struct.unpack(">H", data[2:4])[0]
        offset = 4
    elif length == 127:
        length = struct.unpack(">Q", data[2:10])[0]
        offset = 10
    mask = None
    if masked:
        mask = data[offset:offset + 4]
        offset += 4
    payload = data[offset:offset + length]
    if mask:
        payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
    return {
        "fin": fin,
        "opcode": opcode,
        "masked": masked,
        "payload_length": length,
        "mask": list(mask) if mask else None,
        "payload": payload,
    }
"""


def _make_fail_level9() -> str:
    """Level 9: encode_frame and decode_frame — always fails."""
    return """import os
import struct


def encode_frame(payload: bytes, opcode: int = 1) -> bytes:
    raise NotImplementedError("Mock fail for level 9")


def decode_frame(data: bytes) -> dict:
    raise NotImplementedError("Mock fail for level 9")
"""


def _make_pass_level10() -> str:
    """Level 10: StateMachine and process_events — working implementation."""
    return """class StateMachine:
    def __init__(self, initial_state: str = "idle"):
        self._state = initial_state
        self._transitions = {
            ("idle", "start"): "processing",
            ("processing", "complete"): "completed",
            ("processing", "fail"): "failed",
            ("completed", "reset"): "idle",
            ("failed", "reset"): "idle",
        }
        # Also allow "reset" from any state
        self._reset_states = {"idle", "processing", "completed", "failed"}
        self._log = []

    @property
    def state(self) -> str:
        return self._state

    def transition(self, event: str) -> str:
        if event == "reset":
            self._state = "idle"
            if len(self._log) < 1000:
                self._log.append((event, self._state))
            return self._state
        key = (self._state, event)
        if key in self._transitions:
            self._state = self._transitions[key]
            if len(self._log) < 1000:
                self._log.append((event, self._state))
            return self._state
        raise ValueError(f"Invalid event '{event}' for state '{self._state}'")


def process_events(events: list[str], initial_state: str = "idle") -> list[str]:
    sm = StateMachine(initial_state)
    states = [sm.state]
    for event in events:
        sm.transition(event)
        states.append(sm.state)
    return states
"""


def _make_fail_level10() -> str:
    """Level 10: StateMachine and process_events — always fails."""
    return """class StateMachine:
    def __init__(self, initial_state: str = "idle"):
        raise NotImplementedError("Mock fail for level 10")


def process_events(events: list[str], initial_state: str = "idle") -> list[str]:
    raise NotImplementedError("Mock fail for level 10")
"""


def _make_pass_level11() -> str:
    """Level 11: Consistent Hash Ring — working implementation."""
    return """def create_ring() -> dict:
    return {"nodes": [], "vnodes": {}}


def add_node(ring: dict, node_id: str, vnodes: int = 9) -> dict:
    suffixes = [f":v{i}" for i in range(vnodes)]
    ring["vnodes"][node_id] = suffixes
    for suffix in suffixes:
        vnode_key = f"{node_id}{suffix}"
        pos = hash(vnode_key)
        ring["nodes"].append((pos, node_id))
    ring["nodes"].sort(key=lambda x: x[0])
    return ring


def remove_node(ring: dict, node_id: str) -> dict:
    ring["nodes"] = [(pos, nid) for pos, nid in ring["nodes"] if nid != node_id]
    if node_id in ring["vnodes"]:
        del ring["vnodes"][node_id]
    return ring


def lookup(ring: dict, key: str) -> str:
    if not ring["nodes"]:
        return ""
    target = hash(key)
    nodes = ring["nodes"]
    lo, hi = 0, len(nodes)
    while lo < hi:
        mid = (lo + hi) // 2
        if nodes[mid][0] < target:
            lo = mid + 1
        else:
            hi = mid
    if lo < len(nodes):
        return nodes[lo][1]
    return nodes[0][1]
"""


def _make_fail_level11() -> str:
    """Level 11: Consistent Hash Ring — always fails."""
    return """def create_ring() -> dict:
    return {"nodes": [], "vnodes": {}}


def add_node(ring: dict, node_id: str, vnodes: int = 9) -> dict:
    raise NotImplementedError("Mock fail for level 11")


def remove_node(ring: dict, node_id: str) -> dict:
    raise NotImplementedError("Mock fail for level 11")


def lookup(ring: dict, key: str) -> str:
    raise NotImplementedError("Mock fail for level 11")
"""


def _make_pass_level12() -> str:
    """Level 12: Event Sourcing Aggregate — working implementation."""
    return """class EventStore:
    def __init__(self):
        self._events = {}

    def append(self, aggregate_id: str, event: dict) -> None:
        if aggregate_id not in self._events:
            self._events[aggregate_id] = []
        self._events[aggregate_id].append(event)

    def get_events(self, aggregate_id: str) -> list:
        return self._events.get(aggregate_id, [])


class OrderAggregate:
    def __init__(self, id: str, event_store: EventStore):
        self._id = id
        self._event_store = event_store

    def create_order(self, customer: str, items: list) -> dict:
        self._event_store.append(self._id, {"type": "OrderCreated", "customer": customer, "items": items})
        return self.get_state()

    def add_item(self, item: str) -> dict:
        state = self.get_state()
        if state["status"] == "cancelled":
            raise ValueError("Order already cancelled")
        self._event_store.append(self._id, {"type": "ItemAdded", "item": item})
        return self.get_state()

    def remove_item(self, item_id: str) -> dict:
        state = self.get_state()
        if state["status"] == "cancelled":
            raise ValueError("Order already cancelled")
        self._event_store.append(self._id, {"type": "ItemRemoved", "item_id": item_id})
        return self.get_state()

    def cancel(self) -> dict:
        state = self.get_state()
        if state["status"] == "cancelled":
            raise ValueError("Order already cancelled")
        self._event_store.append(self._id, {"type": "OrderCancelled"})
        return self.get_state()

    def get_state(self) -> dict:
        events = self._event_store.get_events(self._id)
        state = {"id": self._id, "customer": "", "items": [], "status": "active", "total": 0.0}
        for event in events:
            if event["type"] == "OrderCreated":
                state["customer"] = event["customer"]
                state["items"] = list(event["items"])
                state["total"] = len(event["items"]) * 10.0
            elif event["type"] == "ItemAdded":
                state["items"].append(event["item"])
                state["total"] += 10.0
            elif event["type"] == "ItemRemoved":
                item_id = event["item_id"]
                for i, item in enumerate(state["items"]):
                    if item_id in item:
                        state["items"].pop(i)
                        break
                state["total"] -= 10.0
            elif event["type"] == "OrderCancelled":
                state["status"] = "cancelled"
        return state


def process_command(event_store: EventStore, aggregate_id: str, command: dict) -> dict:
    agg = OrderAggregate(aggregate_id, event_store)
    cmd_type = command["type"]
    if cmd_type == "create_order":
        return agg.create_order(command["customer"], command["items"])
    elif cmd_type == "add_item":
        return agg.add_item(command["item"])
    elif cmd_type == "remove_item":
        return agg.remove_item(command["item_id"])
    elif cmd_type == "cancel":
        return agg.cancel()
    raise ValueError(f"Unknown command type: {cmd_type}")
"""


def _make_fail_level12() -> str:
    """Level 12: Event Sourcing Aggregate — always fails."""
    return """class EventStore:
    def __init__(self):
        raise NotImplementedError("Mock fail for level 12")

    def append(self, aggregate_id: str, event: dict) -> None:
        pass

    def get_events(self, aggregate_id: str) -> list:
        return []


class OrderAggregate:
    def __init__(self, id: str, event_store: EventStore):
        raise NotImplementedError("Mock fail for level 12")


def process_command(event_store: EventStore, aggregate_id: str, command: dict) -> dict:
    raise NotImplementedError("Mock fail for level 12")
"""


def _make_pass_level13() -> str:
    """Level 13: Circuit Breaker — working implementation."""
    return """import time


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0,
                 exceptions: tuple = (Exception,)):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._exceptions = exceptions
        self._state = "CLOSED"
        self._failure_count = 0
        self._open_time = 0.0

    def call(self, func, *args, **kwargs):
        if self._state == "CLOSED":
            try:
                result = func(*args, **kwargs)
                self._failure_count = 0
                return result
            except self._exceptions:
                self._failure_count += 1
                if self._failure_count >= self._failure_threshold:
                    self._state = "OPEN"
                    self._open_time = time.monotonic()
                raise

        if self._state == "OPEN":
            if time.monotonic() - self._open_time >= self._recovery_timeout:
                self._state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._state = "CLOSED"
            self._failure_count = 0
            return result
        except self._exceptions:
            self._state = "OPEN"
            self._open_time = time.monotonic()
            raise

    def reset(self) -> None:
        self._state = "CLOSED"
        self._failure_count = 0

    def get_state(self) -> str:
        return self._state
"""


def _make_fail_level13() -> str:
    """Level 13: Circuit Breaker — always fails."""
    return """import time


class CircuitBreakerOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0,
                 exceptions: tuple = (Exception,)):
        raise NotImplementedError("Mock fail for level 13")

    def call(self, func, *args, **kwargs):
        raise NotImplementedError("Mock fail for level 13")

    def reset(self) -> None:
        raise NotImplementedError("Mock fail for level 13")

    def get_state(self) -> str:
        return "OPEN"
"""


def _make_pass_level14() -> str:
    """Level 14: Token Bucket Rate Limiter — working implementation."""
    return """import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float, refill_interval: float = 1.0):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._refill_interval = refill_interval
        self._tokens = capacity
        self._last_refill = time.monotonic()

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        intervals = int(elapsed / self._refill_interval)
        if intervals > 0:
            self._tokens = min(self._capacity, self._tokens + intervals * self._refill_rate)
            self._last_refill += intervals * self._refill_interval

    def allow_request(self, tokens: float = 1.0) -> bool:
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    def get_wait_time(self, tokens: float = 1.0) -> float:
        self._refill()
        if self._tokens >= tokens:
            return 0.0
        shortfall = tokens - self._tokens
        intervals_needed = -(-int(shortfall) // int(self._refill_rate)) if self._refill_rate > 0 else 1
        return intervals_needed * self._refill_interval

    def get_tokens(self) -> float:
        self._refill()
        return self._tokens
"""


def _make_fail_level14() -> str:
    """Level 14: Token Bucket Rate Limiter — always fails."""
    return """import time


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float, refill_interval: float = 1.0):
        raise NotImplementedError("Mock fail for level 14")

    def allow_request(self, tokens: float = 1.0) -> bool:
        raise NotImplementedError("Mock fail for level 14")

    def get_wait_time(self, tokens: float = 1.0) -> float:
        raise NotImplementedError("Mock fail for level 14")

    def get_tokens(self) -> float:
        raise NotImplementedError("Mock fail for level 14")
"""


def _make_pass_level15() -> str:
    """Level 15: Dependency Resolution Engine — working implementation."""
    return """from collections import deque


def topological_sort(dependencies: dict[str, list[str]]) -> list[list[str]]:
    in_degree = {}
    adj = {}

    for task in dependencies:
        in_degree[task] = 0
        adj[task] = []

    for task, deps in dependencies.items():
        in_degree[task] = len(deps)
        for dep in deps:
            if dep not in adj:
                adj[dep] = []
            adj[dep].append(task)

    queue = deque([t for t, d in in_degree.items() if d == 0])
    result = []
    processed = 0

    while queue:
        level = []
        for _ in range(len(queue)):
            task = queue.popleft()
            level.append(task)
            processed += 1
            for depender in adj.get(task, []):
                in_degree[depender] -= 1
                if in_degree[depender] == 0:
                    queue.append(depender)
        result.append(level)

    if processed != len(in_degree):
        raise ValueError("Cycle detected in dependencies")

    return result


def resolve_critical_path(graph: dict[str, dict]) -> dict[str, int]:
    deps = {task: data["deps"] for task, data in graph.items()}
    topo_levels = topological_sort(deps)
    order = [t for level in topo_levels for t in level]

    finish = {}
    for task in order:
        data = graph[task]
        if not data["deps"]:
            finish[task] = data["duration"]
        else:
            finish[task] = max(finish[d] for d in data["deps"]) + data["duration"]

    return finish
"""


def _make_fail_level15() -> str:
    """Level 15: Dependency Resolution Engine — always fails."""
    return """from collections import deque


def topological_sort(dependencies: dict[str, list[str]]) -> list[list[str]]:
    raise NotImplementedError("Mock fail for level 15")


def resolve_critical_path(graph: dict[str, dict]) -> dict[str, int]:
    raise NotImplementedError("Mock fail for level 15")
"""


# Map level -> (pass_code_func, fail_code_func)
MOCK_CODE_GENERATORS = {
    1: (_make_pass_level1, _make_fail_level1),
    2: (_make_pass_level2, _make_fail_level2),
    3: (_make_pass_level3, _make_fail_level3),
    4: (_make_pass_level4, _make_fail_level4),
    5: (_make_pass_level5, _make_fail_level5),
    6: (_make_pass_level6, _make_fail_level6),
    7: (_make_pass_level7, _make_fail_level7),
    8: (_make_pass_level8, _make_fail_level8),
    9: (_make_pass_level9, _make_fail_level9),
    10: (_make_pass_level10, _make_fail_level10),
    11: (_make_pass_level11, _make_fail_level11),
    12: (_make_pass_level12, _make_fail_level12),
    13: (_make_pass_level13, _make_fail_level13),
    14: (_make_pass_level14, _make_fail_level14),
    15: (_make_pass_level15, _make_fail_level15),
}


class MockStreamClient:
    """
    Mock client for testing binary search logic without a real Ollama model.

    Modes:
      - all_pass: returns code that passes all tests
      - all_fail: returns code that fails all tests
      - start_pass_then_fail: returns passing code for levels 1-5, failing for 6-10
      - per-level override: pass a dict like {1: 'pass', 2: 'fail', ...}
    """

    def __init__(self, mode: str = "all_pass", level_overrides: dict = None):
        self.mode = mode
        self.level_overrides = level_overrides or {}
        self.ttft = 0.05
        self.total_duration = 0.5
        self.prompt_eval_count = 100
        self.prompt_eval_duration = 0.2
        self.eval_count = 50
        self.eval_duration = 0.3

    @property
    def prompt_eval_speed(self) -> float:
        if self.prompt_eval_duration > 0:
            return self.prompt_eval_count / self.prompt_eval_duration
        return 0.0

    @property
    def eval_speed(self) -> float:
        if self.eval_duration > 0:
            return self.eval_count / self.eval_duration
        return 0.0

    def generate(self, prompt: str, level: int,
                 model_name: str = DEFAULT_MODEL) -> str:
        """Generate mock code that either passes or fails based on mode/overrides."""

        # Check per-level override first
        if level in self.level_overrides:
            should_pass = self.level_overrides[level] == "pass"
        elif self.mode == "all_pass":
            should_pass = True
        elif self.mode == "all_fail":
            should_pass = False
        elif self.mode == "start_pass_then_fail":
            should_pass = level <= 5
        else:
            should_pass = True

        # Get the code generator for this level
        pass_gen, fail_gen = MOCK_CODE_GENERATORS.get(level, (None, None))
        if should_pass and pass_gen:
            return pass_gen()
        elif not should_pass and fail_gen:
            return fail_gen()
        else:
            # Fallback (should not happen given all 10 levels are mapped)
            if should_pass:
                return "# Mock pass\n"
            else:
                return "# Mock fail\n"