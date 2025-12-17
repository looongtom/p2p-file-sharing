<<<<<<< HEAD
# BitTorrent P2P (Docker demo with real transfer)

## Run
From `docker/`:

```bash
docker compose up --build
```

## Seed a file (on host)
Create file on host:

- `data/peer1/node_files/demo.txt`

## Announce seed on peer1
Attach peer1:

```bash
docker attach bt-peer1
```

Type:

```text
torrent -setMode send demo.txt
```

Detach without stopping: `Ctrl+P` then `Ctrl+Q`.

## Download on peer2
Attach peer2:

```bash
docker attach bt-peer2
```

Type:

```text
torrent -setMode download demo.txt
```

## Where is the downloaded file?
On host:

- `data/peer2/downloads/demo.txt`

Inside container:

- `/app/downloads/demo.txt`
=======
BitTorrent-like P2P File Sharing (Docker Demo)
1. Giới thiệu

Dự án này là một mô phỏng hệ thống chia sẻ file ngang hàng (P2P) theo ý tưởng của BitTorrent, được xây dựng nhằm mục đích:

Minh hoạ cơ chế tracker – peer

Thực hành chia file thành các piece

Download song song từ nhiều peer

Hỗ trợ resume download

Dễ dàng demo và mở rộng trên Docker

⚠️ Đây không phải BitTorrent chuẩn RFC, mà là một phiên bản giản lược – dễ hiểu – phục vụ học tập, demo, đồ án.

2. Kiến trúc tổng thể

Hệ thống gồm 3 thành phần chính:

2.1 Tracker

Là node trung tâm duy nhất

Không lưu dữ liệu file

Chỉ quản lý metadata:

file nào (theo infohash)

đang có ở những peer nào

Giao tiếp với peer qua UDP

2.2 Peer (Node)

Mỗi peer vừa có thể là:

Seeder (có file, chia sẻ file)

Leecher (tải file)

Peer giao tiếp:

Với tracker: đăng ký, tìm file

Với peer khác: trao đổi piece

2.3 Docker Network

Mỗi tracker / peer chạy trong container riêng

Kết nối với nhau qua docker network nội bộ

Port của từng peer được cố định

3. Cấu trúc thư mục
bittorrent-p2p/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── tracker/
│   └── tracker.py
│
├── peer/
│   └── node.py
│
├── common/
│   ├── constants.py
│   └── utils.py
│
├── data/
│   ├── peer1/
│   │   ├── node_files/     # file seed
│   │   └── downloads/      # file tải về
│   ├── peer2/
│   │   ├── node_files/
│   │   └── downloads/
│   └── peer3/
│       ├── node_files/
│       └── downloads/
│
└── README.md

4. Các khái niệm chính
4.1 Infohash

Mỗi file được đại diện bởi infohash

Infohash = SHA256(meta)

meta bao gồm:

filename

size

piece_size

danh sách hash của từng piece

👉 Hai file cùng tên nhưng nội dung khác → infohash khác

4.2 Piece & Block

File được chia thành:

Piece: 256KB (configurable)

Block: 8KB (gửi qua UDP)

Download:

nhận từng block

ghép thành piece

verify hash

ghi xuống file .part

5. Chức năng hiện có
5.1 Announce file (Seeder)

Peer có file sẽ chạy:

torrent -setMode send <filename>


Peer sẽ:

Tính infohash

Gửi metadata lên tracker

Bắt đầu serve piece cho peer khác

Gửi heartbeat định kỳ để tracker không xoá owner

5.2 List file trên mạng P2P
torrent list


Tracker trả về danh sách:

filename

size

số peer đang giữ

infohash (rút gọn)

Ví dụ:

Xshell.rar  size=51466180  peers=2  ih=2727e463fc..

5.3 Download theo tên file
torrent -setMode download Xshell.rar


Cơ chế:

Peer hỏi tracker theo filename

Nếu:

1 infohash → download ngay

nhiều infohash → báo AMBIGUOUS

Tracker trả về:

metadata

danh sách peer đang giữ file

5.4 Download theo infohash
torrent -setMode download 2727e463fc...


Áp dụng khi:

Có nhiều file trùng tên

Cần chỉ định chính xác torrent

5.5 Download từ nhiều peer (Multi-peer)

Nếu:

Có N peer cùng giữ 1 infohash

Tracker trả về danh sách peers = [peer1, peer2, ...]

Peer download sẽ:

Tạo 1 queue chứa tất cả piece

Tạo 1 worker thread cho mỗi peer

Mỗi worker:

lấy piece từ queue

tải piece từ peer của nó

Piece fail (timeout/hash mismatch):

được đưa lại vào queue

peer khác có thể tải tiếp

👉 Đây là cơ chế multi-peer song song.

5.6 Resume download

Trong quá trình download:

File tạm: filename.part

Trạng thái: filename.resume.json

Resume file lưu:

infohash

completed piece list

tiến độ

❌ Không lưu bytes (tránh lỗi JSON)

Khi chạy lại download:

Peer tự động resume từ các piece đã có

5.7 Logging chi tiết

Peer log rõ:

piece nào được request

request từ peer nào

piece hoàn tất từ peer nào

Ví dụ:

[NODE 2] request piece 12 from node 1 @ peer1:20001
[NODE 2] completed piece 12 from node 1 @ peer1:20001


Rất phù hợp cho:

demo

báo cáo

giải thích multi-peer

6. Giao thức trao đổi (tóm tắt)
Tracker ⇄ Peer

OWN – announce file

NEED – tìm file theo infohash

LIST – liệt kê file

FIND_BY_NAME – tìm theo filename

REGISTER – heartbeat

EXIT – rời swarm

Peer ⇄ Peer

GET_PIECE

PIECE_BLOCK

7. Cách chạy
cd docker
docker compose up --build


Attach vào peer:

docker attach bt-peer1
>>>>>>> 5d906bc (Initial commit: BitTorrent-like P2P file sharing core)
