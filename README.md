![CS:GO Legacy](https://i.ibb.co/F4rhh9nb/Screenshot-2026-10-05-235613.png)

## What it is

### A P2P app with matchmaking and a skin editor for [mikkokko's csgo_gc](https://github.com/mikkokko/csgo_gc)

## Features
- Gloves, knives and agents editor, exports straight to `inventory.txt`
- Steam login with avatar, friends and parties
- Matchmaking: finds a server with room for your whole party
- Server list from `csgo_gc/server.txt`
- Backup and restore your save data

## How to Download
1. Download CS:GO Legacy from [Steam](https://store.steampowered.com/app/4465480/CounterStrikeGlobal_Offensive/).
2. Download the mod from [GitHub](https://github.com/ankerboi/frad-mod/releases/tag/continuous).
3. Open the zip and drag and drop the files into the CS:GO folder.
4. Replace the files with the new one.

## How to Use Matchmaking
1. Log in, open **Matchmaking** and invite friends (optional).
2. Pick a category (5v5, dm, no_gc) and press **Queue**.
3. Press **Copy IP**, then paste it into the CS:GO console.

## Servers
Servers live in `csgo_gc/server.txt`, one `ip:port` per line. A line starting with `//` starts a category.

```
//5v5
51.75.147.102:27016

//dm
45.136.205.63:27017
```

And add community servers to the file, then press Queue.