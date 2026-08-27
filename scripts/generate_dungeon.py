#!/usr/bin/env python3
"""
Dungeon Run generator — creates a dark-neon pixel dungeon SVG.
Mimics Dungeon-Night style: 16px tiles -> SVG, seeded by current UTC hour.
Auto-committed by GitHub Actions every 6h.
"""
import random, datetime, os, hashlib

W, H = 26, 10          # tiles
TILE = 22
PAD = 16
SVG_W = W * TILE + PAD * 2
SVG_H = H * TILE + PAD * 2 + 38  # extra for HUD

# colors — same palette as Dungeon Gelap
BG = "#050608"
WALL = "#1a1f26"
FLOOR = "#12161b"
FLOOR2 = "#181d24"
TORCH = "#f1c40f"
GOLD = "#f1c40f"
SLIME = "#2ecc71"
GOBLIN = "#e74c3c"
BAT = "#9b59b6"
CHEST = "#f39c12"
STAIRS = "#3498db"
KNIGHT = "#c8cdd4"

def make_dungeon(seed: int):
    random.seed(seed)
    # grid 0=wall 1=floor
    g = [[0]*W for _ in range(H)]
    # carve 4 rooms
    rooms = []
    for _ in range(4):
        rw = random.randint(5, 8)
        rh = random.randint(3, 5)
        rx = random.randint(1, W - rw - 1)
        ry = random.randint(1, H - rh - 1)
        rooms.append((rx, ry, rw, rh))
        for y in range(ry, ry+rh):
            for x in range(rx, rx+rw):
                g[y][x] = 1
    # connect rooms with L corridors
    for i in range(len(rooms)-1):
        x1 = rooms[i][0] + rooms[i][2]//2
        y1 = rooms[i][1] + rooms[i][3]//2
        x2 = rooms[i+1][0] + rooms[i+1][2]//2
        y2 = rooms[i+1][1] + rooms[i+1][3]//2
        if random.random() < 0.5:
            for x in range(min(x1,x2), max(x1,x2)+1): g[y1][x] = 1
            for y in range(min(y1,y2), max(y1,y2)+1): g[y][x2] = 1
        else:
            for y in range(min(y1,y2), max(y1,y2)+1): g[y][x1] = 1
            for x in range(min(x1,x2), max(x1,x2)+1): g[y2][x] = 1
    # sprinkle floor2 variation
    for y in range(H):
        for x in range(W):
            if g[y][x]==1 and random.random()<0.12:
                g[y][x]=2
    floors = [(x,y) for y in range(H) for x in range(W) if g[y][x] in (1,2)]
    if not floors: floors=[(W//2,H//2)]
    px, py = random.choice(floors)
    # place 3 enemies, 1 chest, 1 stairs on distinct floors
    picks = random.sample(floors, min(8, len(floors)))
    enemies = [(picks[i][0], picks[i][1], [SLIME,GOBLIN,BAT][i%3]) for i in range(min(3,len(picks)))]
    chest = picks[4] if len(picks)>4 else None
    stairs = picks[5] if len(picks)>5 else picks[-1]
    return g, (px,py), enemies, chest, stairs

def svg_for(g, player, enemies, chest, stairs, seed):
    dt = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:00 UTC")
    h = hashlib.md5(str(seed).encode()).hexdigest()[:6]
    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}" role="img">')
    out.append(f'<rect width="100%" height="100%" rx="12" fill="{BG}" />')
    # title
    out.append(f'<text x="{SVG_W/2}" y="22" text-anchor="middle" font-family="\'Courier New\',monospace" font-size="11" font-weight="bold" letter-spacing="3" fill="{GOLD}">DUNGEON RUN  •  Seed {h}  •  {dt}</text>')
    # grid
    for y in range(H):
        for x in range(W):
            v = g[y][x]
            col = WALL if v==0 else (FLOOR2 if v==2 else FLOOR)
            rx = PAD + x*TILE
            ry = PAD + 28 + y*TILE
            out.append(f'<rect x="{rx}" y="{ry}" width="{TILE-1}" height="{TILE-1}" rx="2" fill="{col}" />')
            if v==0 and random.random()<0.04:
                out.append(f'<rect x="{rx+6}" y="{ry+6}" width="3" height="3" rx="1" fill="#0b0d10" opacity="0.6"/>')
    # stairs
    if stairs:
        sx, sy = stairs
        cx = PAD + sx*TILE + TILE//2
        cy = PAD + 28 + sy*TILE + TILE//2
        out.append(f'<rect x="{PAD+sx*TILE+4}" y="{PAD+28+sy*TILE+4}" width="{TILE-8}" height="{TILE-8}" rx="3" fill="{STAIRS}" opacity="0.9"/>')
        out.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-family="monospace" font-size="9" fill="white">▦</text>')
    if chest:
        cx2, cy2 = chest
        out.append(f'<rect x="{PAD+cx2*TILE+5}" y="{PAD+28+cy2*TILE+6}" width="{TILE-10}" height="{TILE-10}" rx="2" fill="{CHEST}" />')
        out.append(f'<text x="{PAD+cx2*TILE+TILE//2}" y="{PAD+28+cy2*TILE+TILE//2+4}" text-anchor="middle" font-size="8" fill="#111">◆</text>')
    for ex, ey, col in enemies:
        cx = PAD + ex*TILE + TILE//2
        cy = PAD + 28 + ey*TILE + TILE//2
        out.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{col}" stroke="#0b0d10" stroke-width="1.2"/>')
        out.append(f'<circle cx="{cx-2}" cy="{cy-1}" r="1.2" fill="white" opacity="0.9"/>')
        out.append(f'<circle cx="{cx+2}" cy="{cy-1}" r="1.2" fill="white" opacity="0.9"/>')
    # player (knight) — pulsing
    px, py = player
    pcx = PAD + px*TILE + TILE//2
    pcy = PAD + 28 + py*TILE + TILE//2
    out.append(f'<g id="player"><circle cx="{pcx}" cy="{pcy}" r="9" fill="{KNIGHT}" stroke="{GOLD}" stroke-width="1.6"/>'
               f'<text x="{pcx}" y="{pcy+4}" text-anchor="middle" font-size="10" fill="#0b0d10">♞</text>'
               f'<animateTransform attributeName="transform" type="scale" values="1;1.06;1" dur="1.2s" repeatCount="indefinite" additive="sum"/>'
               f'</g>')
    # HUD
    hud_y = PAD + 28 + H*TILE + 18
    out.append(f'<text x="{PAD}" y="{hud_y}" font-family="\'Courier New\',monospace" font-size="10" fill="#8a909a">Floor <tspan fill="{GOLD}" font-weight="bold">{(seed%5)+1}</tspan>  •  Enemies 3  •  Seed {h}</text>')
    out.append(f'<text x="{SVG_W-PAD}" y="{hud_y}" text-anchor="end" font-family="monospace" font-size="9" fill="#6a707a">auto-generated by GitHub Actions</text>')
    out.append('</svg>')
    return "\n".join(out)

def main():
    now = datetime.datetime.utcnow()
    # seed changes every 6h so dungeon evolves but stays stable within window
    seed_str = now.strftime("%Y-%m-%d-%H")
    # quantize to 6h bucket
    bucket = (now.hour // 6) * 6
    seed_str = now.strftime(f"%Y-%m-%d-{bucket:02d}")
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16)
    g, player, enemies, chest, stairs = make_dungeon(seed)
    svg = svg_for(g, player, enemies, chest, stairs, seed)
    os.makedirs("assets", exist_ok=True)
    with open("assets/dungeon.svg", "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"Dungeon generated seed={seed_str} -> assets/dungeon.svg")

if __name__ == "__main__":
    main()
