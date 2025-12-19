import os, socket, threading, time, json
from typing import Dict, Any
from common.constants import BUFFER_SIZE, TRACKER_PORT, MODE_OWN, MODE_NEED, MODE_LIST, MODE_FIND_BY_NAME, MODE_REGISTER, MODE_EXIT
from common.utils import jencode, jdecode

class Tracker:
    def __init__(self):
        self.addr = ("0.0.0.0", TRACKER_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.addr)
        self.lock = threading.Lock()

        # swarm: infohash -> {meta:{...}, owners:[{node_id,host,port}], last_seen:{node_id:ts}}
        self.swarm: Dict[str, Dict[str, Any]] = {}
        self.ttl = int(os.getenv("TRACKER_TTL_SEC", "60"))
        self.db_dir = os.getenv("TRACKER_DB_DIR", "/app/tracker_db")
        os.makedirs(self.db_dir, exist_ok=True)

    def _log(self, msg: str):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"{ts} [TRACKER] {msg}", flush=True)

    def _save_db(self):
        try:
            with self.lock:
                path = os.path.join(self.db_dir, "swarm.json")
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fp:
                    json.dump(self.swarm, fp, ensure_ascii=False, indent=2)
                os.replace(tmp, path)
        except Exception as e:
            self._log(f"save db failed: {e}")

    def _gc_loop(self):
        while True:
            time.sleep(10)
            now = time.time()
            changed = False
            with self.lock:
                for ih in list(self.swarm.keys()):
                    sw = self.swarm[ih]
                    last_seen = sw.get("last_seen", {})
                    owners = sw.get("owners", [])
                    alive = []
                    for o in owners:
                        nid = str(o.get("node_id"))
                        ts = last_seen.get(nid, 0)
                        if now - ts <= self.ttl:
                            alive.append(o)
                    if len(alive) != len(owners):
                        sw["owners"] = alive
                        changed = True
                    if not sw["owners"]:
                        self.swarm.pop(ih, None)
                        changed = True
            if changed:
                self._save_db()

    def handle(self, msg: Dict[str, Any], addr):
        mode = msg.get("mode")

        if mode == MODE_REGISTER:
            ih = msg.get("infohash")
            nid = str(msg.get("node_id"))
            with self.lock:
                if ih and ih in self.swarm:
                    self.swarm[ih].setdefault("last_seen", {})[nid] = time.time()
            return

        if mode == MODE_OWN:
            ih = msg["infohash"]
            meta = msg["meta"]
            owner = {"node_id": msg["node_id"], "host": msg["host"], "port": msg["port"]}
            with self.lock:
                sw = self.swarm.setdefault(ih, {"meta": meta, "owners": [], "last_seen": {}})
                sw["meta"] = meta
                if owner not in sw["owners"]:
                    sw["owners"].append(owner)
                sw["last_seen"][str(owner["node_id"])] = time.time()
            self._log(f"OWN ih={ih[:10]}.. file={meta.get('filename')} owner={owner['host']}:{owner['port']}")
            self._save_db()
            return

        if mode == MODE_NEED:
            ih = msg.get("infohash")
            with self.lock:
                sw = self.swarm.get(ih)
                if not sw:
                    resp = {"ok": False, "error": "NOT_FOUND", "infohash": ih}
                else:
                    resp = {"ok": True, "infohash": ih, "meta": sw["meta"], "peers": sw["owners"]}
            self.sock.sendto(jencode(resp), addr)
            return

        if mode == MODE_LIST:
            with self.lock:
                items = []
                for ih, sw in self.swarm.items():
                    meta = sw.get("meta", {})
                    items.append({
                        "infohash": ih,
                        "filename": meta.get("filename"),
                        "size": meta.get("size"),
                        "pieces": len(meta.get("piece_hashes", []) or []),
                        "peers": len(sw.get("owners", []) or []),
                    })
            self.sock.sendto(jencode({"ok": True, "items": items}), addr)
            return

        if mode == MODE_FIND_BY_NAME:
            name = msg.get("filename")
            with self.lock:
                matches = []
                for ih, sw in self.swarm.items():
                    meta = sw.get("meta", {})
                    if meta.get("filename") == name:
                        matches.append({
                            "infohash": ih,
                            "filename": meta.get("filename"),
                            "size": meta.get("size"),
                            "pieces": len(meta.get("piece_hashes", []) or []),
                            "peers": len(sw.get("owners", []) or []),
                        })
            if not matches:
                resp = {"ok": False, "error": "NOT_FOUND", "filename": name, "matches": []}
            elif len(matches) == 1:
                resp = {"ok": True, "filename": name, "match": matches[0]}
            else:
                resp = {"ok": False, "error": "AMBIGUOUS", "filename": name, "matches": matches}
            self.sock.sendto(jencode(resp), addr)
            return

        if mode == MODE_EXIT:
            nid = msg.get("node_id")
            ih = msg.get("infohash")
            with self.lock:
                if ih and ih in self.swarm:
                    sw = self.swarm[ih]
                    sw["owners"] = [o for o in sw.get("owners", []) if o.get("node_id") != nid]
                    sw.get("last_seen", {}).pop(str(nid), None)
                    if not sw["owners"]:
                        self.swarm.pop(ih, None)
            self._log(f"EXIT node={nid} ih={str(ih)[:10]}..")
            self._save_db()
            return

    def serve(self):
        self._log(f"listening udp {self.addr[0]}:{self.addr[1]}")
        threading.Thread(target=self._gc_loop, daemon=True).start()
        while True:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            try:
                msg = jdecode(data)
            except Exception:
                continue
            threading.Thread(target=self.handle, args=(msg, addr), daemon=True).start()

if __name__ == "__main__":
    Tracker().serve()
