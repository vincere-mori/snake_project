import pygame
import sys
import random
import math

W, H   = 800, 600
HUD    = 40
CELL   = 20
COLS   = W // CELL
ROWS   = (H - HUD) // CELL   # 28

FPS    = 10

BG      = (6,   8,  20)
GRID_C  = (18,  25,  42)
S_HEAD  = (0,  255, 180)
S_TAIL  = (0,   80,  60)
NODE_C  = (255, 215,  40)
VIRUS_C = (255,  55,  55)
HUD_C   = (0,  210, 255)
WHITE   = (220, 240, 255)

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("SERPENT.EXE")
clock  = pygame.time.Clock()
fnt_lg = pygame.font.SysFont("Courier New", 36, bold=True)
fnt_md = pygame.font.SysFont("Courier New", 20, bold=True)
fnt_sm = pygame.font.SysFont("Courier New", 13)

_scan = pygame.Surface((W, H), pygame.SRCALPHA)
for _y in range(0, H, 2):
    pygame.draw.line(_scan, (0, 0, 0, 50), (0, _y), (W, _y))


def cell_px(cx, cy):
    return cx * CELL, cy * CELL + HUD


def glow(surf, x, y, r, color, layers=3):
    for i in range(layers, 0, -1):
        s = pygame.Surface((r*2*i + 2, r*2*i + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, max(10, 55 // i)), (r*i + 1, r*i + 1), r*i)
        surf.blit(s, (x - r*i - 1, y - r*i - 1), special_flags=pygame.BLEND_RGBA_ADD)


class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'life', 'maxlife', 'color')

    def __init__(self, x, y, color):
        a = random.uniform(0, math.tau)
        sp = random.uniform(1.5, 4.0)
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.life = self.maxlife = random.randint(18, 35)
        self.color = color

    def update(self):
        self.vy += 0.12
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surf):
        r = max(1, self.life // 9)
        alpha = int(255 * self.life / self.maxlife)
        s = pygame.Surface((r*2 + 1, r*2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surf.blit(s, (int(self.x) - r, int(self.y) - r))


class Virus:
    def __init__(self):
        side = random.randrange(4)
        if   side == 0: self.cx, self.cy = random.randrange(COLS), 0
        elif side == 1: self.cx, self.cy = random.randrange(COLS), ROWS - 1
        elif side == 2: self.cx, self.cy = 0, random.randrange(ROWS)
        else:           self.cx, self.cy = COLS - 1, random.randrange(ROWS)

    def move_toward(self, tx, ty):
        dx, dy = tx - self.cx, ty - self.cy
        if abs(dx) >= abs(dy):
            if dx != 0: self.cx += 1 if dx > 0 else -1
        else:
            if dy != 0: self.cy += 1 if dy > 0 else -1

    def draw(self, surf):
        px, py = cell_px(self.cx, self.cy)
        mx, my = px + CELL // 2, py + CELL // 2
        r = CELL // 2 - 2
        glow(surf, mx, my, r + 3, VIRUS_C, layers=2)
        pts = [(mx, my - r), (mx - r + 1, my + r - 1), (mx + r - 1, my + r - 1)]
        pygame.draw.polygon(surf, VIRUS_C, pts)


def draw_grid():
    for x in range(0, W, CELL):
        pygame.draw.line(screen, GRID_C, (x, HUD), (x, H))
    for y in range(HUD, H, CELL):
        pygame.draw.line(screen, GRID_C, (0, y), (W, y))


def draw_snake(body, direction):
    n = len(body)
    for i, (cx, cy) in enumerate(reversed(body)):
        t = i / max(n - 1, 1)
        color = tuple(int(S_HEAD[c] * (1 - t) + S_TAIL[c] * t) for c in range(3))
        px, py = cell_px(cx, cy)
        m = 2 + int(t * 4)
        pygame.draw.rect(screen, color, (px + m, py + m, CELL - m*2, CELL - m*2), border_radius=4)

    if not body:
        return
    px, py = cell_px(body[0][0], body[0][1])
    mx, my = px + CELL // 2, py + CELL // 2
    r = CELL // 2 - 1
    d = direction
    if   d == (0, -1): pts = [(mx, my-r), (mx-r+1, my+r-1), (mx+r-1, my+r-1)]
    elif d == (0,  1): pts = [(mx, my+r), (mx-r+1, my-r+1), (mx+r-1, my-r+1)]
    elif d == (-1, 0): pts = [(mx-r, my), (mx+r-1, my-r+1), (mx+r-1, my+r-1)]
    else:              pts = [(mx+r, my), (mx-r+1, my-r+1), (mx-r+1, my+r-1)]
    glow(screen, mx, my, r + 2, S_HEAD)
    pygame.draw.polygon(screen, S_HEAD, pts)


def draw_node(ncx, ncy, tick):
    px, py = cell_px(ncx, ncy)
    mx, my = px + CELL // 2, py + CELL // 2
    s = int(CELL // 2 - 4 + abs(math.sin(tick * 0.18)) * 2)
    glow(screen, mx, my, s + 5, NODE_C)
    pygame.draw.rect(screen, NODE_C, (mx - s, my - s, s*2, s*2), border_radius=3)


def draw_hud(score, integrity, wave):
    pygame.draw.rect(screen, (0, 20, 40), (0, 0, W, HUD))
    pygame.draw.line(screen, HUD_C, (0, HUD), (W, HUD), 1)
    screen.blit(fnt_md.render(f"SCORE {score:05d}", True, HUD_C), (10, 10))
    wt = fnt_md.render(f"WAVE {wave}", True, HUD_C)
    screen.blit(wt, (W // 2 - wt.get_width() // 2, 10))
    bw, bh = 160, 14
    bx, by = W - bw - 60, (HUD - bh) // 2
    pygame.draw.rect(screen, (40, 0, 0), (bx, by, bw, bh))
    fc = (0, 200, 80) if integrity > 50 else (240, 160, 0) if integrity > 25 else VIRUS_C
    pygame.draw.rect(screen, fc, (bx, by, int(bw * integrity / 100), bh))
    pygame.draw.rect(screen, HUD_C, (bx, by, bw, bh), 1)
    screen.blit(fnt_sm.render("INTEGRITY", True, WHITE), (bx + bw + 4, by + 1))


def text_c(txt, y, font, color):
    s = font.render(txt, True, color)
    screen.blit(s, (W // 2 - s.get_width() // 2, y))


def menu():
    while True:
        screen.fill(BG)
        draw_grid()
        t = pygame.time.get_ticks()
        blink = HUD_C if (t // 500) % 2 else GRID_C
        text_c("SERPENT.EXE", 180, fnt_lg, S_HEAD)
        text_c("[ PRESS ANY KEY TO BOOT ]", 250, fnt_md, blink)
        text_c("WASD / ARROWS  —  MOVE", 340, fnt_sm, WHITE)
        text_c("EAT DATA NODES BEFORE VIRUSES REACH THEM", 360, fnt_sm, WHITE)
        text_c("TAIL ABSORBS VIRUS HITS  —  HEAD HIT = DEAD", 380, fnt_sm, WHITE)
        screen.blit(_scan, (0, 0))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN: return
        clock.tick(30)


def game_over(score):
    while True:
        screen.fill(BG)
        t = pygame.time.get_ticks()
        blink = WHITE if (t // 500) % 2 else GRID_C
        text_c("// PROCESS TERMINATED", 210, fnt_lg, VIRUS_C)
        text_c(f"FINAL SCORE: {score:05d}", 280, fnt_md, HUD_C)
        text_c("R — RESTART     ESC — EXIT", 360, fnt_sm, blink)
        screen.blit(_scan, (0, 0))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:      return True
                if e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        clock.tick(30)


def run():
    body      = [(COLS//2, ROWS//2), (COLS//2-1, ROWS//2), (COLS//2-2, ROWS//2)]
    direction = (1, 0)
    queued    = (1, 0)
    nodes: list     = []
    viruses: list   = []
    particles: list = []
    score     = 0
    integrity = 100
    wave      = 1
    tick      = 0
    v_timer   = 0
    v_rate    = 55

    def fresh_node():
        occupied = set(body) | set(nodes)
        for _ in range(200):
            p = (random.randint(1, COLS-2), random.randint(1, ROWS-2))
            if p not in occupied:
                nodes.append(p)
                return

    for _ in range(3):
        fresh_node()

    while True:
        clock.tick(FPS)
        tick += 1

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if   e.key in (pygame.K_UP,    pygame.K_w) and direction != (0,  1): queued = (0, -1)
                elif e.key in (pygame.K_DOWN,  pygame.K_s) and direction != (0, -1): queued = (0,  1)
                elif e.key in (pygame.K_LEFT,  pygame.K_a) and direction != (1,  0): queued = (-1, 0)
                elif e.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0): queued = (1,  0)
                elif e.key == pygame.K_ESCAPE: return score

        direction = queued
        hx, hy = body[0]
        ddx, ddy = direction
        nhx, nhy = (hx + ddx) % COLS, (hy + ddy) % ROWS
        new_head = (nhx, nhy)

        if new_head in body[1:]:
            return score

        ate = new_head in nodes
        body.insert(0, new_head)
        if ate:
            nodes.remove(new_head)
            score += 10 * wave
            fresh_node()
            epx, epy = cell_px(new_head[0], new_head[1])
            for _ in range(14):
                particles.append(Particle(epx + CELL//2, epy + CELL//2, NODE_C))
        else:
            body.pop()

        v_timer += 1
        if v_timer >= v_rate:
            v_timer = 0
            viruses.append(Virus())
        if tick % 200 == 0:
            wave += 1
            v_rate = max(18, v_rate - 5)

        if tick % 3 == 0 and nodes:
            target = nodes[0]
            for v in viruses:
                v.move_toward(target[0], target[1])

        dead_v = []
        for v in viruses:
            vpos = (v.cx, v.cy)
            if vpos in nodes:
                nodes.remove(vpos)
                dead_v.append(v)
                integrity = max(0, integrity - 8)
                fresh_node()
            elif len(body) > 1 and vpos in body[1:]:
                idx = body.index(vpos, 1)
                body = body[:idx]
                dead_v.append(v)
                integrity = max(0, integrity - 5)
                vpx, vpy = cell_px(v.cx, v.cy)
                for _ in range(10):
                    particles.append(Particle(vpx + CELL//2, vpy + CELL//2, VIRUS_C))
            elif vpos == body[0]:
                return score
        for v in dead_v:
            if v in viruses:
                viruses.remove(v)

        if integrity <= 0:
            return score

        while len(nodes) < 3:
            fresh_node()

        screen.fill(BG)
        draw_grid()
        for ncx, ncy in nodes:
            draw_node(ncx, ncy, tick)
        for v in viruses:
            v.draw(screen)
        draw_snake(body, direction)
        for p in particles[:]:
            p.update()
            p.draw(screen)
            if p.life <= 0:
                particles.remove(p)
        draw_hud(score, integrity, wave)
        screen.blit(_scan, (0, 0))
        pygame.display.flip()


menu()
while True:
    score = run()
    game_over(score)
