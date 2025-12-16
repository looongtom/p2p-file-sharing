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
