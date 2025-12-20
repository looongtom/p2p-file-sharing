import os
import re
import json
import time
import socket
import threading
from typing import Dict, Any, Tuple, Optional
from flask import Flask, request, jsonify

from common.constants import (
    TRACKER_HOST,
    TRACKER_PORT,
    ADVERTISE_HOST,
    NODE_PORT,
    BUFFER_SIZE,
    PIECE_SIZE,
    BLOCK_SIZE,
    HEARTBEAT_SEC,
    SEED_DIR,
    DOWNLOAD_DIR,
    MODE_OWN,
    MODE_NEED,
    MODE_LIST,
    MODE_FIND_BY_NAME,
    MODE_REGISTER,
    MODE_EXIT,
    T_GET_PIECE,
    T_PIECE_BLOCK,
)
from common.utils import jencode, jdecode, sha256_hex, b64e, b64d


class Node:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.seed_dir = SEED_DIR
        self.download_dir = DOWNLOAD_DIR

        self.tracker = (TRACKER_HOST, TRACKER_PORT)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", NODE_PORT))
        self.sock.settimeout(0.5)

        # download sessions: infohash -> state dict
        self.dl_lock = threading.Lock()
        self.downloads: Dict[str, Dict[str, Any]] = {}

        # keep track of seeded torrents so tracker TTL won't drop them (optional but useful)
        self.seeding = set()

        self._log(f"bind=0.0.0.0:{NODE_PORT} advertise={ADVERTISE_HOST}:{NODE_PORT}")
        self._log(f"tracker={TRACKER_HOST}:{TRACKER_PORT} piece_size={PIECE_SIZE} block_size={BLOCK_SIZE}")

        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _log(self, msg: str) -> None:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"{ts} [NODE {self.node_id}] {msg}", flush=True)

    # ---------------- Tracker calls ----------------
    def _send_tracker(self, msg: Dict[str, Any]) -> None:
        self.sock.sendto(jencode(msg), self.tracker)

    def _tracker_call(self, req: Dict[str, Any]) -> Dict[str, Any]:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3.0)
        s.sendto(jencode(req), self.tracker)
        data, _ = s.recvfrom(BUFFER_SIZE)
        s.close()
        return jdecode(data)

    def _tracker_need(self, infohash: str) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_NEED, "node_id": self.node_id, "infohash": infohash})

    def _tracker_list(self) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_LIST, "node_id": self.node_id})

    def _tracker_find_by_name(self, filename: str) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_FIND_BY_NAME, "node_id": self.node_id, "filename": filename})

    def _heartbeat_loop(self) -> None:
        """
        Heartbeat/REGISTER for both:
        - active downloads
        - active seeding torrents
        This prevents tracker TTL from dropping owners.
        """
        while True:
            time.sleep(HEARTBEAT_SEC)
            with self.dl_lock:
                active = set(self.downloads.keys()) | set(self.seeding)
            for ih in active:
                self._send_tracker({"mode": MODE_REGISTER, "node_id": self.node_id, "infohash": ih})

    # ---------------- Meta / Own ----------------
    def _build_meta(self, filepath: str) -> Tuple[str, Dict[str, Any]]:
        size = os.path.getsize(filepath)
        piece_hashes = []
        with open(filepath, "rb") as fp:
            while True:
                piece = fp.read(PIECE_SIZE)
                if not piece:
                    break
                piece_hashes.append(sha256_hex(piece))
        meta = {
            "filename": os.path.basename(filepath),
            "size": size,
            "piece_size": PIECE_SIZE,
            "piece_hashes": piece_hashes,
        }
        infohash = sha256_hex(json.dumps(meta, sort_keys=True).encode("utf-8"))
        return infohash, meta

    def own_file(self, filename: str) -> bool:
        path = os.path.join("/app", self.seed_dir, filename)
        if not os.path.exists(path):
            self._log(f"File not found (seed): {path}")
            return False

        ih, meta = self._build_meta(path)
        self._send_tracker(
            {
                "mode": MODE_OWN,
                "node_id": self.node_id,
                "host": ADVERTISE_HOST,
                "port": NODE_PORT,
                "infohash": ih,
                "meta": meta,
            }
        )
        self.seeding.add(ih)
        self._log(f"OWN announced: {filename} ih={ih[:10]}.. size={meta['size']} pieces={len(meta['piece_hashes'])}")
        return True

    # ---------------- Resume helpers ----------------
    def _resume_paths(self, filename: str) -> Tuple[str, str]:
        rp = os.path.join("/app", self.download_dir, f"{filename}.resume.json")
        pp = os.path.join("/app", self.download_dir, f"{filename}.part")
        return rp, pp

    def _save_resume(self, st: Dict[str, Any]) -> None:
        """
        Persist only JSON-serializable fields.
        DO NOT include st['buffers'] (contains bytes).
        """
        rp = st["resume_path"]
        tmp = rp + ".tmp"
        safe = {
            "infohash": st.get("infohash"),
            "filename": st.get("filename"),
            "size": st.get("size"),
            "piece_size": st.get("piece_size"),
            "piece_hashes": st.get("piece_hashes"),
            "completed": st.get("completed"),
            "done": st.get("done"),
            "total_pieces": st.get("total_pieces"),
        }
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(safe, fp, ensure_ascii=False, indent=2)
        os.replace(tmp, rp)

    def _load_resume(self, filename: str) -> Optional[Dict[str, Any]]:
        rp, pp = self._resume_paths(filename)
        if not os.path.exists(rp):
            return None
        with open(rp, "r", encoding="utf-8") as fp:
            st = json.load(fp)
        st["resume_path"] = rp
        st["part_path"] = pp
        st["buffers"] = {}
        return st

    def _ensure_partfile(self, part_path: str, total_size: int) -> None:
        os.makedirs(os.path.dirname(part_path), exist_ok=True)
        if not os.path.exists(part_path):
            with open(part_path, "wb") as fp:
                fp.truncate(total_size)

    def _write_piece(self, st: Dict[str, Any], idx: int, data: bytes) -> None:
        with open(st["part_path"], "r+b") as fp:
            fp.seek(idx * st["piece_size"])
            fp.write(data)

    def _finalize(self, st: Dict[str, Any]) -> None:
        out = os.path.join("/app", self.download_dir, st["filename"])
        with open(st["part_path"], "rb+") as fp:
            fp.truncate(st["size"])
        os.replace(st["part_path"], out)
        try:
            os.remove(st["resume_path"])
        except Exception:
            pass
        self._log(f"DOWNLOAD COMPLETE: {st['filename']} saved to {out}")

    # ---------------- Peer transfer (UDP blocks) ----------------
    def _send_peer(self, msg: Dict[str, Any], addr: Tuple[str, int]) -> None:
        self.sock.sendto(jencode(msg), addr)

    def _find_seed_file_by_infohash(self, ih: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Demo implementation: scan seed_dir to find file whose meta infohash matches.
        """
        seed_root = os.path.join("/app", self.seed_dir)
        if not os.path.exists(seed_root):
            return None

        for fn in os.listdir(seed_root):
            fp = os.path.join(seed_root, fn)
            if not os.path.isfile(fp):
                continue
            try:
                ih2, meta = self._build_meta(fp)
            except Exception:
                continue
            if ih2 == ih:
                return fp, meta
        return None

    def _serve_piece(self, ih: str, idx: int, addr: Tuple[str, int]) -> None:
        found = self._find_seed_file_by_infohash(ih)
        if not found:
            return
        fp, meta = found

        # optional server-side log
        # self._log(f"serve piece {idx} to {addr[0]}:{addr[1]}")

        with open(fp, "rb") as f:
            f.seek(idx * meta["piece_size"])
            piece = f.read(meta["piece_size"])

        total_blocks = (len(piece) + BLOCK_SIZE - 1) // BLOCK_SIZE if piece else 0
        for b in range(total_blocks):
            blk = piece[b * BLOCK_SIZE : (b + 1) * BLOCK_SIZE]
            self._send_peer(
                {
                    "type": T_PIECE_BLOCK,
                    "ih": ih,
                    "piece": idx,
                    "block": b,
                    "total_blocks": total_blocks,
                    "data": b64e(blk),
                },
                addr,
            )

    def _recv_loop(self) -> None:
        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except Exception:
                continue

            try:
                msg = jdecode(data)
            except Exception:
                continue

            t = msg.get("type")
            if t == T_GET_PIECE:
                ih = msg.get("ih")
                idx = int(msg.get("piece", -1))
                if not ih or idx < 0:
                    continue
                threading.Thread(target=self._serve_piece, args=(ih, idx, addr), daemon=True).start()
                continue

            if t == T_PIECE_BLOCK:
                ih = msg.get("ih")
                if not ih:
                    continue
                p = int(msg.get("piece", -1))
                b = int(msg.get("block", -1))
                tb = int(msg.get("total_blocks", 0))
                if p < 0 or b < 0 or tb <= 0:
                    continue
                try:
                    chunk = b64d(msg.get("data", ""))
                except Exception:
                    continue

                with self.dl_lock:
                    st = self.downloads.get(ih)
                    if not st:
                        continue
                    buf = st["buffers"].setdefault(p, {"total": tb, "blocks": {}})
                    buf["total"] = tb
                    buf["blocks"][b] = chunk

    def _piece_worker(self, ih: str, peer: Dict[str, Any], q) -> None:
        """
        Worker pinned to a single peer.
        Critical fix:
        - if a piece times out or hash mismatch -> re-queue the piece (do not lose it)
        """
        import queue as _q

        addr = (peer["host"], int(peer["port"]))

        while True:
            try:
                idx = q.get_nowait()
            except _q.Empty:
                return

            success = False

            with self.dl_lock:
                st = self.downloads[ih]
                if st["completed"][idx] == 1:
                    q.task_done()
                    continue
                st["buffers"].pop(idx, None)

            # log request
            self._log(
                f"request piece {idx} from node {peer.get('node_id','?')} @ {peer['host']}:{peer['port']}"
            )

            # request piece
            self._send_peer({"type": T_GET_PIECE, "ih": ih, "piece": idx}, addr)

            deadline = time.time() + 5.0
            while time.time() < deadline:
                time.sleep(0.05)

                with self.dl_lock:
                    st = self.downloads[ih]
                    buf = st["buffers"].get(idx)
                    if not buf:
                        continue
                    if len(buf["blocks"]) != buf["total"]:
                        continue

                    blocks = buf["blocks"]
                    try:
                        data = b"".join(blocks[i] for i in range(buf["total"]))
                    except KeyError:
                        continue

                    if sha256_hex(data) != st["piece_hashes"][idx]:
                        self._log(f"piece {idx} hash mismatch -> requeue")
                        st["buffers"].pop(idx, None)
                        break

                    # write piece
                    self._write_piece(st, idx, data)
                    st["completed"][idx] = 1
                    st["done"] += 1
                    self._save_resume(st)

                    # log completed
                    self._log(
                        f"completed piece {idx} from node {peer.get('node_id','?')} @ {peer['host']}:{peer['port']}"
                    )

                    if st["done"] % 5 == 0 or st["done"] == st["total_pieces"]:
                        self._log(f"progress {st['done']}/{st['total_pieces']} pieces")

                    st["buffers"].pop(idx, None)
                    success = True
                    break

            if not success:
                # timed out (or mismatch) -> re-queue so another worker/another round can fetch it
                q.put(idx)

            q.task_done()

    # ---------------- Download ----------------
    def download_by_infohash(self, ih: str) -> None:
        resp = self._tracker_need(ih)
        if not resp.get("ok"):
            self._log(f"tracker says NOT_FOUND ih={ih[:10]}..")
            return

        meta = resp["meta"]
        peers = resp.get("peers", [])
        if not peers:
            self._log("no peers available")
            return

        filename = meta["filename"]
        size = int(meta["size"])
        piece_hashes = meta["piece_hashes"]
        total_pieces = len(piece_hashes)

        st = self._load_resume(filename)
        if st and st.get("infohash") == ih and st.get("piece_size") == PIECE_SIZE:
            st["piece_hashes"] = piece_hashes
            st["total_pieces"] = total_pieces
            st["done"] = int(sum(st["completed"]))
            self._log(f"resume found: {filename} done={st['done']}/{total_pieces}")
        else:
            rp, pp = self._resume_paths(filename)
            st = {
                "infohash": ih,
                "filename": filename,
                "size": size,
                "piece_size": PIECE_SIZE,
                "piece_hashes": piece_hashes,
                "completed": [0] * total_pieces,
                "done": 0,
                "total_pieces": total_pieces,
                "resume_path": rp,
                "part_path": pp,
                "buffers": {},
            }
            self._ensure_partfile(pp, size)
            self._save_resume(st)

        self._ensure_partfile(st["part_path"], size)

        with self.dl_lock:
            self.downloads[ih] = st

        self._log(f"META ok: {filename} size={size} pieces={total_pieces} peers={len(peers)} ih={ih[:10]}..")

        if st["done"] >= total_pieces:
            self._finalize(st)
            return

        import queue

        q = queue.Queue()
        for i in range(total_pieces):
            if st["completed"][i] == 0:
                q.put(i)

        # one worker per peer
        for peer in peers:
            threading.Thread(target=self._piece_worker, args=(ih, peer, q), daemon=True).start()

        q.join()

        with self.dl_lock:
            st2 = self.downloads.get(ih)
            if st2 and int(sum(st2["completed"])) == total_pieces:
                self._finalize(st2)
            else:
                missing = 0
                if st2:
                    missing = st2["total_pieces"] - int(sum(st2["completed"]))
                self._log(f"download finished but missing {missing} pieces (will resume on next run)")

    def download_by_filename(self, filename: str) -> None:
        resp = self._tracker_find_by_name(filename)
        if not resp.get("ok"):
            err = resp.get("error")
            if err == "AMBIGUOUS":
                self._log(f"AMBIGUOUS filename '{filename}'. Use infohash instead. Matches:")
                for m in resp.get("matches", []):
                    self._log(f"  {m.get('infohash','')[:10]}.. size={m.get('size')} peers={m.get('peers')}")
            else:
                self._log(f"File not found on tracker: {filename}")
            return
        ih = resp["match"]["infohash"]
        self.download_by_infohash(ih)

    # ---------------- CLI ----------------
    def start_interactive(self) -> None:
        self._log("Commands:")
        self._log("  torrent -setMode send <filename>")
        self._log("  torrent list")
        self._log("  torrent -setMode download <filename|infohash>")
        self._log("  exit")

        while True:
            try:
                cmd = input(f"[NODE {self.node_id}]> ").strip()
            except EOFError:
                time.sleep(0.5)
                continue

            if not cmd:
                continue

            parts = cmd.split()

            if parts[:3] == ["torrent", "-setMode", "send"] and len(parts) >= 4:
                self.own_file(parts[3])
                continue

            if parts[:2] == ["torrent", "list"]:
                resp = self._tracker_list()
                if not resp.get("ok"):
                    self._log("tracker list failed")
                    continue
                items = resp.get("items", [])
                if not items:
                    self._log("tracker has no files")
                    continue
                self._log("Files on tracker:")
                for it in items:
                    self._log(
                        f"  {it.get('filename')}  size={it.get('size')}  peers={it.get('peers')}  ih={str(it.get('infohash'))[:10]}.."
                    )
                continue

            if parts[:3] == ["torrent", "-setMode", "download"] and len(parts) >= 4:
                arg = parts[3]
                if re.fullmatch(r"[0-9a-fA-F]{16,}", arg or ""):
                    threading.Thread(target=self.download_by_infohash, args=(arg.lower(),), daemon=True).start()
                else:
                    threading.Thread(target=self.download_by_filename, args=(arg,), daemon=True).start()
                continue

            if parts[0] == "exit":
                with self.dl_lock:
                    for ih in list(self.downloads.keys()):
                        self._send_tracker({"mode": MODE_EXIT, "node_id": self.node_id, "infohash": ih})
                self._log("bye")
                return

            self._log("unknown command")


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("-node_id", type=int, required=True)
    args = p.parse_args()
    Node(args.node_id).start_interactive()


if __name__ == "__main__":
    main()
