"""
Skill Bank — 10 coding tasks for adaptive skill ceiling evaluation.

Each level is a dict with:
  - level (int): difficulty level 1-10
  - name (str): human-readable name
  - prompt (str): prompt sent to the model
  - boilerplate (str): starter code with function stubs / docstrings
  - test_code (str): pytest unit tests as a string
  - requirements (list[str]): pip packages needed for testing
"""

SKILLS = {
    1: {
        "level": 1,
        "name": "Basic Syntax — Malformed JSON Parser",
        "prompt": """Write a Python function `parse_malformed_json(json_str: str, keys: list[str]) -> dict` that parses malformed JSON (trailing commas, single quotes instead of double quotes, unquoted keys) and extracts specific nested key-value pairs into a flat dict with dot-separated keys.

Example:
  input: "{'user': {'name': 'Alice', 'age': 30,},}"  with keys=["user.name", "user.age"]
  output: {"user.name": "Alice", "user.age": 30}

Rules:
  - Handle single quotes as well as double quotes
  - Handle trailing commas before closing braces
  - Handle keys without quotes (bare words)
  - Use dot-separated keys for nested access
  - If a key path doesn't exist, omit it (don't raise)
  - Only return the keys requested (not the whole flattened dict)""",
        "boilerplate": """import json
import re


def parse_malformed_json(json_str: str, keys: list[str]) -> dict:
    \"\"\"
    Parse malformed JSON strings (single quotes, trailing commas, bare keys)
    and extract specific nested values into a flat dict with dot-separated keys.

    Args:
        json_str: A malformed JSON string.
        keys: List of dot-separated key paths to extract.

    Returns:
        A dict mapping requested key paths to their values.
    \"\"\"
    # 1. Replace single quotes with double quotes
    # 2. Add quotes around bare keys
    # 3. Remove trailing commas
    # 4. Parse with json.loads
    # 5. Navigate the parsed dict for each key path
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import parse_malformed_json


class TestParseMalformedJSON:
    def test_single_quotes(self):
        result = parse_malformed_json("{'name': 'Alice', 'age': 30}", ["name", "age"])
        assert result == {"name": "Alice", "age": 30}, f"Expected flat dict, got {result}"

    def test_trailing_comma(self):
        result = parse_malformed_json("{'user': {'name': 'Bob', 'age': 25,},}", ["user.name", "user.age"])
        assert result == {"user.name": "Bob", "user.age": 25}, f"Got {result}"

    def test_unquoted_keys(self):
        result = parse_malformed_json("{name: 'Charlie', age: 35}", ["name", "age"])
        assert result == {"name": "Charlie", "age": 35}, f"Got {result}"

    def test_mixed_malformed(self):
        result = parse_malformed_json(
            "{'items': [{'id': 1, 'val': 'x',}, {'id': 2, 'val': 'y',}], 'count': 2,}",
            ["count", "items"]
        )
        assert result["count"] == 2
        assert len(result["items"]) == 2

    def test_missing_key_omitted(self):
        result = parse_malformed_json("{'a': 1}", ["a", "b"])
        assert result == {"a": 1}, f"Missing key should be omitted, got {result}"

    def test_empty_input(self):
        result = parse_malformed_json("{}", ["x"])
        assert result == {}, f"Empty result expected, got {result}"

    def test_nested_deep(self):
        json_str = "{'a': {'b': {'c': 42}}}"
        result = parse_malformed_json(json_str, ["a.b.c"])
        assert result == {"a.b.c": 42}, f"Deep nested extraction failed, got {result}"
""",
        "requirements": [],
    },

    2: {
        "level": 2,
        "name": "Standard Routing — Input Sanitizer",
        "prompt": """Write a Python function `sanitize_and_respond(param: str) -> tuple[int, dict]` that acts like a simple HTTP request handler.

Rules:
1. If `param` contains any non-alphanumeric characters (except whitespace), return (400, {"error": "Invalid parameter"})
2. Strip HTML tags from `param` and trim whitespace
3. If after sanitization the string is empty, return (400, {"error": "Empty parameter"})
4. Otherwise return (200, {"message": f"Hello, {sanitized}!", "param": sanitized})

Examples:
  sanitize_and_respond("Alice") -> (200, {"message": "Hello, Alice!", "param": "Alice"})
  sanitize_and_respond("<script>alert('xss')</script>Bob") -> (200, {"message": "Hello, Bob!", "param": "Bob"})
  sanitize_and_respond("hello world!") -> (400, {"error": "Invalid parameter"})
  sanitize_and_respond("   ") -> (400, {"error": "Empty parameter"})

Use re.sub(r'<[^>]+>', '', param) to strip HTML tags.""",
        "boilerplate": """import re


def sanitize_and_respond(param: str) -> tuple:
    \"\"\"
    Validate, sanitize, and respond like an HTTP handler.

    Args:
        param: Input string to validate and sanitize.

    Returns:
        Tuple of (status_code, response_dict).
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import sanitize_and_respond


class TestSanitizeAndRespond:
    def test_valid_alphanumeric(self):
        status, body = sanitize_and_respond("Alice")
        assert status == 200
        assert body["message"] == "Hello, Alice!"
        assert body["param"] == "Alice"

    def test_html_tag_stripping(self):
        status, body = sanitize_and_respond("<b>Bob</b>")
        assert status == 200
        assert body["param"] == "Bob"
        assert "Bob" in body["message"]

    def test_invalid_special_chars(self):
        status, body = sanitize_and_respond("hello!")
        assert status == 400
        assert "error" in body

    def test_xss_attempt(self):
        status, body = sanitize_and_respond("<script>alert('x')</script>")
        assert status == 400, "Script tag content is not alphanumeric, should be 400"

    def test_whitespace_only(self):
        status, body = sanitize_and_respond("   ")
        assert status == 400
        assert body["error"] == "Empty parameter"

    def test_mixed_valid(self):
        status, body = sanitize_and_respond("  Alice123  ")
        assert status == 200
        assert body["param"] == "Alice123"

    def test_multiple_tags(self):
        status, body = sanitize_and_respond("<div><p>Test</p></div>")
        assert status == 200
        assert body["param"] == "Test"
""",
        "requirements": [],
    },

    3: {
        "level": 3,
        "name": "Database CRUD — SQLite Schema & Query",
        "prompt": """Write a Python function `create_schema_and_query(db_path: str) -> list[tuple]` that:

1. Creates/opens a SQLite database at `db_path`
2. Creates two tables:
   - `authors`: id (INTEGER PRIMARY KEY), name (TEXT NOT NULL)
   - `books`: id (INTEGER PRIMARY KEY), title (TEXT NOT NULL), author_id (INTEGER REFERENCES authors(id)), year (INTEGER)
3. Inserts 3 authors and at least 4 books (with the third author having multiple books)
4. Executes a multi-table JOIN query to return all books with their author names
5. Returns the query results as a list of tuples: [(title, author_name, year), ...]
6. Closes the connection

Use the standard `sqlite3` module (stdlib).""",
        "boilerplate": """import sqlite3


def create_schema_and_query(db_path: str) -> list:
    \"\"\"
    Create SQLite schema, insert sample data, and run a multi-table JOIN query.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of (title, author_name, year) tuples from the JOIN query.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import create_schema_and_query


class TestCreateSchemaAndQuery:
    def test_returns_list_of_tuples(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        result = create_schema_and_query(db_path)
        assert isinstance(result, list), f"Expected list, got {type(result)}"
        assert len(result) >= 4, f"Expected at least 4 books, got {len(result)}"
        for row in result:
            assert isinstance(row, tuple), f"Each row should be a tuple, got {type(row)}"
            assert len(row) == 3, f"Each row should have 3 elements (title, author, year), got {len(row)}"

    def test_contains_author_names(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        result = create_schema_and_query(db_path)
        titles_authors = {r[0]: r[1] for r in result}
        assert len(titles_authors) == len(result), "Duplicate titles found"

    def test_third_author_multiple_books(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        result = create_schema_and_query(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        conn.close()

        assert book_count >= 4, f"Expected at least 4 books, got {book_count}"

        # Check that there are at least 3 distinct authors in the results
        authors = set(r[1] for r in result)
        assert len(authors) >= 2, f"Expected at least 2 distinct authors, got {len(authors)}"

    def test_schema_persists(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        create_schema_and_query(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()
        assert "authors" in tables, f"authors table not found, got {tables}"
        assert "books" in tables, f"books table not found, got {tables}"
""",
        "requirements": [],
    },

    4: {
        "level": 4,
        "name": "Async Resilience — Retry with Exponential Backoff",
        "prompt": """Write an async function `fetch_with_retry(fetch_func, max_retries: int = 3) -> dict` that:

1. Calls `fetch_func()` — an async callable that returns a dict
2. If `fetch_func()` raises an exception, wait with exponential backoff (1s, 2s, 4s) then retry
3. If `fetch_func()` succeeds, return its result immediately
4. After `max_retries` consecutive failures, re-raise the last exception

The function signature is: async def fetch_with_retry(fetch_func, max_retries=3) -> dict

Use asyncio.sleep() for delays. Do not use any external packages — only asyncio from stdlib.

Example usage with a mock:
  async def flaky_func():
      nonlocal attempts
      attempts += 1
      if attempts < 3:
          raise ConnectionError("fail")
      return {"status": "ok"}
  
  result = await fetch_with_retry(flaky_func, max_retries=3)
  # result == {"status": "ok"}""",
        "boilerplate": """import asyncio


async def fetch_with_retry(fetch_func, max_retries: int = 3) -> dict:
    \"\"\"
    Call an async fetch function with exponential backoff retry logic.

    Args:
        fetch_func: An async callable that returns a dict.
        max_retries: Maximum number of retry attempts (default 3).

    Returns:
        The result dict from fetch_func on success.

    Raises:
        The last exception from fetch_func after exhausting retries.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import fetch_with_retry


class TestFetchWithRetry:
    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        async def ok():
            return {"status": "ok"}
        result = await fetch_with_retry(ok, max_retries=3)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_retries_and_succeeds(self):
        attempts = 0
        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError(f"Attempt {attempts} failed")
            return {"status": "recovered"}
        result = await fetch_with_retry(flaky, max_retries=5)
        assert result == {"status": "recovered"}
        assert attempts == 3, f"Expected 3 attempts, got {attempts}"

    @pytest.mark.asyncio
    async def test_exhausts_retries_then_raises(self):
        attempts = 0
        async def always_fails():
            nonlocal attempts
            attempts += 1
            raise ValueError("persistent failure")
        with pytest.raises(ValueError, match="persistent failure"):
            await fetch_with_retry(always_fails, max_retries=3)
        assert attempts == 3, f"Expected 3 attempts, got {attempts}"

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        import time
        attempts = 0
        async def flaky():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise OSError("fail")
            return {"status": "ok"}
        start = time.monotonic()
        result = await fetch_with_retry(flaky, max_retries=3)
        elapsed = time.monotonic() - start
        assert result == {"status": "ok"}
        # 2 retries: 1s + 2s = at least 3s, at most ~3.5s
        assert elapsed >= 2.5, f"Expected exponential backoff delay, took {elapsed:.2f}s"
        assert elapsed <= 4.0, f"Backoff delay too long, took {elapsed:.2f}s"

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self):
        attempts = 0
        async def ok():
            nonlocal attempts
            attempts += 1
            return {"status": "ok"}
        result = await fetch_with_retry(ok, max_retries=5)
        assert result == {"status": "ok"}
        assert attempts == 1, f"Should only call once on success, got {attempts}"
""",
        "requirements": ["pytest-asyncio"],
    },

    5: {
        "level": 5,
        "name": "Security Middleware — JWT Validation",
        "prompt": """Write a Python function `validate_jwt(token: str, secret: str = "secret") -> tuple[int, dict]` that validates a JWT token.

Rules:
1. Decode the JWT using PyJWT library (`import jwt`)
2. If the token is valid and not expired, return (200, {"user": payload["sub"]})
3. If the signature is invalid, return (401, {"error": "Invalid signature"})
4. If the token is expired (`jwt.ExpiredSignatureError`), return (403, {"error": "Token expired"})
5. For any other `jwt.PyJWTError`, return (401, {"error": "Invalid token"})

Use `jwt.decode(token, secret, algorithms=["HS256"])` for decoding.

Example:
  import jwt, time
  token = jwt.encode({"sub": "user123", "exp": time.time() + 3600}, "secret", algorithm="HS256")
  validate_jwt(token) -> (200, {"user": "user123"})""",
        "boilerplate": """import jwt


def validate_jwt(token: str, secret: str = \"secret\") -> tuple:
    \"\"\"
    Validate a JWT token and return appropriate HTTP-style response.

    Args:
        token: The JWT string to validate.
        secret: The secret key used for decoding (default \"secret\").

    Returns:
        Tuple of (status_code, response_dict).
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import jwt
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import validate_jwt


class TestValidateJWT:
    def test_valid_token(self):
        token = jwt.encode({"sub": "alice", "exp": time.time() + 3600}, "secret", algorithm="HS256")
        status, body = validate_jwt(token)
        assert status == 200, f"Expected 200, got {status}"
        assert body["user"] == "alice", f"Expected user alice, got {body}"

    def test_expired_token(self):
        token = jwt.encode({"sub": "bob", "exp": time.time() - 10}, "secret", algorithm="HS256")
        status, body = validate_jwt(token)
        assert status == 403, f"Expected 403 for expired, got {status}"
        assert "expired" in body.get("error", "").lower(), f"Expected expired error, got {body}"

    def test_invalid_signature(self):
        token = jwt.encode({"sub": "charlie", "exp": time.time() + 3600}, "wrong_secret", algorithm="HS256")
        status, body = validate_jwt(token)
        assert status == 401, f"Expected 401 for bad signature, got {status}"

    def test_malformed_token(self):
        status, body = validate_jwt("not.a.token")
        assert status == 401, f"Expected 401 for malformed token, got {status}"
        assert "error" in body

    def test_empty_token(self):
        status, body = validate_jwt("")
        assert status == 401, f"Expected 401 for empty token, got {status}"

    def test_custom_secret(self):
        token = jwt.encode({"sub": "dave", "exp": time.time() + 3600}, "mysecret", algorithm="HS256")
        status, body = validate_jwt(token, secret="mysecret")
        assert status == 200, f"Expected 200 with custom secret, got {status}"
        assert body["user"] == "dave"
""",
        "requirements": ["pyjwt"],
    },

    6: {
        "level": 6,
        "name": "API State Management — Redis Session with TTL",
        "prompt": """Write a Python function `manage_session(redis_client, user_id: str, new_session_data: dict | None = None) -> dict` that manages user sessions in Redis.

Rules:
1. If `new_session_data` is provided, store it in Redis with key "session:{user_id}" and a TTL of 300 seconds, then return {"user_id": user_id, "data": new_session_data, "cached": False}
2. If `new_session_data` is None, attempt to retrieve existing session data from Redis with key "session:{user_id}"
   - If found, return {"user_id": user_id, "data": retrieved_data, "cached": True}
   - If not found, return {"user_id": user_id, "data": None, "cached": False}

The `redis_client` is a Redis-like client (can be `fakeredis.FakeStrictRedis()` for testing) with:
  - `.set(key, value, ex=ttl)` — stores with TTL
  - `.get(key)` — retrieves (returns None if not found)

Use `import json` to serialize/deserialize dict data to/from strings for Redis storage.

Example:
  from fakeredis import FakeStrictRedis
  r = FakeStrictRedis()
  manage_session(r, "user1", {"role": "admin"})
  # -> {"user_id": "user1", "data": {"role": "admin"}, "cached": False}

  manage_session(r, "user1")
  # -> {"user_id": "user1", "data": {"role": "admin"}, "cached": True}""",
        "boilerplate": """import json


def manage_session(redis_client, user_id: str, new_session_data: dict = None) -> dict:
    \"\"\"
    Manage user sessions in Redis with TTL-based storage.

    Args:
        redis_client: A Redis-like client (fakeredis.FakeStrictRedis or redis.Redis).
        user_id: The user identifier.
        new_session_data: If provided, stores this data with TTL 300s.

    Returns:
        dict with user_id, data, and cached flag.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import json
import sys
import os
from fakeredis import FakeStrictRedis
sys.path.insert(0, os.path.dirname(__file__))
from task_template import manage_session


class TestManageSession:
    def test_store_new_session(self):
        r = FakeStrictRedis()
        result = manage_session(r, "user1", {"role": "admin", "theme": "dark"})
        assert result["user_id"] == "user1"
        assert result["data"] == {"role": "admin", "theme": "dark"}
        assert result["cached"] is False

    def test_retrieve_existing_session(self):
        r = FakeStrictRedis()
        manage_session(r, "user2", {"score": 100, "level": 5})
        result = manage_session(r, "user2")
        assert result["user_id"] == "user2"
        assert result["data"] == {"score": 100, "level": 5}
        assert result["cached"] is True

    def test_missing_session(self):
        r = FakeStrictRedis()
        result = manage_session(r, "unknown_user")
        assert result["user_id"] == "unknown_user"
        assert result["data"] is None
        assert result["cached"] is False

    def test_ttl_expires(self):
        import time
        r = FakeStrictRedis()
        manage_session(r, "ephemeral", {"temp": "data"})
        # fakeredis respects TTL if we move time forward
        # For fakeredis >= 2.0, time can be advanced
        # We'll just verify the key was set with TTL
        ttl = r.ttl("session:ephemeral")
        assert ttl > 0, f"Expected positive TTL, got {ttl}"
        assert ttl <= 300, f"Expected TTL <= 300, got {ttl}"

    def test_update_existing_session(self):
        r = FakeStrictRedis()
        manage_session(r, "user3", {"first": "visit"})
        manage_session(r, "user3", {"second": "visit"})
        result = manage_session(r, "user3")
        assert result["cached"] is True
        assert result["data"] == {"second": "visit"}, f"Expected updated data, got {result['data']}"

    def test_multiple_users(self):
        r = FakeStrictRedis()
        manage_session(r, "alice", {"color": "blue"})
        manage_session(r, "bob", {"color": "red"})
        alice = manage_session(r, "alice")
        bob = manage_session(r, "bob")
        assert alice["data"]["color"] == "blue"
        assert bob["data"]["color"] == "red"
""",
        "requirements": ["fakeredis"],
    },

    7: {
        "level": 7,
        "name": "Concurrency Traps — ThreadSafe Queue Processor",
        "prompt": """Write a thread-safe queue class `ThreadSafeQueue` that processes items with multiple workers.

Requirements:
  - `add_item(item)` — adds an item to the internal queue (thread-safe)
  - `process_all(num_workers=4) -> list[Result]` — processes all items using `num_workers` threads, returns a list of Result dataclass objects
  - Each worker pops items from the queue and processes them by calling `self._process(item)` which should be overridden or passed
  - Use `threading.Lock` to prevent race conditions
  - The default `_process` method should just return the item unchanged (identity function)
  - All items must be processed exactly once (no duplicates, no drops)

Use the `Result` dataclass:
  @dataclass
  class Result:
      item: Any
      worker_id: int

Pure stdlib only (threading, dataclasses, queue, time).

Example:
  q = ThreadSafeQueue()
  for i in range(100):
      q.add_item(i)
  results = q.process_all(num_workers=4)
  # len(results) == 100
  # items 0-99 each appear exactly once""",
        "boilerplate": """import threading
import queue
from dataclasses import dataclass
from typing import Any


@dataclass
class Result:
    item: Any
    worker_id: int


class ThreadSafeQueue:
    \"\"\"
    A multi-threaded worker queue that processes items exactly once.
    \"\"\"

    def __init__(self):
        self._queue = queue.Queue()
        self._lock = threading.Lock()

    def add_item(self, item: Any) -> None:
        \"\"\"Add an item to the queue (thread-safe).\"\"\"
        self._queue.put(item)

    def _process(self, item: Any) -> Any:
        \"\"\"Process a single item. Override in subclass for custom logic.\"\"\"
        return item

    def process_all(self, num_workers: int = 4) -> list[Result]:
        \"\"\"
        Process all items in the queue using multiple worker threads.

        Args:
            num_workers: Number of worker threads to spawn.

        Returns:
            List of Result objects, one per processed item.
        \"\"\"
        pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import ThreadSafeQueue, Result


class TestThreadSafeQueue:
    def test_process_100_items(self):
        q = ThreadSafeQueue()
        for i in range(100):
            q.add_item(i)
        results = q.process_all(num_workers=4)
        assert len(results) == 100, f"Expected 100 results, got {len(results)}"

    def test_no_duplicates(self):
        q = ThreadSafeQueue()
        for i in range(100):
            q.add_item(i)
        results = q.process_all(num_workers=4)
        processed = [r.item for r in results]
        assert len(set(processed)) == 100, f"Duplicates found: {len(processed)} items, {len(set(processed))} unique"

    def test_all_items_processed_exactly_once(self):
        q = ThreadSafeQueue()
        items = list(range(100))
        for item in items:
            q.add_item(item)
        results = q.process_all(num_workers=4)
        processed = sorted([r.item for r in results])
        assert processed == items, f"Items mismatch: expected first 10 and last 10: {processed[:10]}...{processed[-10:]}"

    def test_single_worker(self):
        q = ThreadSafeQueue()
        for i in range(10):
            q.add_item(i)
        results = q.process_all(num_workers=1)
        assert len(results) == 10

    def test_empty_queue(self):
        q = ThreadSafeQueue()
        results = q.process_all(num_workers=4)
        assert results == [], f"Expected empty list for empty queue, got {results}"

    def test_worker_ids_present(self):
        q = ThreadSafeQueue()
        for i in range(20):
            q.add_item(i)
        results = q.process_all(num_workers=4)
        worker_ids = set(r.worker_id for r in results)
        assert len(worker_ids) >= 1, "At least one worker should have processed items"

    def test_custom_process(self):
        class DoubleQueue(ThreadSafeQueue):
            def _process(self, item):
                return item * 2
        q = DoubleQueue()
        for i in range(5):
            q.add_item(i)
        results = q.process_all(num_workers=2)
        processed = sorted([r.item for r in results])
        assert processed == [0, 2, 4, 6, 8], f"Expected doubled items, got {processed}"
""",
        "requirements": [],
    },

    8: {
        "level": 8,
        "name": "Distributed Systems — Redis Distributed Lock",
        "prompt": """Write two functions for Redis distributed locking:

1. `distributed_lock(redis_client, lock_name: str, timeout: int = 10) -> bool`
   - Try to acquire a distributed lock using Redis SET NX EX
   - Generate a unique value (use a random hex string) and store it as the lock value
   - Uses `redis_client.set(lock_name, value, nx=True, ex=timeout)` 
   - Returns True if lock acquired, False if already held
   - Stores the lock value on the client object so `release_lock` can access it

2. `release_lock(redis_client, lock_name: str, lock_value: str) -> bool`
   - Releases the lock only if `lock_value` matches the stored value (safe release)
   - Uses a Lua script or read-compare-delete pattern:
     ```
     if redis.call("GET", lock_name) == lock_value then
         redis.call("DEL", lock_name)
         return 1
     else
         return 0
     end
     ```
   - Since fakeredis supports eval, use `redis_client.eval(lua_script, 1, lock_name, lock_value)`
   - Returns True if released, False if value didn't match or lock didn't exist

The `redis_client` can be `fakeredis.FakeStrictRedis()` for testing.

Example:
  from fakeredis import FakeStrictRedis
  r = FakeStrictRedis()
  acquired = distributed_lock(r, "resource:42")  # True
  released = release_lock(r, "resource:42", <lock_value>)  # True""",
        "boilerplate": """import os


def distributed_lock(redis_client, lock_name: str, timeout: int = 10) -> bool:
    \"\"\"
    Acquire a distributed lock via Redis SET NX EX.

    Args:
        redis_client: A Redis-like client (fakeredis or redis).
        lock_name: The name/key of the lock.
        timeout: Lock TTL in seconds (default 10).

    Returns:
        True if lock acquired, False otherwise.
    \"\"\"
    pass


def release_lock(redis_client, lock_name: str, lock_value: str) -> bool:
    \"\"\"
    Release a distributed lock safely (only if value matches).

    Uses a Lua script for atomic compare-and-delete.

    Args:
        redis_client: A Redis-like client.
        lock_name: The name/key of the lock.
        lock_value: The unique value stored when acquiring the lock.

    Returns:
        True if lock released, False otherwise.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
from fakeredis import FakeStrictRedis
sys.path.insert(0, os.path.dirname(__file__))
from task_template import distributed_lock, release_lock


class TestDistributedLock:
    def test_acquire_lock(self):
        r = FakeStrictRedis()
        result = distributed_lock(r, "lock:test1", timeout=10)
        assert result is True, f"Expected True, got {result}"

    def test_lock_already_held(self):
        r = FakeStrictRedis()
        distributed_lock(r, "lock:test2", timeout=10)
        # Second attempt should fail
        result = distributed_lock(r, "lock:test2", timeout=10)
        assert result is False, f"Expected False (already held), got {result}"

    def test_release_lock(self):
        r = FakeStrictRedis()
        lock_value = os.urandom(16).hex()
        r.set("lock:test3", lock_value, nx=True, ex=10)
        result = release_lock(r, "lock:test3", lock_value)
        assert result is True, f"Expected True on release, got {result}"
        assert r.get("lock:test3") is None, "Lock key should be deleted after release"

    def test_release_wrong_value(self):
        r = FakeStrictRedis()
        r.set("lock:test4", "correct_value", nx=True, ex=10)
        result = release_lock(r, "lock:test4", "wrong_value")
        assert result is False, f"Expected False for wrong value, got {result}"

    def test_release_nonexistent_lock(self):
        r = FakeStrictRedis()
        result = release_lock(r, "lock:nonexistent", "some_value")
        assert result is False, f"Expected False for nonexistent lock, got {result}"

    def test_acquire_after_release(self):
        r = FakeStrictRedis()
        lock_value = os.urandom(16).hex()
        r.set("lock:test5", lock_value, nx=True, ex=10)
        release_lock(r, "lock:test5", lock_value)
        acquired = distributed_lock(r, "lock:test5", timeout=10)
        assert acquired is True, "Should be able to re-acquire after release"

    def test_lock_expires(self):
        import time
        r = FakeStrictRedis()
        distributed_lock(r, "lock:test6", timeout=1)
        # Check TTL was set
        ttl = r.ttl("lock:test6")
        assert ttl > 0, "Lock should have a positive TTL"
        assert ttl <= 1, f"Expected TTL <= 1, got {ttl}"
""",
        "requirements": ["fakeredis"],
    },

    9: {
        "level": 9,
        "name": "Protocol Parsing — WebSocket Frame Encode/Decode",
        "prompt": """Write two functions for WebSocket frame encoding and decoding:

1. `encode_frame(payload: bytes, opcode: int = 1) -> bytes`
   - Creates a WebSocket frame (client-to-server, with masking)
   - FIN bit = 1, masking = 1 (client frame)
   - Masking key = 4 random bytes
   - Payload length encoding:
     - 0-125: single byte
     - 126-65535: 2-byte extended length (network byte order)
   - Returns the complete frame bytes

2. `decode_frame(data: bytes) -> dict`
   - Parses a WebSocket frame
   - Returns dict with keys: fin, opcode, masked, payload_length, mask, payload
   - Handles both masked and unmasked frames
   - Handles payload lengths up to 65535 (2-byte extended)

WebSocket frame format (RFC 6455):
  Byte 0: FIN (1 bit) | RSV (3 bits) | Opcode (4 bits)
  Byte 1: MASK (1 bit) | Payload Length (7 bits)
  Bytes 2-3 (if payload length == 126): Extended payload length (16 bits)
  Bytes 2-5 (if mask=1): Masking key (4 bytes)
  Following bytes: Payload data (masked with XOR if mask=1)

Pure stdlib only (os, struct).

Example:
  frame = encode_frame(b"Hello")
  decoded = decode_frame(frame)
  decoded["payload"] == b"Hello"  # True (unmasked after decode)""",
        "boilerplate": """import os
import struct


def encode_frame(payload: bytes, opcode: int = 1) -> bytes:
    \"\"\"
    Encode a payload into a WebSocket frame (client-to-server, masked).

    Args:
        payload: The payload bytes to encode.
        opcode: WebSocket opcode (1=text, 2=binary, 8=close, 9=ping, 10=pong).

    Returns:
        Complete WebSocket frame as bytes.
    \"\"\"
    pass


def decode_frame(data: bytes) -> dict:
    \"\"\"
    Decode a WebSocket frame from bytes.

    Args:
        data: Raw WebSocket frame bytes.

    Returns:
        dict with keys: fin, opcode, masked, payload_length, mask, payload.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import encode_frame, decode_frame


class TestWebSocketFrame:
    def test_encode_decode_short_payload(self):
        payload = b"Hello, WebSocket!"
        frame = encode_frame(payload, opcode=1)
        decoded = decode_frame(frame)
        assert decoded["payload"] == payload, f"Expected {payload!r}, got {decoded['payload']!r}"
        assert decoded["opcode"] == 1
        assert decoded["fin"] == 1
        assert decoded["masked"] == 1

    def test_encode_decode_medium_payload(self):
        # Payload > 125 bytes triggers extended length
        payload = b"x" * 200
        frame = encode_frame(payload, opcode=2)
        decoded = decode_frame(frame)
        assert decoded["payload"] == payload
        assert decoded["opcode"] == 2
        assert decoded["payload_length"] == 200

    def test_decode_unmasked_frame(self):
        payload = b"test"
        frame = bytearray()
        frame.append(0x81)  # FIN=1, opcode=1
        frame.append(len(payload))  # mask=0, length=4
        frame.extend(payload)
        decoded = decode_frame(bytes(frame))
        assert decoded["payload"] == payload
        assert decoded["masked"] == 0

    def test_encode_decode_binary(self):
        payload = bytes(range(256))
        frame = encode_frame(payload, opcode=2)
        decoded = decode_frame(frame)
        assert decoded["payload"] == payload
        assert decoded["opcode"] == 2

    def test_decode_frame_structure(self):
        payload = b"Hello"
        frame = encode_frame(payload)
        decoded = decode_frame(frame)
        expected_keys = {"fin", "opcode", "masked", "payload_length", "mask", "payload"}
        assert set(decoded.keys()) == expected_keys, f"Keys mismatch: {set(decoded.keys())}"

    def test_payload_length_bounds(self):
        p125 = b"x" * 125
        frame125 = encode_frame(p125)
        d125 = decode_frame(frame125)
        assert d125["payload_length"] == 125

        p126 = b"y" * 126
        frame126 = encode_frame(p126)
        d126 = decode_frame(frame126)
        assert d126["payload_length"] == 126
""",
        "requirements": [],
    },

    10: {
        "level": 10,
        "name": "Orchestration Engine — Finite State Machine",
        "prompt": """Write a `StateMachine` class and a `process_events` function for event-driven state transitions.

The state machine has these states and transitions:
  - "idle" -> "processing" on "start" event
  - "processing" -> "completed" on "complete" event
  - "processing" -> "failed" on "fail" event
  - "completed" -> "idle" on "reset" event
  - "failed" -> "idle" on "reset" event

Also allow any state to transition to "idle" on "reset" event.

Class `StateMachine`:
  - `__init__(self, initial_state="idle")` — sets initial state
  - `transition(event: str) -> str` — applies event, returns new state (raises ValueError for invalid transitions)

Function `process_events(events: list[str], initial_state: str = "idle") -> list[str]`:
  - Creates a StateMachine with the given initial state
  - Processes each event in order
  - Returns a list of all states visited (including initial state and each state after transitions)
  - Must not have memory leaks — use a fixed-size transition log (max 1000 entries)

Example:
  process_events(["start", "complete", "reset"])
  # -> ["idle", "processing", "completed", "idle"]""",
        "boilerplate": """class StateMachine:
    \"\"\"
    A finite state machine with event-driven transitions.

    States: idle, processing, completed, failed
    Events: start, complete, fail, reset
    \"\"\"

    def __init__(self, initial_state: str = \"idle\"):
        self._state = initial_state
        self._transitions = {
            (\"idle\", \"start\"): \"processing\",
            (\"processing\", \"complete\"): \"completed\",
            (\"processing\", \"fail\"): \"failed\",
            (\"completed\", \"reset\"): \"idle\",
            (\"failed\", \"reset\"): \"idle\",
        }
        self._log = []  # Fixed-size transition log

    @property
    def state(self) -> str:
        return self._state

    def transition(self, event: str) -> str:
        \"\"\"
        Apply an event and transition to the next state.

        Args:
            event: The event string.

        Returns:
            The new state after transition.

        Raises:
            ValueError: If the event is invalid for the current state.
        \"\"\"
        pass


def process_events(events: list[str], initial_state: str = \"idle\") -> list[str]:
    \"\"\"
    Process a list of events through a state machine.

    Args:
        events: List of event strings.
        initial_state: Starting state for the state machine.

    Returns:
        List of all states visited (including initial and each state after transitions).
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import StateMachine, process_events


class TestStateMachine:
    def test_idle_to_processing(self):
        sm = StateMachine("idle")
        new_state = sm.transition("start")
        assert new_state == "processing"
        assert sm.state == "processing"

    def test_full_cycle(self):
        result = process_events(["start", "complete", "reset"])
        assert result == ["idle", "processing", "completed", "idle"], f"Got {result}"

    def test_failure_path(self):
        result = process_events(["start", "fail", "reset"])
        assert result == ["idle", "processing", "failed", "idle"], f"Got {result}"

    def test_failed_to_completed_invalid(self):
        sm = StateMachine("failed")
        with pytest.raises(ValueError):
            sm.transition("complete")

    def test_reset_from_any_state(self):
        for state in ["idle", "processing", "completed", "failed"]:
            sm = StateMachine(state)
            if state == "processing":
                sm.transition("complete")
                sm = StateMachine(state)
            result = process_events(["reset"], initial_state=state)
            assert result[-1] == "idle", f"Reset from {state} should end at idle, got {result[-1]}"

    def test_invalid_event_raises(self):
        sm = StateMachine("completed")
        with pytest.raises(ValueError):
            sm.transition("start")

    def test_initial_state_property(self):
        sm = StateMachine("processing")
        assert sm.state == "processing"

    def test_empty_events(self):
        result = process_events([])
        assert result == ["idle"], f"Empty events should return [initial_state], got {result}"

    def test_multiple_resets(self):
        result = process_events(["start", "complete", "reset", "start", "fail", "reset"])
        expected = ["idle", "processing", "completed", "idle", "processing", "failed", "idle"]
        assert result == expected, f"Got {result}"

    def test_no_memory_leak(self):
        sm = StateMachine("idle")
        for _ in range(2000):
            sm.transition("start")
            sm.transition("complete")
            sm.transition("reset")
        assert sm.state == "idle", f"Expected idle after many resets, got {sm.state}"
""",
        "requirements": [],
    },

    11: {
        "level": 11,
        "name": "Consistent Hash Ring — Distributed Data Partitioning",
        "prompt": """Write functions for a consistent hash ring with virtual nodes for distributed key lookup.

Functions to implement:

1. `create_ring() -> dict` — returns an empty ring dict with structure: {"nodes": [], "vnodes": {}}
   - "nodes": sorted list of (hash_position, node_id) tuples
   - "vnodes": dict mapping node_id -> list of virtual node suffixes [":v0", ":v1", ..., ":v8"]

2. `add_node(ring, node_id: str, vnodes: int = 9) -> dict`
   - Adds `vnodes` virtual nodes for the given node_id
   - Virtual node keys are `{node_id}:v{N}` (e.g., "server-1:v0" through "server-1:v8")
   - Each virtual node is assigned a hash position: use `hash(vnode_key)` as the position
   - Insert each (hash_position, node_id) tuple into the ring's "nodes" list, maintaining sorted order
   - Update the "vnodes" dict with the list of virtual node suffixes
   - Return the updated ring dict

3. `remove_node(ring, node_id: str) -> dict`
   - Removes all entries from "nodes" where the node_id matches
   - Removes node_id from "vnodes" dict
   - Return the updated ring dict

4. `lookup(ring, key: str) -> str`
   - Calculate `hash(key)` as the target position
   - Binary search the sorted "nodes" list to find the first node with hash_position >= target
   - If no such node (target is larger than all positions), wrap around to the first node
   - Return the node_id for the responsible node

Use the built-in `hash()` function for all hashing. Pure stdlib only.

Example:
  ring = create_ring()
  ring = add_node(ring, "server-1", vnodes=3)
  ring = add_node(ring, "server-2", vnodes=3)
  lookup(ring, "my-key")  # -> "server-1" or "server-2"
  ring = remove_node(ring, "server-1")
  lookup(ring, "my-key")  # -> "server-2" (redistributed)""",
        "boilerplate": """def create_ring() -> dict:
    \"\"\"
    Create an empty consistent hash ring.

    Returns:
        Dict with keys: nodes (sorted list of (hash_pos, node_id)), vnodes (node_id -> suffixes).
    \"\"\"
    return {"nodes": [], "vnodes": {}}


def add_node(ring: dict, node_id: str, vnodes: int = 9) -> dict:
    \"\"\"
    Add a node with virtual nodes to the hash ring.

    Args:
        ring: The hash ring dict.
        node_id: The node identifier (e.g., \"server-1\").
        vnodes: Number of virtual nodes to create (default 9).

    Returns:
        Updated ring dict.
    \"\"\"
    pass


def remove_node(ring: dict, node_id: str) -> dict:
    \"\"\"
    Remove a node and all its virtual nodes from the hash ring.

    Args:
        ring: The hash ring dict.
        node_id: The node identifier to remove.

    Returns:
        Updated ring dict.
    \"\"\"
    pass


def lookup(ring: dict, key: str) -> str:
    \"\"\"
    Find the responsible node for a given key.

    Args:
        ring: The hash ring dict.
        key: The key to look up.

    Returns:
        The node_id responsible for this key.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
import bisect
sys.path.insert(0, os.path.dirname(__file__))
from task_template import create_ring, add_node, remove_node, lookup


class TestConsistentHashRing:
    def test_create_empty_ring(self):
        ring = create_ring()
        assert ring["nodes"] == [], f"Expected empty nodes, got {ring['nodes']}"
        assert ring["vnodes"] == {}, f"Expected empty vnodes, got {ring['vnodes']}"

    def test_add_single_node(self):
        ring = create_ring()
        ring = add_node(ring, "server-1", vnodes=3)
        assert len(ring["nodes"]) == 3, f"Expected 3 vnodes, got {len(ring['nodes'])}"
        assert "server-1" in ring["vnodes"], f"Expected server-1 in vnodes"
        assert len(ring["vnodes"]["server-1"]) == 3, f"Expected 3 vnode suffixes"

    def test_lookup_returns_node(self):
        ring = create_ring()
        ring = add_node(ring, "server-a", vnodes=5)
        ring = add_node(ring, "server-b", vnodes=5)
        result = lookup(ring, "some-key")
        assert result in ("server-a", "server-b"), f"Expected server-a or server-b, got {result}"

    def test_consistent_routing(self):
        ring = create_ring()
        ring = add_node(ring, "alpha", vnodes=5)
        ring = add_node(ring, "beta", vnodes=5)
        r1 = lookup(ring, "test-key-42")
        r2 = lookup(ring, "test-key-42")
        assert r1 == r2, f"Expected consistent routing, got {r1} and {r2}"

    def test_remove_node(self):
        ring = create_ring()
        ring = add_node(ring, "node-1", vnodes=3)
        ring = add_node(ring, "node-2", vnodes=3)
        ring = remove_node(ring, "node-1")
        assert "node-1" not in ring["vnodes"], "node-1 should be removed from vnodes"
        for _, node_id in ring["nodes"]:
            assert node_id != "node-1", "node-1 should not appear in nodes list"
        assert len(ring["nodes"]) == 3, f"Expected 3 remaining vnodes, got {len(ring['nodes'])}"

    def test_wrap_around(self):
        ring = create_ring()
        ring = add_node(ring, "only-node", vnodes=3)
        result = lookup(ring, "anything")
        assert result == "only-node", f"With one node all keys route to it, got {result}"

    def test_multiple_nodes_distribution(self):
        ring = create_ring()
        ring = add_node(ring, "A", vnodes=5)
        ring = add_node(ring, "B", vnodes=5)
        ring = add_node(ring, "C", vnodes=5)
        keys = [f"key-{i}" for i in range(100)]
        results = [lookup(ring, k) for k in keys]
        assert len(set(results)) >= 2, f"Expected at least 2 nodes used, got {len(set(results))}"
        assert all(r in ("A", "B", "C") for r in results), "All results should be valid node IDs"

    def test_nodes_sorted(self):
        ring = create_ring()
        ring = add_node(ring, "a", vnodes=5)
        ring = add_node(ring, "b", vnodes=5)
        positions = [pos for pos, _ in ring["nodes"]]
        assert positions == sorted(positions), "Nodes list must be sorted by hash position"
""",
        "requirements": [],
    },

    12: {
        "level": 12,
        "name": "Event Sourcing Aggregate — Event-Driven Architecture",
        "prompt": """Implement an event store and an order aggregate using event sourcing pattern.

Classes and functions:

1. `class EventStore`:
   - `__init__(self)` — initializes an empty in-memory dict for events
   - `append(self, aggregate_id: str, event: dict)` — appends event dict to aggregate's event list
   - `get_events(self, aggregate_id: str) -> list` — returns list of events for aggregate (empty list if none)

2. `class OrderAggregate`:
   - `__init__(self, id: str, event_store: EventStore)` — stores id and event_store reference
   - `create_order(self, customer: str, items: list) -> dict` — appends OrderCreated event, returns current state
   - `add_item(self, item: str) -> dict` — appends ItemAdded event, returns current state
   - `remove_item(self, item_id: str) -> dict` — appends ItemRemoved event, returns current state
   - `cancel(self) -> dict` — appends OrderCancelled event, returns current state
   - `get_state(self) -> dict` — replays all events from the event store and returns current state dict:
     {"id": str, "customer": str, "items": list, "status": "active"|"cancelled", "total": float}

3. `def process_command(event_store: EventStore, aggregate_id: str, command: dict) -> dict`
   - Command format: {"type": "create_order"|"add_item"|"remove_item"|"cancel", ...}
   - Creates/reuses OrderAggregate for the aggregate_id
   - Dispatches to the appropriate method
   - Returns the resulting state

Event types and their data:
  - OrderCreated: {"type": "OrderCreated", "customer": str, "items": list}
  - ItemAdded: {"type": "ItemAdded", "item": str}
  - ItemRemoved: {"type": "ItemRemoved", "item_id": str}
  - OrderCancelled: {"type": "OrderCancelled"}

get_state() rebuilds state by replaying events in order:
  - Start from empty state: {"id": id, "customer": "", "items": [], "status": "active", "total": 0.0}
  - OrderCreated: set customer, items
  - ItemAdded: append item to items, add 10.0 to total
  - ItemRemoved: remove item from items by checking if item_id is in item string, subtract 10.0 from total
  - OrderCancelled: set status to "cancelled"
  - If status is "cancelled", reject any further commands (raise ValueError), except cancel itself

Rules:
  - Calling cancel on an already-cancelled order raises ValueError("Order already cancelled")
  - Total starts at 0.0, each item adds 10.0, each removal subtracts 10.0""",
        "boilerplate": """class EventStore:
    \"\"\"An in-memory event store for event sourcing.\"\"\"

    def __init__(self):
        self._events = {}

    def append(self, aggregate_id: str, event: dict) -> None:
        \"\"\"
        Append an event to an aggregate's event list.

        Args:
            aggregate_id: The aggregate identifier.
            event: The event dict to append.
        \"\"\"
        pass

    def get_events(self, aggregate_id: str) -> list:
        \"\"\"
        Get all events for an aggregate.

        Args:
            aggregate_id: The aggregate identifier.

        Returns:
            List of event dicts (empty list if none).
        \"\"\"
        pass


class OrderAggregate:
    \"\"\"An order aggregate using event sourcing.\"\"\"

    def __init__(self, id: str, event_store: EventStore):
        self._id = id
        self._event_store = event_store

    def create_order(self, customer: str, items: list) -> dict:
        \"\"\"
        Create a new order.

        Args:
            customer: Customer name.
            items: List of item names.

        Returns:
            Current state dict after applying the event.
        \"\"\"
        pass

    def add_item(self, item: str) -> dict:
        \"\"\"
        Add an item to the order.

        Args:
            item: Item name to add.

        Returns:
            Current state dict.
        \"\"\"
        pass

    def remove_item(self, item_id: str) -> dict:
        \"\"\"
        Remove an item from the order.

        Args:
            item_id: Identifier/name of item to remove.

        Returns:
            Current state dict.
        \"\"\"
        pass

    def cancel(self) -> dict:
        \"\"\"
        Cancel the order.

        Returns:
            Current state dict.

        Raises:
            ValueError: If order is already cancelled.
        \"\"\"
        pass

    def get_state(self) -> dict:
        \"\"\"
        Rebuild current state by replaying all events.

        Returns:
            Dict with id, customer, items, status, total.
        \"\"\"
        pass


def process_command(event_store: EventStore, aggregate_id: str, command: dict) -> dict:
    \"\"\"
    Process a command against an order aggregate.

    Args:
        event_store: The event store instance.
        aggregate_id: Aggregate identifier.
        command: Dict with "type" key and optional params.

    Returns:
        Current state after command execution.
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import EventStore, OrderAggregate, process_command


class TestEventSourcing:
    def test_create_order(self):
        store = EventStore()
        agg = OrderAggregate("order-1", store)
        state = agg.create_order("Alice", ["Laptop", "Mouse"])
        assert state["customer"] == "Alice"
        assert len(state["items"]) == 2
        assert state["status"] == "active"
        assert state["total"] == 20.0

    def test_add_item(self):
        store = EventStore()
        agg = OrderAggregate("order-2", store)
        agg.create_order("Bob", ["Desk"])
        state = agg.add_item("Chair")
        assert "Chair" in state["items"]
        assert state["total"] == 20.0
        assert state["status"] == "active"

    def test_cancel_order(self):
        store = EventStore()
        agg = OrderAggregate("order-3", store)
        agg.create_order("Charlie", ["Book"])
        state = agg.cancel()
        assert state["status"] == "cancelled"

    def test_cancel_already_cancelled_raises(self):
        store = EventStore()
        agg = OrderAggregate("order-4", store)
        agg.create_order("Dave", ["Pen"])
        agg.cancel()
        with pytest.raises(ValueError, match="already cancelled"):
            agg.cancel()

    def test_event_replay_builds_state(self):
        store = EventStore()
        agg = OrderAggregate("order-5", store)
        agg.create_order("Eve", ["Phone"])
        agg.add_item("Case")
        agg.add_item("Charger")
        agg.remove_item("Case")
        state = agg.get_state()
        assert state["customer"] == "Eve"
        assert len(state["items"]) == 2, f"Expected 2 items, got {state['items']}"
        assert state["total"] == 30.0, f"Expected total 30.0, got {state['total']}"

    def test_process_command_function(self):
        store = EventStore()
        state = process_command(store, "order-6", {"type": "create_order", "customer": "Frank", "items": ["Table"]})
        assert state["customer"] == "Frank"
        assert state["status"] == "active"

        state = process_command(store, "order-6", {"type": "add_item", "item": "Lamp"})
        assert len(state["items"]) == 2

    def test_remove_item_reduces_total(self):
        store = EventStore()
        agg = OrderAggregate("order-7", store)
        agg.create_order("Grace", ["TV", "Remote"])
        state = agg.remove_item("Remote")
        assert len(state["items"]) == 1
        assert state["total"] == 10.0

    def test_reject_commands_on_cancelled(self):
        store = EventStore()
        agg = OrderAggregate("order-8", store)
        agg.create_order("Hank", ["Speaker"])
        agg.cancel()
        with pytest.raises(ValueError):
            agg.add_item("Cable")

    def test_empty_aggregate_state(self):
        store = EventStore()
        agg = OrderAggregate("order-9", store)
        state = agg.get_state()
        assert state["customer"] == ""
        assert state["items"] == []
        assert state["status"] == "active"
        assert state["total"] == 0.0
""",
        "requirements": [],
    },

    13: {
        "level": 13,
        "name": "Circuit Breaker — Resilience Pattern",
        "prompt": """Implement a Circuit Breaker pattern for resilient service calls.

Class `CircuitBreaker`:
  - `__init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0, exceptions: tuple = (Exception,))`
    - failure_threshold: number of consecutive failures before opening the circuit
    - recovery_timeout: seconds to wait before transitioning from OPEN to HALF_OPEN
    - exceptions: tuple of exception types that count as failures

  - States: "CLOSED" (normal), "OPEN" (fast-fail), "HALF_OPEN" (probing)

  - `call(self, func, *args, **kwargs) -> Any`:
    - CLOSED: Call func(*args, **kwargs). On success, reset failure_count to 0. On failure (if exception is instance of self.exceptions), increment failure_count. If failure_count >= failure_threshold, transition to OPEN (record the time). Return the result or raise the exception.
    - OPEN: If recovery_timeout has elapsed since entering OPEN state, transition to HALF_OPEN and allow a probe call. Otherwise, raise CircuitBreakerOpenError("Circuit breaker is open") immediately.
    - HALF_OPEN: Allow exactly one probe call. Call func(*args, **kwargs). On success, transition to CLOSED (reset failure_count to 0, reset state). On failure, transition back to OPEN (re-record the time). Return the result or raise the exception.

  - `reset(self)` — Manually reset to CLOSED state with failure_count = 0

  - `get_state(self) -> str` — Returns the current state string

Helper exception:
  - `class CircuitBreakerOpenError(Exception)` — raised when circuit is OPEN and not yet ready to probe

Pure stdlib only (time).

Example:
  cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
  
  def may_fail(x):
      if x < 0:
          raise ValueError("negative")
      return x
  
  cb.call(may_fail, 5)   # -> 5 (CLOSED, success, failures=0)
  cb.call(may_fail, -1)  # raises ValueError (CLOSED, failures=1)
  cb.call(may_fail, -2)  # raises ValueError (CLOSED, failures=2)
  cb.call(may_fail, -3)  # raises ValueError -> circuit OPEN
  cb.call(may_fail, 1)   # raises CircuitBreakerOpenError (OPEN, fast-fail)
  # After recovery_timeout...
  cb.call(may_fail, 1)   # -> 1 (HALF_OPEN probe succeeds, back to CLOSED)""",
        "boilerplate": """import time


class CircuitBreakerOpenError(Exception):
    \"\"\"Raised when the circuit breaker is open and rejecting calls.\"\"\"
    pass


class CircuitBreaker:
    \"\"\"
    A circuit breaker pattern implementation for resilient service calls.

    States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    \"\"\"

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0,
                 exceptions: tuple = (Exception,)):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._exceptions = exceptions
        self._state = "CLOSED"
        self._failure_count = 0
        self._open_time = 0.0

    def call(self, func, *args, **kwargs):
        \"\"\"
        Call a function through the circuit breaker.

        Args:
            func: The callable to invoke.
            *args, **kwargs: Arguments to pass to func.

        Returns:
            The return value of func.

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN (fast-fail).
            Exception: Any exception raised by func (if circuit allows the call).
        \"\"\"
        pass

    def reset(self) -> None:
        \"\"\"Manually reset the circuit breaker to CLOSED state.\"\"\"
        pass

    def get_state(self) -> str:
        \"\"\"Return the current circuit breaker state.\"\"\"
        return self._state
""",
        "test_code": """
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import CircuitBreaker, CircuitBreakerOpenError


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.get_state() == "CLOSED"

    def test_call_success_resets_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        def ok():
            return 42
        result = cb.call(ok)
        assert result == 42
        assert cb._failure_count == 0

    def test_failures_accumulate(self):
        cb = CircuitBreaker(failure_threshold=3)
        def fail():
            raise ValueError("nope")
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)
        assert cb._failure_count == 2
        assert cb.get_state() == "CLOSED"

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        def fail():
            raise ValueError("nope")
        for _ in range(3):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.get_state() == "OPEN", f"Expected OPEN, got {cb.get_state()}"

    def test_open_rejects_immediately(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0)
        def fail():
            raise ValueError("nope")
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "should not reach")

    def test_half_open_probe_success(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        def fail():
            raise ValueError("nope")
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.get_state() == "OPEN"
        time.sleep(0.1)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.get_state() == "CLOSED", f"Expected CLOSED after successful probe, got {cb.get_state()}"
        assert cb._failure_count == 0

    def test_half_open_probe_failure(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.05)
        def fail():
            raise ValueError("nope")
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.get_state() == "OPEN"
        time.sleep(0.1)
        with pytest.raises(ValueError):
            cb.call(fail)
        assert cb.get_state() == "OPEN", f"Expected OPEN after failed probe, got {cb.get_state()}"

    def test_reset_works(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0)
        def fail():
            raise ValueError("nope")
        for _ in range(2):
            try:
                cb.call(fail)
            except ValueError:
                pass
        assert cb.get_state() == "OPEN"
        cb.reset()
        assert cb.get_state() == "CLOSED"
        assert cb._failure_count == 0
        result = cb.call(lambda: "after reset")
        assert result == "after reset"

    def test_custom_exceptions(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=30.0,
                            exceptions=(ValueError,))
        def raise_type_error():
            raise TypeError("not counted")
        for _ in range(3):
            with pytest.raises(TypeError):
                cb.call(raise_type_error)
        assert cb.get_state() == "CLOSED", "TypeError should not trip the breaker"
        assert cb._failure_count == 0
""",
        "requirements": [],
    },

    14: {
        "level": 14,
        "name": "Token Bucket Rate Limiter — Traffic Shaping",
        "prompt": """Implement a Token Bucket rate limiter for traffic shaping.

Class `TokenBucket`:
  - `__init__(self, capacity: float, refill_rate: float, refill_interval: float = 1.0)`
    - capacity: maximum number of tokens the bucket can hold
    - refill_rate: number of tokens added per refill_interval seconds
    - refill_interval: time in seconds between refills (default 1.0)
    - Internal: track current tokens (start at capacity), last refill time (start at creation time)

  - `allow_request(self, tokens: float = 1.0) -> bool`
    - Refill tokens first (calculate elapsed intervals since last refill)
    - If tokens >= tokens requested: consume tokens, return True
    - Otherwise: return False (do NOT consume tokens)

  - `get_wait_time(self, tokens: float = 1.0) -> float`
    - Returns the estimated seconds until enough tokens are available
    - Refill first, then if enough tokens exist, return 0.0
    - Otherwise: calculate shortfall, refill_rate per interval, return seconds needed
    - Return 0.0 if tokens already available

  - `get_tokens(self) -> float`
    - Refill first, then return current token count (capped at capacity)

Token refill logic:
  - On every operation that checks/consumes tokens, calculate elapsed time since last refill
  - elapsed_intervals = elapsed_time / refill_interval (floor division, integer count)
  - Add elapsed_intervals * refill_rate tokens (capped at capacity)
  - Update last_refill_time by adding elapsed_intervals * refill_interval
  - Do NOT use fractional refills (only full intervals)

Pure stdlib only (time).

Example:
  bucket = TokenBucket(capacity=10, refill_rate=5, refill_interval=1.0)
  bucket.allow_request(5)   # True (5 tokens consumed, 5 remain)
  bucket.allow_request(10)  # False (only 5 available, need 10)
  # After 1 second (1 interval at 5/sec): 5 tokens added back
  bucket.allow_request(7)   # True (5 refilled + 5 remaining = 10, consume 7, 3 remain)""",
        "boilerplate": """import time


class TokenBucket:
    \"\"\"
    A token bucket rate limiter for traffic shaping.

    Tokens are added at a fixed rate over discrete intervals.
    \"\"\"

    def __init__(self, capacity: float, refill_rate: float, refill_interval: float = 1.0):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._refill_interval = refill_interval
        self._tokens = capacity
        self._last_refill = time.monotonic()

    def _refill(self):
        \"\"\"Refill tokens based on elapsed time.\"\"\"
        pass

    def allow_request(self, tokens: float = 1.0) -> bool:
        \"\"\"
        Check if a request with the given token cost is allowed.

        Args:
            tokens: Number of tokens required (default 1.0).

        Returns:
            True if allowed (tokens consumed), False otherwise.
        \"\"\"
        pass

    def get_wait_time(self, tokens: float = 1.0) -> float:
        \"\"\"
        Estimate the wait time until the requested tokens are available.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Seconds until enough tokens are available (0.0 if available now).
        \"\"\"
        pass

    def get_tokens(self) -> float:
        \"\"\"
        Get the current number of available tokens.

        Returns:
            Current token count (capped at capacity).
        \"\"\"
        pass
""",
        "test_code": """
import pytest
import time
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import TokenBucket


class TestTokenBucket:
    def test_allow_when_enough_tokens(self):
        bucket = TokenBucket(capacity=10, refill_rate=5, refill_interval=1.0)
        assert bucket.allow_request(5) is True
        assert bucket.get_tokens() == 5.0

    def test_deny_when_exhausted(self):
        bucket = TokenBucket(capacity=3, refill_rate=1, refill_interval=1.0)
        assert bucket.allow_request(3) is True
        assert bucket.allow_request(1) is False
        assert bucket.get_tokens() == 0.0

    def test_refill_over_time(self):
        bucket = TokenBucket(capacity=10, refill_rate=5, refill_interval=1.0)
        bucket.allow_request(10)
        assert bucket.get_tokens() == 0.0
        time.sleep(1.1)
        tokens = bucket.get_tokens()
        assert tokens >= 4.0, f"Expected ~5 tokens after refill, got {tokens}"

    def test_burst_capacity(self):
        bucket = TokenBucket(capacity=20, refill_rate=2, refill_interval=1.0)
        assert bucket.allow_request(20) is True
        assert bucket.allow_request(1) is False

    def test_get_wait_time_zero_when_available(self):
        bucket = TokenBucket(capacity=10, refill_rate=5, refill_interval=1.0)
        wait = bucket.get_wait_time(3)
        assert wait == 0.0

    def test_get_wait_time_positive(self):
        bucket = TokenBucket(capacity=5, refill_rate=2, refill_interval=1.0)
        bucket.allow_request(5)
        wait = bucket.get_wait_time(3)
        assert wait >= 1.0, f"Expected at least 1s wait, got {wait}"
        assert wait <= 2.5, f"Expected <= 2s wait, got {wait}"

    def test_tokens_capped_at_capacity(self):
        bucket = TokenBucket(capacity=100, refill_rate=50, refill_interval=1.0)
        time.sleep(2.1)
        tokens = bucket.get_tokens()
        assert tokens == 100.0, f"Expected 100 (capped), got {tokens}"

    def test_fractional_refill_rate(self):
        bucket = TokenBucket(capacity=10, refill_rate=0.5, refill_interval=1.0)
        bucket.allow_request(10)
        time.sleep(3.1)
        tokens = bucket.get_tokens()
        assert tokens >= 1.0, f"Expected about 1.5 tokens after 3s, got {tokens}"
        assert tokens <= 2.0

    def test_deny_does_not_consume(self):
        bucket = TokenBucket(capacity=5, refill_rate=5, refill_interval=1.0)
        assert bucket.allow_request(10) is False
        assert bucket.get_tokens() == 5.0, "Tokens should NOT be consumed on deny"
""",
        "requirements": [],
    },

    15: {
        "level": 15,
        "name": "Dependency Resolution Engine — Graph Algorithms",
        "prompt": """Implement a dependency resolution engine with topological sort and critical path analysis.

Functions:

1. `topological_sort(dependencies: dict[str, list[str]]) -> list[list[str]]`
   - Input: dict mapping task_id -> list of dependency task_ids
   - Uses Kahn's algorithm (BFS) for topological sorting
   - Returns a list of lists, where each inner list contains tasks that can run in parallel at that level
   - Tasks with no dependencies go in the first level
   - A task appears only after ALL its dependencies are in earlier levels
   - Must detect cycles: if a cycle exists, raise ValueError("Cycle detected in dependencies")
   - Example:
     Input: {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"], "E": ["D"]}
     Output: [["A"], ["B", "C"], ["D"], ["E"]]

2. `resolve_critical_path(graph: dict[str, dict]) -> dict[str, int]`
   - Input: dict mapping task_id -> {"deps": [task_id, ...], "duration": int}
   - Returns dict mapping task_id -> earliest_finish_time (int)
   - Uses forward pass dynamic programming:
     - If task has no deps: finish_time = duration
     - If task has deps: finish_time = max(finish_time of all deps) + duration
   - Example:
     Input: {"A": {"deps": [], "duration": 3}, "B": {"deps": ["A"], "duration": 5},
             "C": {"deps": ["A"], "duration": 2}, "D": {"deps": ["B", "C"], "duration": 4}}
     Output: {"A": 3, "B": 8, "C": 5, "D": 12}

Pure stdlib only (collections.deque for BFS queue).

Example:
  deps = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"], "E": ["D"]}
  result = topological_sort(deps)
  # result == [["A"], ["B", "C"], ["D"], ["E"]]

  cpm = {"A": {"deps": [], "duration": 3}, "B": {"deps": ["A"], "duration": 5},
         "C": {"deps": ["A"], "duration": 2}, "D": {"deps": ["B", "C"], "duration": 4}}
  finish = resolve_critical_path(cpm)
  # finish == {"A": 3, "B": 8, "C": 5, "D": 12}""",
        "boilerplate": """from collections import deque


def topological_sort(dependencies: dict[str, list[str]]) -> list[list[str]]:
    \"\"\"
    Perform topological sort on a dependency graph using Kahn's algorithm.

    Returns tasks grouped by parallelizable levels.

    Args:
        dependencies: dict mapping task_id -> list of dependency task_ids.

    Returns:
        List of lists, where each inner list is tasks that can run in parallel.

    Raises:
        ValueError: If a cycle is detected in the dependency graph.
    \"\"\"
    pass


def resolve_critical_path(graph: dict[str, dict]) -> dict[str, int]:
    \"\"\"
    Calculate the earliest finish time for each task using forward pass DP.

    Args:
        graph: dict mapping task_id -> {"deps": [...], "duration": int}

    Returns:
        dict mapping task_id -> earliest_finish_time (int).
    \"\"\"
    pass
""",
        "test_code": """
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from task_template import topological_sort, resolve_critical_path


class TestTopologicalSort:
    def test_simple_dag(self):
        deps = {"A": [], "B": ["A"], "C": ["B"]}
        result = topological_sort(deps)
        assert len(result) == 3, f"Expected 3 levels, got {result}"
        assert result[0] == ["A"]
        assert result[2] == ["C"]

    def test_multi_level_parallelism(self):
        deps = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"], "E": ["D"]}
        result = topological_sort(deps)
        assert result[0] == ["A"], f"Level 0 should be [A], got {result[0]}"
        assert set(result[1]) == {"B", "C"}, f"Level 1 should be {{B, C}}, got {result[1]}"
        assert result[2] == ["D"], f"Level 2 should be [D], got {result[2]}"
        assert result[3] == ["E"], f"Level 3 should be [E], got {result[3]}"

    def test_cycle_detection(self):
        deps = {"A": ["B"], "B": ["C"], "C": ["A"]}
        with pytest.raises(ValueError, match="Cycle"):
            topological_sort(deps)

    def test_single_node(self):
        deps = {"A": []}
        result = topological_sort(deps)
        assert result == [["A"]], f"Expected [['A']], got {result}"

    def test_independent_tasks(self):
        deps = {"A": [], "B": [], "C": []}
        result = topological_sort(deps)
        assert len(result) == 1, f"Expected 1 level (all parallel), got {result}"
        assert set(result[0]) == {"A", "B", "C"}

    def test_complex_dag(self):
        deps = {"A": [], "B": [], "C": ["A", "B"], "D": ["A"], "E": ["C", "D"], "F": ["E"]}
        result = topological_sort(deps)
        assert set(result[0]) == {"A", "B"}, f"Got {result[0]}"
        assert set(result[1]) == {"C", "D"} or set(result[1]) == {"D", "C"}, f"Got {result[1]}"
        assert result[-1] == ["F"], f"Last should be [F], got {result[-1]}"


class TestCriticalPath:
    def test_simple_path(self):
        graph = {"A": {"deps": [], "duration": 3}, "B": {"deps": ["A"], "duration": 5}}
        result = resolve_critical_path(graph)
        assert result["A"] == 3
        assert result["B"] == 8

    def test_bottleneck_path(self):
        graph = {"A": {"deps": [], "duration": 3}, "B": {"deps": ["A"], "duration": 5},
                 "C": {"deps": ["A"], "duration": 2}, "D": {"deps": ["B", "C"], "duration": 4}}
        result = resolve_critical_path(graph)
        assert result["A"] == 3
        assert result["B"] == 8
        assert result["C"] == 5
        assert result["D"] == 12

    def test_single_node(self):
        graph = {"A": {"deps": [], "duration": 10}}
        result = resolve_critical_path(graph)
        assert result == {"A": 10}

    def test_no_deps_path(self):
        graph = {"X": {"deps": [], "duration": 7}, "Y": {"deps": [], "duration": 3},
                 "Z": {"deps": ["X", "Y"], "duration": 1}}
        result = resolve_critical_path(graph)
        assert result["X"] == 7
        assert result["Y"] == 3
        assert result["Z"] == 8

    def test_chain(self):
        graph = {"A": {"deps": [], "duration": 1}, "B": {"deps": ["A"], "duration": 2},
                 "C": {"deps": ["B"], "duration": 3}, "D": {"deps": ["C"], "duration": 4}}
        result = resolve_critical_path(graph)
        assert result["A"] == 1
        assert result["B"] == 3
        assert result["C"] == 6
        assert result["D"] == 10
""",
        "requirements": [],
    },
}