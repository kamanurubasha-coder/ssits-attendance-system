"""
Turso Cloud SQLite Database Adapter for SSITS Attendance Portal
High-Performance Pooled Client with Keep-Alive & Pipeline Batching.
100% SQLite-compatible interface over Turso HTTP Pipeline API.
"""

import json
import ssl
import urllib.parse

# Try importing urllib3 for high-performance connection pooling
try:
    import urllib3
    _HTTP_POOL = urllib3.PoolManager(
        maxsize=15,
        timeout=urllib3.Timeout(connect=5.0, read=30.0),
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
        self._cols = cols
        self._values = tuple(values)
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        if key not in self:
            for k in self:
                if k.lower() == key.lower():
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

    def execute(self, sql, args=()):
        formatted_args = _format_args(args)
        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {"sql": sql, "args": formatted_args}
                }
            ]
        }
        
        results = self.conn._send_pipeline_payload(payload)
        if not results:
            self.rows = []
            return self

        res = results[0]
        if res.get("type") == "error":
            err_msg = res.get("error", {}).get("message", str(res))
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
        return self

    def executemany(self, sql, seq_of_args):
        """
        Executes a parameterized SQL query against multiple parameter tuples
        using batch pipelining for maximum speed.
        """
        arg_list = list(seq_of_args)
        if not arg_list:
            return self

        # Chunk into batches of 40 to avoid oversized HTTP requests
        batch_size = 40
        total_affected = 0
        last_id = None

        for i in range(0, len(arg_list), batch_size):
            chunk = arg_list[i:i + batch_size]
            requests = [
                {
                    "type": "execute",
                    "stmt": {"sql": sql, "args": _format_args(args)}
                }
                for args in chunk
            ]
            results = self.conn._send_pipeline_payload({"requests": requests})
            for r in results:
                if r.get("type") == "error":
                    err_msg = r.get("error", {}).get("message", str(r))
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
        parsed = urllib.parse.urlparse(self.http_url)
        self._host = parsed.netloc
        self._path = parsed.path

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
            import time
            for attempt in range(3):
                try:
                    resp = _HTTP_POOL.request(
                        "POST",
                        self.http_url,
                        body=json_data,
                        headers=headers
                    )
                    body_text = resp.data.decode('utf-8', errors='ignore')
                    if resp.status in [429, 502, 503, 504] or "capacity" in body_text.lower():
                        if attempt < 2:
                            time.sleep(0.6 * (attempt + 1))
                            continue
                    if resp.status != 200:
                        raise Exception(f"Turso HTTP {resp.status}: {body_text}")
                    data = json.loads(body_text)
                    return data.get("results", [])
                except Exception as e:
                    if attempt < 2:
                        time.sleep(0.6 * (attempt + 1))
                        continue
                    raise

        # Fallback: Persistent HTTPSConnection
        ssl_ctx = ssl.create_default_context()
        for attempt in range(2):
            try:
                if self._fallback_conn is None:
                    self._fallback_conn = http.client.HTTPSConnection(self._host, context=ssl_ctx, timeout=20)
                self._fallback_conn.request("POST", self._path, body=json_data, headers=headers)
                r = self._fallback_conn.getresponse()
                raw_body = r.read().decode('utf-8')
                if r.status != 200:
                    raise Exception(f"Turso HTTP {r.status}: {raw_body}")
                data = json.loads(raw_body)
                return data.get("results", [])
            except Exception:
                try:
                    if self._fallback_conn:
                        self._fallback_conn.close()
                except Exception:
                    pass
                self._fallback_conn = None
                if attempt == 1:
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
        pass

    def rollback(self):
        pass

    def close(self):
        if self._fallback_conn is not None:
            try:
                self._fallback_conn.close()
            except Exception:
                pass
            self._fallback_conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
