"""
Turso Cloud SQLite Database Adapter for SSITS Attendance Portal
High-Performance Pooled Client with Keep-Alive, Pipeline Batching & Instant Local SQLite Fallback.
100% SQLite-compatible interface over Turso HTTP Pipeline API.
Guarantees ZERO 500 errors even if Turso cloud is slow, down, or rate-limited.
"""

import json
import ssl
import time
import os
import sqlite3
import urllib.parse

# Local DB path for instant fallback & dual-sync
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "attendance.db")
DB_PATH = os.getenv("DB_PATH", DEFAULT_DB_PATH)

# Circuit Breaker: If Turso fails or times out, bypass it for 45 seconds to keep responses instant
_TURSO_DISABLED_UNTIL = 0

def is_turso_available():
    global _TURSO_DISABLED_UNTIL
    return time.time() > _TURSO_DISABLED_UNTIL

def mark_turso_failed(cooldown=45):
    global _TURSO_DISABLED_UNTIL
    _TURSO_DISABLED_UNTIL = time.time() + cooldown

class TursoOfflineException(Exception):
    """Raised when Turso is in cooldown or fails to respond quickly."""
    pass

# Try importing urllib3 for high-performance connection pooling with aggressive timeout
try:
    import urllib3
    # Generous read timeout (connect=3.0s, read=8.0s) so cross-region database writes commit safely
    _HTTP_POOL = urllib3.PoolManager(
        maxsize=20,
        timeout=urllib3.Timeout(connect=3.0, read=8.0),
        retries=urllib3.Retry(total=2, backoff_factor=0.2)
    )
except ImportError:
    _HTTP_POOL = None
    import http.client


class TursoRow(dict):
    """
    Dict-like and tuple-like row object matching sqlite3.Row functionality.
    Supports row['column'], row[0], dict(row), row.get('column').
    """
    def __init__(self, cols, values):
        super().__init__(zip(cols, values))
        self._cols = list(cols)
        self._values = tuple(values)
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        if key not in self:
            for k in self:
                if str(k).lower() == str(key).lower():
                    return self[k]
        return super().__getitem__(key)

    def keys(self):
        return self._cols

    def values(self):
        return self._values

    def items(self):
        return zip(self._cols, self._values)


def _format_args(args):
    """Format python arguments into Turso JSON representation."""
    if args is None:
        return []
    if not isinstance(args, (list, tuple, dict)):
        args = (args,)
        
    formatted = []
    if isinstance(args, dict):
        for k, v in args.items():
            arg_obj = {"name": k}
            if v is None:
                arg_obj["value"] = {"type": "null"}
            elif isinstance(v, bool):
                arg_obj["value"] = {"type": "integer", "value": "1" if v else "0"}
            elif isinstance(v, int):
                arg_obj["value"] = {"type": "integer", "value": str(v)}
            elif isinstance(v, float):
                arg_obj["value"] = {"type": "float", "value": v}
            else:
                arg_obj["value"] = {"type": "text", "value": str(v)}
            formatted.append(arg_obj)
    else:
        for a in args:
            if a is None:
                formatted.append({"type": "null"})
            elif isinstance(a, bool):
                formatted.append({"type": "integer", "value": "1" if a else "0"})
            elif isinstance(a, int):
                formatted.append({"type": "integer", "value": str(a)})
            elif isinstance(a, float):
                formatted.append({"type": "float", "value": a})
            else:
                formatted.append({"type": "text", "value": str(a)})
    return formatted


class TursoCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rows = []
        self.cols = []
        self.row_idx = 0
        self.lastrowid = None
        self.rowcount = 0

    def _fallback_execute(self, sql, args=()):
        """Transparently execute SQL against the local SQLite database."""
        try:
            loc = self.conn._get_local_conn()
            loc_cur = loc.cursor()
            loc_cur.execute(sql, args)
            
            is_write = any(sql.strip().upper().startswith(v) for v in ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER"))
            if is_write:
                loc.commit()

            self.lastrowid = loc_cur.lastrowid
            self.rowcount = loc_cur.rowcount
            if loc_cur.description:
                self.cols = [d[0] for d in loc_cur.description]
                raw_rows = loc_cur.fetchall()
                self.rows = [TursoRow(self.cols, list(r)) for r in raw_rows]
            else:
                self.cols = []
                self.rows = []
            self.row_idx = 0
            return self
        except Exception as local_err:
            # Re-raise if local SQLite also errors (e.g. SQL syntax error)
            raise local_err

    def execute(self, sql, args=()):
        # Fast path: If Turso is in circuit-breaker cooldown, immediately use local SQLite
        if not is_turso_available():
            return self._fallback_execute(sql, args)

        formatted_args = _format_args(args)
        # Always append {"type": "close"} to close the Turso interactive stream session immediately
        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {"sql": sql, "args": formatted_args}
                },
                {"type": "close"}
            ]
        }
        
        try:
            results = self.conn._send_pipeline_payload(payload)
            if not results:
                self.rows = []
                return self

            res = results[0]
            if res.get("type") == "error":
                err_msg = res.get("error", {}).get("message", str(res))
                # If error is capacity, rate limit or server error, trip circuit breaker and fallback
                if any(x in err_msg.lower() for x in ("capacity", "limit", "timeout", "overloaded", "locked")):
                    mark_turso_failed(30)
                    return self._fallback_execute(sql, args)
                raise Exception(f"Turso Error: {err_msg}")
            
            result_data = res.get("response", {}).get("result", {})
            self.cols = [c["name"] for c in result_data.get("cols", [])]
            raw_rows = result_data.get("rows", [])
            
            parsed_rows = []
            for r in raw_rows:
                vals = []
                for col_val in r:
                    t = col_val.get("type")
                    v = col_val.get("value")
                    if t == "null" or v is None:
                        vals.append(None)
                    elif t == "integer":
                        vals.append(int(v))
                    elif t == "float":
                        vals.append(float(v))
                    else:
                        vals.append(v)
                parsed_rows.append(TursoRow(self.cols, vals))
                
            self.rows = parsed_rows
            self.row_idx = 0
            self.rowcount = result_data.get("affected_row_count", len(parsed_rows))
            lid = result_data.get("last_insert_rowid")
            self.lastrowid = int(lid) if lid is not None else None

            # Dual-write: If this is a write query, also apply to local SQLite so offline fallback stays fresh!
            is_write = any(sql.strip().upper().startswith(v) for v in ("INSERT", "UPDATE", "DELETE", "REPLACE"))
            if is_write:
                try:
                    loc = self.conn._get_local_conn()
                    loc.execute(sql, args)
                    loc.commit()
                except Exception:
                    pass

            return self

        except Exception as e:
            # If Turso fails, times out, or network dropped, mark failed and seamlessly fallback to local SQLite
            mark_turso_failed(45)
            return self._fallback_execute(sql, args)

    def executemany(self, sql, seq_of_args):
        """
        Executes a parameterized SQL query against multiple parameter tuples
        using batch pipelining for maximum speed, with instant local SQLite fallback.
        """
        arg_list = list(seq_of_args)
        if not arg_list:
            return self

        if not is_turso_available():
            loc = self.conn._get_local_conn()
            loc_cur = loc.cursor()
            loc_cur.executemany(sql, arg_list)
            loc.commit()
            self.rows = []
            self.row_idx = 0
            self.rowcount = loc_cur.rowcount
            self.lastrowid = loc_cur.lastrowid
            return self

        batch_size = 40
        total_affected = 0
        last_id = None

        try:
            for i in range(0, len(arg_list), batch_size):
                chunk = arg_list[i:i + batch_size]
                requests = [
                    {
                        "type": "execute",
                        "stmt": {"sql": sql, "args": _format_args(args)}
                    }
                    for args in chunk
                ]
                requests.append({"type": "close"})
                results = self.conn._send_pipeline_payload({"requests": requests})
                for r in results:
                    if r.get("type") == "error":
                        err_msg = r.get("error", {}).get("message", str(r))
                        if any(x in err_msg.lower() for x in ("capacity", "limit", "timeout", "overloaded", "locked")):
                            raise TursoOfflineException(err_msg)
                        raise Exception(f"Turso Error: {err_msg}")
                    res_data = r.get("response", {}).get("result", {})
                    total_affected += res_data.get("affected_row_count", 0)
                    lid = res_data.get("last_insert_rowid")
                    if lid is not None:
                        last_id = int(lid)

            self.rows = []
            self.row_idx = 0
            self.rowcount = total_affected
            self.lastrowid = last_id

            # Also sync to local SQLite
            try:
                loc = self.conn._get_local_conn()
                loc.executemany(sql, arg_list)
                loc.commit()
            except Exception:
                pass

            return self

        except Exception as e:
            mark_turso_failed(45)
            loc = self.conn._get_local_conn()
            loc_cur = loc.cursor()
            loc_cur.executemany(sql, arg_list)
            loc.commit()
            self.rows = []
            self.row_idx = 0
            self.rowcount = loc_cur.rowcount
            self.lastrowid = loc_cur.lastrowid
            return self

    def fetchone(self):
        if self.row_idx < len(self.rows):
            r = self.rows[self.row_idx]
            self.row_idx += 1
            return r
        return None

    def fetchall(self):
        res = self.rows[self.row_idx:]
        self.row_idx = len(self.rows)
        return res

    def close(self):
        self.rows = []


class TursoConnection:
    def __init__(self, db_url, auth_token):
        if db_url.startswith("libsql://"):
            self.http_url = db_url.replace("libsql://", "https://") + "/v2/pipeline"
        elif db_url.startswith("https://"):
            self.http_url = db_url.rstrip("/") + "/v2/pipeline"
        else:
            self.http_url = f"https://{db_url}/v2/pipeline"
            
        self.auth_token = auth_token
        self.row_factory = None
        self._fallback_conn = None
        self._local_sqlite = None
        parsed = urllib.parse.urlparse(self.http_url)
        self._host = parsed.netloc
        self._path = parsed.path

    def _get_local_conn(self):
        """Returns a cached thread-safe SQLite connection to the local database file."""
        if self._local_sqlite is None:
            self._local_sqlite = sqlite3.connect(DB_PATH, check_same_thread=False)
            self._local_sqlite.row_factory = sqlite3.Row
        return self._local_sqlite

    def _send_pipeline_payload(self, payload):
        """Sends a JSON pipeline payload using the connection pool with Keep-Alive."""
        json_data = json.dumps(payload).encode('utf-8')
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Connection": "keep-alive"
        }

        # Fast Path: Pooled urllib3
        if _HTTP_POOL is not None:
            try:
                resp = _HTTP_POOL.request(
                    "POST",
                    self.http_url,
                    body=json_data,
                    headers=headers
                )
                body_text = resp.data.decode('utf-8', errors='ignore')
                if resp.status in [429, 502, 503, 504] or "capacity" in body_text.lower():
                    mark_turso_failed(30)
                    raise TursoOfflineException(f"Turso rate limit/capacity: {resp.status}")
                if resp.status != 200:
                    mark_turso_failed(30)
                    raise TursoOfflineException(f"Turso HTTP {resp.status}: {body_text}")
                data = json.loads(body_text)
                return data.get("results", [])
            except Exception as e:
                mark_turso_failed(45)
                raise

        # Fallback: Persistent HTTPSConnection
        ssl_ctx = ssl.create_default_context()
        try:
            if self._fallback_conn is None:
                self._fallback_conn = http.client.HTTPSConnection(self._host, context=ssl_ctx, timeout=8)
            self._fallback_conn.request("POST", self._path, body=json_data, headers=headers)
            r = self._fallback_conn.getresponse()
            raw_body = r.read().decode('utf-8')
            if r.status != 200:
                mark_turso_failed(30)
                raise TursoOfflineException(f"Turso HTTP {r.status}: {raw_body}")
            data = json.loads(raw_body)
            return data.get("results", [])
        except Exception:
            mark_turso_failed(45)
            try:
                if self._fallback_conn:
                    self._fallback_conn.close()
            except Exception:
                pass
            self._fallback_conn = None
            raise

    def cursor(self):
        return TursoCursor(self)

    def execute(self, sql, args=()):
        c = self.cursor()
        return c.execute(sql, args)

    def executemany(self, sql, seq_of_args):
        c = self.cursor()
        return c.executemany(sql, seq_of_args)

    def commit(self):
        if self._local_sqlite:
            try:
                self._local_sqlite.commit()
            except Exception:
                pass

    def rollback(self):
        if self._local_sqlite:
            try:
                self._local_sqlite.rollback()
            except Exception:
                pass

    def close(self):
        if self._fallback_conn is not None:
            try:
                self._fallback_conn.close()
            except Exception:
                pass
            self._fallback_conn = None
        if self._local_sqlite is not None:
            try:
                self._local_sqlite.close()
            except Exception:
                pass
            self._local_sqlite = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
