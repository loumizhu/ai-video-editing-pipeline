"""Persistent FilmCraft engine session over `filmcraft-cli mcp` (stdio JSON-RPC). Returns command results
(clip ids, layer bounds) so multi-step graphics can be built interactively, then saved once."""
import json, subprocess

FC = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"


class FCSession:
    def __init__(self, project):
        self.p = subprocess.Popen([FC, "--project", project, "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self.i = 0
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "pipeline", "version": "1"}})
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self.i += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params}) + "\n")
        self.p.stdin.flush()
        while True:
            msg = json.loads(self.p.stdout.readline())
            if msg.get("id") == self.i:
                return msg

    def tool(self, name, args=None):
        r = self._rpc("tools/call", {"name": name, "arguments": args or {}})
        if "error" in r:
            raise RuntimeError(f"{name}: {r['error']}")
        res = r["result"]
        txt = "".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError"):
            raise RuntimeError(f"{name} {json.dumps(args)[:300]}: {txt[:500]}")
        try:
            return json.loads(txt)
        except Exception:
            return txt

    def run(self, cid, params=None):
        return self.tool("command_run", {"id": cid, "params": params or {}})

    def batch(self, steps):
        return self.tool("command_batch", {"steps": [{"id": a, "params": b} for a, b in steps]})

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass
