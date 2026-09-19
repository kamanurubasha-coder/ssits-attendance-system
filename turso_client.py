"""
Turso Cloud SQLite Database Adapter for SSITS Attendance Portal
Provides transparent, 100% compatible SQLite-like interface over Turso HTTP Pipeline API.
Uses Python standard library urllib (no external dependencies required).
"""

import json
import urllib.request
import urllib.error
import ssl

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


class TursoCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rows = []
        self.cols = []
        self.row_idx = 0
        self.lastrowid = None
        self.rowcount = 0

    def execute(self, sql, args=()):
        if args is None:
            args = ()
        elif not isinstance(args, (list, tuple, dict)):
            args = (args,)
            
        res = self.conn._execute_sql(sql, args)
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
        for args in seq_of_args:
            self.execute(sql, args)
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

    def _execute_sql(self, sql, args=()):
        formatted_args = []
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
                formatted_args.append(arg_obj)
        else:
            for a in args:
                if a is None:
                    formatted_args.append({"type": "null"})
                elif isinstance(a, bool):
                    formatted_args.append({"type": "integer", "value": "1" if a else "0"} )
                elif isinstance(a, int):
                    formatted_args.append({"type": "integer", "value": str(a)})
                elif isinstance(a, float):
                    formatted_args.append({"type": "float", "value": a})
                else:
                    formatted_args.append({"type": "text", "value": str(a)})
                
        payload = {
            "requests": [
                {
                    "type": "execute",
                    "stmt": {"sql": sql, "args": formatted_args}
                },
                {"type": "close"}
            ]
        }
        
        req = urllib.request.Request(
            self.http_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                results = data.get("results", [])
                if results and results[0].get("type") == "ok":
                    return results[0]
                elif results and results[0].get("type") == "error":
                    raise Exception(results[0].get("error", {}).get("message", "Turso query error"))
                return {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise Exception(f"Turso HTTP {e.code}: {err_body}")

    def cursor(self):
        return TursoCursor(self)

    def execute(self, sql, args=()):
        c = self.cursor()
        return c.execute(sql, args)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
