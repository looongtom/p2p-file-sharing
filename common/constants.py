import os

TRACKER_HOST = os.getenv("TRACKER_HOST", "tracker")
TRACKER_PORT = int(os.getenv("TRACKER_PORT", "12345"))

ADVERTISE_HOST = os.getenv("ADVERTISE_HOST", "peer1")
NODE_PORT = int(os.getenv("NODE_PORT", "20001"))

BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "65535"))

PIECE_SIZE = int(os.getenv("PIECE_SIZE", str(256 * 1024)))  # 256KB pieces
BLOCK_SIZE = int(os.getenv("BLOCK_SIZE", str(8 * 1024)))    # 8KB UDP blocks (safe)

HEARTBEAT_SEC = int(os.getenv("NODE_TIME_INTERVAL", "10"))

SEED_DIR = os.getenv("SEED_DIR", "node_files")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# Tracker modes
MODE_OWN = "OWN"
MODE_NEED = "NEED"
MODE_LIST = "LIST"
MODE_FIND_BY_NAME = "FIND_BY_NAME"
MODE_REGISTER = "REGISTER"
MODE_EXIT = "EXIT"

# Peer msg types
T_GET_PIECE = "GET_PIECE"
T_PIECE_BLOCK = "PIECE_BLOCK"
