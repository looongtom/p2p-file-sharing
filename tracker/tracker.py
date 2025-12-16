# tracker/tracker.py
from __future__ import annotations

import os
import json
import time
import socket
from threading import Thread, Timer
from collections import defaultdict
from typing import Dict, Any, Tuple, List

from common.constants import (
    MODE_REGISTER, MODE_OWN, MODE_NEED, MODE_UPDATE, MODE_EXIT,
    DEFAULT_BUFFER_SIZE, DEFAULT_TRACKER_PORT, DEFAULT_TRACKER_HOST,
    DEFAULT_TRACKER_CHECK_INTERVAL
)
from common.protocol import decode_message, encode_message, get_advertised_endpoint


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


class Tracker:
    def __init__(self):
        self.tracker_host = os.getenv("TRACKER_HOST", DEFAULT_TRACKER_HOST)
        self.tracker_port = int(os.getenv("TRACKER_PORT", str(DEFAULT_TRACKER_PORT)))
        self.buffer_size = int(os.getenv("BUFFER_SIZE", str(DEFAULT_BUFFER_SIZE)))
        self.check_interval = int(os.getenv("TRACKER_TIME_INTERVAL", str(DEFAULT_TRACKER_CHECK_INTERVAL)))

        self.db_dir = os.getenv("TRACKER_DB_DIR", "tracker_db")
        os.makedirs(self.db_dir, exist_ok=True)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.tracker_host, self.tracker_port))

        self.file_owners_list = defaultdict(list)   # filename -> list[str json]
        self.send_freq_list = defaultdict(int)      # node_id -> int
        self.has_informed_tracker = defaultdict(bool)  # (node_id,(host,port))->bool

        self._load_db()
        self._next_call = time.time()

        print(f"[{_now()}][TRACKER] listening on {self.tracker_host}:{self.tracker_port}")

    def _db_paths(self):
        return (
            os.path.join(self.db_dir, "nodes.json"),
            os.path.join(self.db_dir, "files.json"),
        )

    def _load_db(self):
        nodes_path, files_path = self._db_paths()
        try:
            if os.path.exists(nodes_path):
                with open(nodes_path, "r", encoding="utf-8") as f:
                    nodes = json.load(f)
                for k, v in nodes.items():
                    if k.startswith("node"):
                        nid = int(k.replace("node", ""))
                        self.send_freq_list[nid] = int(v)

            if os.path.exists(files_path):
                with open(files_path, "r", encoding="utf-8") as f:
                    files = json.load(f)
                self.file_owners_list = defaultdict(list, files)
        except Exception as e:
            print(f"[{_now()}][TRACKER][WARN] failed loading db: {e}")

    def save_db_as_json(self):
        nodes_path, files_path = self._db_paths()
        nodes_dump = {f"node{k}": v for k, v in self.send_freq_list.items()}
        with open(nodes_path, "w", encoding="utf-8") as f:
            json.dump(nodes_dump, f, indent=2, sort_keys=True, ensure_ascii=False)
        with open(files_path, "w", encoding="utf-8") as f:
            json.dump(self.file_owners_list, f, indent=2, sort_keys=True, ensure_ascii=False)

    def add_file_owner(self, msg: Dict[str, Any], fallback_addr: Tuple[str, int]):
        ep = get_advertised_endpoint(msg, fallback_addr)
        entry = {"node_id": int(msg["node_id"]), "addr": [ep.host, ep.port]}
        filename = msg["filename"]

        self.file_owners_list[filename].append(json.dumps(entry, sort_keys=True))
        self.file_owners_list[filename] = list(set(self.file_owners_list[filename]))

        _ = self.send_freq_list[int(msg["node_id"])]

        print(f"[{_now()}][TRACKER] OWN: node {msg['node_id']} -> {filename} at {ep.host}:{ep.port}")
        self.save_db_as_json()

    def update_db(self, msg: Dict[str, Any]):
        nid = int(msg["node_id"])
        self.send_freq_list[nid] += 1
        print(f"[{_now()}][TRACKER] UPDATE: node {nid} freq={self.send_freq_list[nid]}")
        self.save_db_as_json()

    def search_file(self, msg: Dict[str, Any], reply_addr: Tuple[str, int]):
        filename = msg["filename"]
        nid = int(msg["node_id"])
        print(f"[{_now()}][TRACKER] NEED: node {nid} searching {filename}")

        matched_entries: List[Tuple[Dict[str, Any], int]] = []
        for json_entry in self.file_owners_list.get(filename, []):
            entry = json.loads(json_entry)
            owner_id = int(entry["node_id"])
            matched_entries.append((entry, int(self.send_freq_list.get(owner_id, 0))))

        matched_entries.sort(key=lambda x: x[1])

        resp = {
            "mode": "SEARCH_RESULT",
            "dest_node_id": nid,
            "filename": filename,
            "search_result": matched_entries,
        }
        self.sock.sendto(encode_message(resp), reply_addr)

    def remove_node(self, node_id: int, advertised_addr: Tuple[str, int]):
        entry = {"node_id": int(node_id), "addr": [advertised_addr[0], advertised_addr[1]]}
        entry_json = json.dumps(entry, sort_keys=True)

        self.send_freq_list.pop(int(node_id), None)
        self.has_informed_tracker.pop((int(node_id), advertised_addr), None)

        for fn in list(self.file_owners_list.keys()):
            owners = self.file_owners_list.get(fn, [])
            if entry_json in owners:
                owners.remove(entry_json)
            if not owners:
                self.file_owners_list.pop(fn, None)
            else:
                self.file_owners_list[fn] = owners

        print(f"[{_now()}][TRACKER] REMOVE: node {node_id} at {advertised_addr[0]}:{advertised_addr[1]}")
        self.save_db_as_json()

    def check_nodes_periodically(self, interval: int):
        alive, dead = set(), set()
        try:
            for node_key, has_informed in list(self.has_informed_tracker.items()):
                node_id, node_addr = node_key
                if has_informed:
                    self.has_informed_tracker[node_key] = False
                    alive.add(node_id)
                else:
                    dead.add(node_id)
                    self.remove_node(node_id=node_id, advertised_addr=node_addr)
        except RuntimeError:
            pass

        if alive or dead:
            print(f"[{_now()}][TRACKER] HEARTBEAT: alive={sorted(alive)} dead={sorted(dead)}")

        self._next_call = self._next_call + interval
        Timer(self._next_call - time.time(), self.check_nodes_periodically, args=(interval,)).start()

    def handle_node_request(self, data: bytes, addr: Tuple[str, int]):
        try:
            msg = decode_message(data)
        except Exception as e:
            print(f"[{_now()}][TRACKER][WARN] decode failed from {addr}: {e}")
            return

        mode = msg.get("mode")
        if mode is None:
            return

        advertised = get_advertised_endpoint(msg, addr).as_tuple()

        if mode == MODE_OWN and "filename" in msg and "node_id" in msg:
            self.add_file_owner(msg=msg, fallback_addr=addr)

        elif mode == MODE_NEED and "filename" in msg and "node_id" in msg:
            self.search_file(msg=msg, reply_addr=addr)

        elif mode == MODE_UPDATE and "node_id" in msg:
            self.update_db(msg=msg)

        elif mode == MODE_REGISTER and "node_id" in msg:
            self.has_informed_tracker[(int(msg["node_id"]), advertised)] = True

        elif mode == MODE_EXIT and "node_id" in msg:
            self.remove_node(node_id=int(msg["node_id"]), advertised_addr=advertised)
            print(f"[{_now()}][TRACKER] EXIT: node {msg['node_id']} requested exit")

    def listen(self):
        Thread(target=self.check_nodes_periodically, args=(self.check_interval,), daemon=True).start()
        while True:
            data, addr = self.sock.recvfrom(self.buffer_size)
            Thread(target=self.handle_node_request, args=(data, addr), daemon=True).start()

    def run(self):
        print(f"[{_now()}][TRACKER] started")
        self.listen()


if __name__ == "__main__":
    Tracker().run()
