"""Arte procedural original: personagens, mutantes, laboratórios e interface."""
import math
import random
import pygame
from pygame import Vector2 as V
from .model import TILE, WORLD_W, WORLD_H, COLS, ROWS
from .story import CHAPTERS

W, H = 1200, 720
INK = (8, 13, 22)
PANEL = (15, 24, 36)
WHITE = (231, 239, 238)
MUTED = (138, 160, 174)
CYAN = (93, 229, 223)
GOLD = (242, 187, 102)
RED = (248, 114, 119)


def glow(radius, color):
    image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -3):
        alpha = int(26 * (1 - r / radius) ** 2)
        pygame.draw.circle(image, (*color, alpha), (radius, radius), r)
    return image


def human(name='LIA', phase=0, facing=1):
    """Sprite 48x64, com cabeça, cabelo, armadura, mochila e pernas animadas."""
    s = pygame.Surface((48, 64), pygame.SRCALPHA)
    armor = {'LIA': (49, 135, 154), 'NINA': (200, 204, 215), 'IVO': (202, 143, 62),
             'TEO': (119, 146, 162), 'MAIA': (179, 210, 190)}.get(name, (130, 140, 160))
    accent = CYAN if name == 'LIA' else GOLD if name == 'IVO' else (163, 239, 183)
    shift = 3 if phase % 2 else -3
    pygame.draw.ellipse(s, (0, 0, 0, 95), (5, 49, 39, 13))
    pygame.draw.rect(s, (24, 37, 49), (10, 24, 29, 25), border_radius=5)
    for x, off in ((15, shift), (28, -shift)):
        pygame.draw.rect(s, (32, 46, 61), (x, 42, 8, 12 + off), border_radius=2)
        pygame.draw.rect(s, (71, 86, 99), (x - 1, 51 + off, 10, 5), border_radius=2)
    pygame.draw.rect(s, armor, (12, 23, 25, 24), border_radius=5)
    pygame.draw.rect(s, (44, 66, 83), (19, 26, 14, 15), border_radius=2)
    pygame.draw.line(s, accent, (21, 29), (31, 29), 3)
    pygame.draw.rect(s, (20, 30, 44), (12, 43, 25, 5))
    pygame.draw.rect(s, accent, (22, 43, 5, 3))
    pygame.draw.rect(s, armor, (6, 26, 8, 17), border_radius=3)
    pygame.draw.rect(s, armor, (35, 26, 8, 17), border_radius=3)
    pygame.draw.rect(s, (211, 166, 139), (7, 40, 6, 6), border_radius=2)
    pygame.draw.rect(s, (211, 166, 139), (36, 40, 6, 6), border_radius=2)
    pygame.draw.rect(s, (37, 43, 53), (14, 6, 23, 19), border_radius=7)
    pygame.draw.rect(s, (221, 180, 148), (17, 11, 18, 15), border_radius=5)
    if name in ('LIA', 'NINA', 'MAIA'):
        pygame.draw.polygon(s, (49, 38, 47), [(14, 17), (14, 7), (20, 3), (34, 5), (38, 14), (24, 10), (21, 19)])
        pygame.draw.rect(s, (57, 40, 48), (12, 13, 6, 17), border_radius=2)
    else:
        pygame.draw.rect(s, armor, (13, 6, 24, 9), border_radius=3)
        pygame.draw.rect(s, accent, (20, 8, 10, 3))
    pygame.draw.rect(s, (30, 44, 55), (27, 16, 6, 3))
    pygame.draw.rect(s, accent, (28, 16, 4, 2))
    if name == 'LIA':
        pygame.draw.rect(s, (19, 28, 39), (34, 33, 14, 7), border_radius=2)
        pygame.draw.rect(s, (101, 129, 141), (37, 32, 11, 3))
        pygame.draw.rect(s, CYAN, (44, 34, 4, 3))
    return pygame.transform.flip(s, facing < 0, False)


def mutant(kind, phase=0):
    size = 100 if kind == 'boss' else 64
    s = pygame.Surface((size, size + 12), pygame.SRCALPHA)
    cx = size // 2
    scale = size / 64
    def p(x, y):
        return (int(x * scale), int(y * scale))
    skin = {'crawler': (136, 105, 127), 'spitter': (99, 153, 119), 'brute': (160, 114, 95), 'boss': (135, 92, 158)}[kind]
    light = {'crawler': (239, 110, 145), 'spitter': (178, 239, 109), 'brute': (255, 169, 105), 'boss': (227, 126, 239)}[kind]
    pygame.draw.ellipse(s, (0, 0, 0, 105), (3, size - 12, size - 6, 19))
    offset = 3 if phase else -3
    for x, off in ((21, offset), (38, -offset)):
        pygame.draw.line(s, (54, 58, 70), p(x, 42), p(x + off, 60), max(5, int(8 * scale)))
        pygame.draw.line(s, skin, p(x + off, 56), p(x + off + 6, 58), max(3, int(4 * scale)))
    pygame.draw.ellipse(s, (45, 50, 65), (*p(14, 22), int(37 * scale), int(28 * scale)))
    pygame.draw.ellipse(s, skin, (*p(13, 19), int(38 * scale), int(29 * scale)))
    for i in range(4):
        pygame.draw.line(s, (65, 65, 81), p(23, 28 + i * 4), p(42, 31 + i * 4), max(1, int(2 * scale)))
    for x, sign in ((17, -1), (46, 1)):
        pygame.draw.line(s, skin, p(x, 27), p(x + sign * 7, 43 + offset), int(9 * scale))
        pygame.draw.line(s, skin, p(x + sign * 7, 43 + offset), p(x + sign * 11, 50), int(5 * scale))
        for f in range(3):
            pygame.draw.line(s, (225, 206, 173), p(x + sign * 11, 48), p(x + sign * (10 + f * 2), 55), max(1, int(scale)))
    pygame.draw.ellipse(s, skin, (*p(20, 6), int(28 * scale), int(26 * scale)))
    pygame.draw.polygon(s, (45, 38, 53), [p(25, 22), p(44, 20), p(38, 30), p(28, 28)])
    for x in range(28, 43, 4):
        pygame.draw.line(s, (234, 221, 192), p(x, 22), p(x - 1, 25), max(1, int(scale)))
    pygame.draw.line(s, light, p(25, 15), p(31, 17), max(2, int(3 * scale)))
    pygame.draw.line(s, light, p(36, 17), p(44, 13), max(2, int(3 * scale)))
    for i in range(4 if kind != 'boss' else 7):
        x = 12 + i * 6
        pygame.draw.polygon(s, light if i % 2 else skin, [p(x, 26), p(x - 5, 11 - i % 3 * 3), p(x + 6, 22)])
    if kind == 'spitter':
        pygame.draw.circle(s, light, p(32, 36), int(7 * scale))
        pygame.draw.circle(s, (209, 255, 165), p(30, 34), int(3 * scale))
    if kind == 'boss':
        pygame.draw.circle(s, light, p(34, 34), int(8 * scale), 3)
        pygame.draw.line(s, light, p(34, 27), p(34, 43), 2)
    return s


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.fonts = {}
        self.floor = None
        self.floor_chapter = -1
        self.camera = V()
        self.zoom = 1.5
        self.scene = pygame.Surface((W, H))
        self.expanded_objectives = False
        self.route_key = None
        self.route = []
        self.vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(90):
            pygame.draw.rect(self.vignette, (1, 5, 13, int(100 * (1 - i / 90) ** 2)), (i, i, W - 2 * i, H - 2 * i), 1)
        self.sprites = {(n, p, d): human(n, p, d) for n in ('LIA', 'NINA', 'IVO', 'TEO', 'MAIA') for p in (0, 1) for d in (-1, 1)}
        self.monsters = {(n, p): mutant(n, p) for n in ('crawler', 'spitter', 'brute', 'boss') for p in (0, 1)}
        self.lights = {'cyan': glow(95, CYAN), 'gold': glow(70, GOLD), 'red': glow(105, RED), 'green': glow(80, (115, 244, 168))}
        self.grain = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 4):
            pygame.draw.line(self.grain, (0, 0, 0, 15), (0, y), (W, y))

    def font(self, size, bold=False, mono=False):
        key = size, bold, mono
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont('consolas' if mono else 'segoeui', size, bold=bold)
        return self.fonts[key]

    def text(self, text, pos, size=20, color=WHITE, bold=False, center=False, mono=False):
        image = self.font(size, bold, mono).render(str(text), True, color)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(image, rect)
        return rect

    def wrap(self, text, pos, width, size=21, color=WHITE, leading=None):
        x, y = pos
        line = ''
        for word in text.split():
            candidate = (line + ' ' + word).strip()
            if self.font(size).size(candidate)[0] > width and line:
                self.text(line, (x, y), size, color)
                y += leading or size + 9
                line = word
            else:
                line = candidate
        if line:
            self.text(line, (x, y), size, color)
            y += leading or size + 9
        return y

    def panel(self, rect, color=PANEL, edge=(45, 64, 77)):
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, edge, rect, 1, border_radius=10)

    def bar(self, rect, value, color):
        pygame.draw.rect(self.screen, (31, 44, 55), rect, border_radius=3)
        fill = pygame.Rect(rect)
        fill.width = int(fill.width * max(0, min(1, value)))
        if fill.width:
            pygame.draw.rect(self.screen, color, fill, border_radius=3)

    def shade(self, alpha=185):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((3, 8, 15, alpha))
        self.screen.blit(s, (0, 0))

    def button(self, rect, label, selected=False, primary=False):
        bg = (37, 76, 85) if selected else (21, 43, 54) if primary else (15, 26, 39)
        self.panel(rect, bg, CYAN if selected else (53, 80, 94))
        self.text(label, rect.center, 19, WHITE, True, center=True)
        if selected:
            pygame.draw.rect(self.screen, CYAN, (rect.x, rect.y + 10, 3, rect.h - 20))

    def build_floor(self, world):
        s = pygame.Surface((WORLD_W, WORLD_H))
        s.fill((14, 22, 31))
        rng = random.Random(130 + world.chapter)
        accent = CHAPTERS[world.chapter]['color']
        for x in range(COLS):
            for y in range(ROWS):
                rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                if (x, y) in world.walls:
                    pygame.draw.rect(s, (9, 15, 23), rect)
                    pygame.draw.rect(s, (42, 57, 69), rect.inflate(-3, -3), border_radius=3)
                    pygame.draw.rect(s, (55, 73, 85), (rect.x + 3, rect.y + 3, TILE - 6, 6), border_radius=2)
                    pygame.draw.rect(s, (24, 35, 47), (rect.x + 6, rect.y + 15, TILE - 12, 25), border_radius=3)
                    pygame.draw.line(s, (68, 82, 95), (rect.x + 9, rect.y + 19), (rect.right - 9, rect.y + 19))
                    if (x + y) % 4 == 0:
                        pygame.draw.rect(s, accent, (rect.x + 12, rect.y + 8, 22, 2))
                    if (x, y) in world.covers:
                        if world.chapter == 2:
                            pygame.draw.rect(s, (35, 65, 69), rect.inflate(-5, -2), border_radius=14)
                            pygame.draw.rect(s, (70, 158, 139), rect.inflate(-10, -7), 2, border_radius=12)
                            pygame.draw.ellipse(s, (57, 104, 93), rect.inflate(-18, -12))
                            pygame.draw.circle(s, (133, 196, 152), rect.center, 8)
                            pygame.draw.line(s, (122, 214, 178), (rect.x + 11, rect.y + 9), (rect.x + 11, rect.bottom - 10), 2)
                        elif world.chapter == 1:
                            pygame.draw.circle(s, (15, 26, 37), rect.center, 20)
                            for angle in range(0, 360, 60):
                                tip = V(rect.center) + V(15, 0).rotate(angle)
                                pygame.draw.line(s, (98, 113, 120), rect.center, tip, 6)
                            pygame.draw.circle(s, GOLD, rect.center, 5)
                        else:
                            pygame.draw.rect(s, (69, 72, 69), rect.inflate(-4, -4), border_radius=3)
                            pygame.draw.rect(s, (103, 99, 75), rect.inflate(-10, -10), 2, border_radius=2)
                            pygame.draw.line(s, (119, 113, 82), (rect.x + 8, rect.y + 8), (rect.right - 8, rect.bottom - 8), 3)
                else:
                    v = rng.randrange(0, 7)
                    pygame.draw.rect(s, (20 + v, 30 + v, 40 + v), rect.inflate(-1, -1))
                    pygame.draw.line(s, (31, 43, 53), (rect.x + 3, rect.y + 3), (rect.right - 4, rect.y + 3))
                    for px, py in ((5, 6), (42, 41)):
                        pygame.draw.circle(s, (47, 58, 68), (rect.x + px, rect.y + py), 1)
                    if rng.random() < .12:
                        for i in range(4):
                            pygame.draw.line(s, (13, 23, 31), (rect.x + 12, rect.y + 13 + i * 6), (rect.x + 36, rect.y + 13 + i * 6), 2)
                    if rng.random() < .025:
                        stain = pygame.Surface((48, 48), pygame.SRCALPHA)
                        for i in range(6):
                            pygame.draw.circle(stain, (106, 55, 73, 110), (rng.randrange(9, 39), rng.randrange(9, 39)), rng.randrange(3, 12))
                        s.blit(stain, rect)
        # Sinalização, cabos e painéis sem obstáculos invisíveis.
        for room_x in (1, 13, 25):
            for room_y in (1, 12):
                # Faixa técnica junto à parede, fora do centro da sala.
                rx, ry = (room_x + 1) * TILE, (room_y + 1) * TILE
                pygame.draw.rect(s, (19, 39, 48), (rx, ry, 310, 14), border_radius=4)
                for dx in range(0, 302, 24):
                    pygame.draw.line(s, (65, 93, 100), (rx + dx, ry + 3), (rx + dx + 10, ry + 10), 2)
                pygame.draw.line(s, accent, (rx + 3, ry + 16), (rx + 310, ry + 16), 1)
        if world.chapter in (1, 4):
            for y in (9, 19):
                for x in range(2, 34):
                    if (x, y) not in world.walls:
                        pygame.draw.line(s, (77, 79, 64), (x * TILE, y * TILE + 7), ((x + 1) * TILE, y * TILE + 7), 4)
                        pygame.draw.line(s, (38, 51, 59), (x * TILE, y * TILE + 13), ((x + 1) * TILE, y * TILE + 13), 3)
        if world.chapter == 3:
            pygame.draw.circle(s, (45, 33, 58), (29 * TILE + 24, 17 * TILE + 24), 161)
            for radius in (118, 150, 165):
                pygame.draw.circle(s, (104, 64, 113), (29 * TILE + 24, 17 * TILE + 24), radius, 2)
            for angle in range(0, 360, 45):
                center = V(29 * TILE + 24, 17 * TILE + 24)
                pygame.draw.line(s, (96, 63, 108), center + V(90, 0).rotate(angle), center + V(164, 0).rotate(angle), 2)
        for x in (6, 18, 30):
            for y in (10, 12):
                pygame.draw.line(s, accent, (x * TILE - 30, y * TILE + 20), (x * TILE + 75, y * TILE + 20), 2)
        for x in (12, 24):
            for y in (5, 17):
                for offset in (-42, 72):
                    pygame.draw.line(s, accent, (x * TILE + 10, y * TILE + offset), (x * TILE + 38, y * TILE + offset), 3)
        labels = [['CARGO / 01', 'ENFERMARIA', 'ARQUIVO', 'DOCAS OESTE', 'TRIAGEM', 'EVAC / 02'],
                  ['RELÉ A', 'RELÉ B', 'CONTROLE', 'MANUTENÇÃO', 'TURBINAS', 'ELEVADOR'],
                  ['PESQUISA', 'CULTURAS', 'ARQUIVO CENTRAL', 'OBSERVAÇÃO', 'QUARENTENA', 'CONTENÇÃO'],
                  ['SELO 01', 'SELO 02', 'SELO 03', 'ACESSO', 'MEMÓRIA', 'VOSS / NÚCLEO'],
                  ['SUPORTE NEURAL', 'ESTABILIZADOR', 'TRANSMISSÃO', 'RESERVA', 'REFRIGERAÇÃO', 'NAVE / SAÍDA']][world.chapter]
        for i, label in enumerate(labels):
            p = ((i % 3 * 12 + 2) * TILE, (3 if i < 3 else 14) * TILE)
            image = self.font(16, True, True).render(label, True, (73, 96, 108))
            s.blit(image, p)
            pygame.draw.line(s, (56, 73, 82), (p[0], p[1] + 30), (p[0] + 260, p[1] + 30), 1)
        self.floor = s
        self.floor_chapter = world.chapter

    def p(self, pos):
        return V(pos) - self.camera

    def world_to_screen(self, pos):
        return (V(pos) - self.camera) * self.zoom

    def screen_to_world(self, pos):
        return V(pos) / self.zoom + self.camera

    def aim(self, mouse, ready=True):
        x, y = int(mouse.x), int(mouse.y)
        color = CYAN if ready else GOLD
        pygame.draw.circle(self.screen, color, (x, y), 10, 1)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pygame.draw.line(self.screen, color, (x + dx * 6, y + dy * 6), (x + dx * 15, y + dy * 15), 2)
        pygame.draw.circle(self.screen, WHITE, (x, y), 1)

    def guidance(self, world):
        target = world.target()
        if target is None:
            return []
        key = (id(world), int(world.player.x // TILE), int(world.player.y // TILE),
               int(target.x), int(target.y), int(world.elapsed * 2))
        if key != self.route_key:
            self.route_key = key
            self.route = world.objective_route()
        return self.route

    def tactical_map(self, world):
        self.shade(244)
        self.text('MAPA TÁTICO', (57, 39), 38, WHITE, True)
        self.text(CHAPTERS[world.chapter]['place'], (59, 92), 17, CYAN)
        rect = pygame.Rect(57, 142, 722, 462)
        self.panel(rect)
        scale = 20
        origin = V(rect.x + 1, rect.y + 1)
        def point(pos):
            return origin + V(pos) / TILE * scale
        for x in range(COLS):
            for y in range(ROWS):
                cell = pygame.Rect(origin.x + x * scale, origin.y + y * scale, scale - 1, scale - 1)
                color = (56, 74, 88) if (x, y) in world.walls else (18, 33, 45)
                pygame.draw.rect(self.screen, color, cell)
        route = self.guidance(world)
        if route:
            pygame.draw.lines(self.screen, (171, 139, 70), False, [point(world.player)] + [point(p) for p in route], 2)
        for n in world.nodes:
            if n.done:
                continue
            color = GOLD if n.kind in ('npc', 'upgrade', 'log') else (127, 227, 176) if n.kind == 'med' else CYAN
            pygame.draw.rect(self.screen, color, (*point(n.pos) - V(3, 3), 6, 6))
        for tile in world.hazard_tiles:
            p = origin + (V(tile) + V(.5, .5)) * scale
            pygame.draw.circle(self.screen, RED, p, 6, 1)
        for enemy in world.enemies:
            if enemy.pos.distance_to(world.player) < 350:
                pygame.draw.circle(self.screen, RED, point(enemy.pos), 3)
        target = world.target()
        if target is not None:
            pygame.draw.circle(self.screen, GOLD, point(target), 10, 2)
        if world.ally is not None:
            p = point(world.ally)
            pygame.draw.circle(self.screen, GOLD, p, 5)
            self.text(world.ally_name, p + (9, -12), 12, GOLD, True)
        p = point(world.player)
        pygame.draw.circle(self.screen, WHITE, p, 6)
        self.text('LIA', p + (10, 1), 12, WHITE, True)
        self.text('ROTA DA MISSÃO', (812, 149), 14, GOLD, True, mono=True)
        current = next((label for _, label, done in world.objectives() if not done and not label.startswith('Opcional')), 'Objetivos concluídos')
        self.wrap(current, (812, 183), 325, 24, WHITE)
        self.wrap('A linha dourada acompanha os corredores até o próximo objetivo.', (812, 259), 325, 18, MUTED, 27)
        for i, (text, color) in enumerate([('Você', WHITE), ('Objetivo / sobreviventes', GOLD), ('Terminais / saída', CYAN),
                                           ('Suprimentos', (127, 227, 176)), ('Perigos / ameaças próximas', RED)]):
            y = 363 + i * 33
            pygame.draw.circle(self.screen, color, (820, y + 9), 4)
            self.text(text, (837, y), 16, MUTED)
        self.wrap('O tempo fica pausado enquanto você consulta o mapa.', (812, 543), 325, 16, CYAN, 23)

    def draw_node(self, n, t):
        if n.done and n.kind in ('npc', 'key', 'sample', 'med'):
            return
        p = self.p(n.pos)
        if not (-100 < p.x < W + 100 and -100 < p.y < H + 100):
            return
        x, y = int(p.x), int(p.y)
        color = (72, 100, 103) if n.done else GOLD if n.kind in ('key', 'log', 'sample', 'upgrade') else CYAN
        if not n.done:
            light = self.lights['gold' if n.kind in ('log', 'key') else 'cyan']
            self.screen.blit(light, (x - light.get_width() // 2, y - light.get_height() // 2))
        if n.kind == 'upgrade':
            pygame.draw.rect(self.screen, (50, 63, 71), (x - 28, y - 19, 56, 38), border_radius=5)
            pygame.draw.rect(self.screen, (19, 35, 46), (x - 23, y - 15, 46, 27), border_radius=3)
            pygame.draw.line(self.screen, color, (x - 12, y - 8), (x + 8, y + 8), 5)
            pygame.draw.circle(self.screen, color, (x - 13, y - 9), 6, 2)
            pygame.draw.rect(self.screen, color, (x + 15, y - 9, 3, 13))
        elif n.kind == 'npc':
            name = n.id.upper()
            if name == 'NINA':
                pygame.draw.ellipse(self.screen, (27, 51, 66), (x - 40, y - 30, 80, 68))
                pygame.draw.ellipse(self.screen, CYAN, (x - 39, y - 30, 78, 68), 2)
                for offset in (-35, 35):
                    pygame.draw.line(self.screen, (79, 122, 132), (x + offset, y), (x + offset, y - 58), 6)
            sprite = self.sprites.get((name, 0, 1), self.sprites[('TEO', 0, 1)])
            self.screen.blit(sprite, (x - 24, y - 44))
            self.text(name, (x, y - 61), 13, GOLD, True, True)
        elif n.kind == 'console':
            pygame.draw.ellipse(self.screen, (5, 13, 21), (x - 27, y + 7, 58, 24))
            pygame.draw.rect(self.screen, (49, 67, 80), (x - 23, y - 27, 46, 44), border_radius=5)
            pygame.draw.rect(self.screen, (13, 25, 33), (x - 19, y - 24, 38, 27), border_radius=3)
            for i in range(3):
                pygame.draw.line(self.screen, color, (x - 14, y - 18 + 7 * i), (x + 7 + i * 3, y - 18 + 7 * i), 2)
            pygame.draw.rect(self.screen, color, (x - 10, y + 9, 6, 3))
            pygame.draw.rect(self.screen, color, (x + 4, y + 9, 6, 3))
        elif n.kind == 'exit':
            rect = pygame.Rect(x - 53, y - 51, 106, 105)
            pygame.draw.rect(self.screen, (11, 30, 39), rect, border_radius=9)
            pygame.draw.rect(self.screen, CYAN, rect, 2, border_radius=9)
            for dx in (-35, 35):
                pygame.draw.line(self.screen, (57, 133, 146), (x + dx, y - 34), (x + dx, y + 33), 4)
            pygame.draw.polygon(self.screen, CYAN, [(x - 14, y - 11), (x + 13, y), (x - 14, y + 11)], 2)
            self.text('SAÍDA / ACESSO', (x, y + 65), 13, CYAN, True, True)
        elif n.kind == 'med':
            pygame.draw.rect(self.screen, (62, 80, 86), (x - 14, y - 12, 28, 24), border_radius=4)
            pygame.draw.rect(self.screen, (149, 239, 180), (x - 3, y - 8, 6, 16))
            pygame.draw.rect(self.screen, (149, 239, 180), (x - 8, y - 3, 16, 6))
        elif n.kind == 'sample':
            pygame.draw.rect(self.screen, (75, 109, 113), (x - 13, y - 18, 26, 36), border_radius=6)
            pygame.draw.rect(self.screen, (129, 245, 167), (x - 7, y - 11, 14, 21), border_radius=4)
        else:
            pygame.draw.rect(self.screen, (49, 70, 87), (x - 13, y - 17, 26, 34), border_radius=3)
            pygame.draw.rect(self.screen, color, (x - 9, y - 12, 18, 15), border_radius=2)
            pygame.draw.line(self.screen, color, (x - 7, y + 9), (x + 7, y + 9), 2)
        if not n.done and n.kind not in ('npc', 'exit', 'med'):
            pygame.draw.circle(self.screen, color, (x, y - 41 - int(math.sin(t * 3) * 3)), 3)

    def world(self, world, t):
        if self.floor_chapter != world.chapter or self.floor is None:
            self.build_floor(world)
        output = self.screen
        self.screen = self.scene
        vw, vh = int(W / self.zoom), int(H / self.zoom)
        self.camera = V(max(0, min(WORLD_W - vw, world.player.x - vw / 2)),
                        max(0, min(WORLD_H - vh, world.player.y - vh / 2)))
        self.screen.blit(self.floor, (-self.camera.x, -self.camera.y))
        for pos, kind in world.corpses:
            p = self.p(pos)
            pygame.draw.ellipse(self.screen, (63, 40, 54), (p.x - 22, p.y - 10, 44, 23))
            pygame.draw.line(self.screen, (104, 71, 94), p + (-16, -2), p + (15, 8), 5)
        for i, tile in enumerate(world.hazard_tiles):
            p = self.p(((tile[0] + .5) * TILE, (tile[1] + .5) * TILE))
            state = world.hazard_state(i)
            color = RED if state == 'active' else GOLD if state == 'warning' else (78, 93, 102)
            pygame.draw.rect(self.screen, (11, 23, 31), (p.x - 25, p.y - 25, 50, 50), border_radius=4)
            pygame.draw.rect(self.screen, color, (p.x - 25, p.y - 25, 50, 50), 2, border_radius=4)
            for k in range(5):
                pygame.draw.line(self.screen, color, p + (-17, -16 + k * 8), p + (17, -16 + k * 8), 2)
            if state == 'active':
                lightning = [p + (math.sin(t * 42 + j) * 15, 22 - j * 9) for j in range(7)]
                pygame.draw.lines(self.screen, (220, 248, 252), False, lightning, 2)
                self.screen.blit(self.lights['red'], p - (105, 105))
        for node in world.nodes:
            self.draw_node(node, t)
        player_light = self.lights['cyan']
        self.screen.blit(player_light, self.p(world.player) - (95, 95))
        for pos, delay, radius in world.dangers:
            p = self.p(pos)
            pygame.draw.circle(self.screen, RED, p, radius, 2)
            pygame.draw.circle(self.screen, RED, p, int(radius * max(.1, 1 - delay / 1.05)), 1)
            self.text('IMPACTO', p + (-27, -8), 13, RED, True)
        entities = [(world.player.y, 'player', world.player, None)]
        if world.ally is not None:
            entities.append((world.ally.y, 'ally', world.ally, None))
        for e in world.enemies:
            entities.append((e.pos.y, 'enemy', e.pos, e))
        for _, kind, pos, e in sorted(entities, key=lambda row: row[0]):
            p = self.p(pos)
            if not (-100 < p.x < W + 100 and -100 < p.y < H + 100):
                continue
            if kind == 'enemy':
                sprite = self.monsters[(e.kind, int(t * (4 if e.stun else 7)) % 2)]
                if e.flash > 0:
                    sprite = sprite.copy()
                    sprite.fill((135, 150, 145, 0), special_flags=pygame.BLEND_RGBA_ADD)
                if e.windup > 0:
                    pygame.draw.circle(self.screen, RED, p, 49, 2)
                if not e.active:
                    pygame.draw.circle(self.screen, (188, 112, 218), p, 70, 2)
                self.screen.blit(sprite, (p.x - sprite.get_width() / 2, p.y - sprite.get_height() + 20))
                if e.hp < e.max_hp or e.kind == 'boss':
                    self.bar((p.x - 26, p.y - sprite.get_height() + 9, 52, 4), e.hp / e.max_hp, RED)
                if e.stun > 0:
                    pygame.draw.circle(self.screen, CYAN, p + (0, -47), 11, 2)
            else:
                name = 'LIA' if kind == 'player' else world.ally_name
                phase = int(t * 10) % 2 if world.moving else 0
                sprite = self.sprites[(name, phase, -1 if world.facing.x < 0 else 1)]
                if kind == 'ally' and world.ally_hp <= 0:
                    sprite = pygame.transform.rotate(sprite, 80)
                if kind != 'player' or world.invincible <= 0 or int(t * 15) % 2:
                    self.screen.blit(sprite, (p.x - sprite.get_width() / 2, p.y - 44))
                if kind == 'player':
                    if world.dash_left > 0:
                        pygame.draw.circle(self.screen, CYAN, p, 29, 2)
                    tip = p + world.facing * 33
                    pygame.draw.circle(self.screen, CYAN, tip, 2)
                    if world.muzzle > 0:
                        tip = p + world.facing * 30 + V(0, -12)
                        pygame.draw.circle(self.screen, (236, 255, 230), tip, 7)
                        pygame.draw.line(self.screen, CYAN, tip, tip + world.facing * 17, 4)
                else:
                    self.text(name, p + (0, -60), 12, GOLD, True, True)
                    self.bar((p.x - 22, p.y + 24, 44, 3), world.ally_hp / 100, GOLD)
        for shot in world.shots:
            p = self.p(shot.pos)
            color = CYAN if shot.friendly else (188, 238, 113)
            tail = p - shot.velocity.normalize() * 14
            pygame.draw.line(self.screen, color, tail, p, 4)
            pygame.draw.circle(self.screen, WHITE, p, 2)
        for pos, life, value in world.floaters:
            self.text(value, self.p(pos) + (0, -42), 14, GOLD, True, True)
        for pos, life, kind in world.effects:
            p = self.p(pos)
            color = RED if kind in ('hit', 'blast', 'death') else CYAN
            radius = int((1 - life / .6) * 185) if kind == 'emp' else int((1 - min(life, .8) / .8) * 42 + 5)
            pygame.draw.circle(self.screen, color, p, max(2, radius), 2)
            for i in range(7):
                q = p + V(radius * .7, 0).rotate(i * 51 + t * 20)
                pygame.draw.circle(self.screen, color, q, 2)
        # A escala afeta apenas a cena; textos e HUD continuam na resolução nativa.
        self.screen = output
        self.screen.blit(pygame.transform.scale(self.scene.subsurface((0, 0, vw, vh)), (W, H)), (0, 0))
        self.screen.blit(self.vignette, (0, 0))

    def hud(self, world, t, notices, muted):
        pygame.draw.rect(self.screen, INK, (0, 0, W, 87))
        pygame.draw.line(self.screen, (40, 62, 74), (0, 86), (W, 86))
        self.text('ECO—7', (24, 12), 25, CYAN, True)
        self.text('PROTOCOLO AURORA', (25, 47), 11, MUTED, mono=True)
        self.text('LIA / VITAL', (207, 14), 12, MUTED, mono=True)
        self.bar((207, 38, 177, 8), world.hp / world.max_hp, RED if world.hp < 35 else CYAN)
        self.text(f'{int(world.hp):03d}', (391, 30), 16, WHITE, mono=True)
        self.text('ENERGIA', (463, 14), 12, MUTED, mono=True)
        self.bar((463, 38, 146, 8), world.energy / 100, GOLD)
        self.text(f'H  KIT ×{world.medkits}', (663, 19), 17, WHITE, mono=True)
        self.text(f'CAPÍTULO {world.chapter + 1:02d} / 05', (884, 15), 13, CYAN, mono=True)
        self.text(CHAPTERS[world.chapter]['place'], (884, 39), 16, WHITE, True)
        self.text('J / ESQ  PLASMA   K / DIR  DISPERSOR', (207, 59), 10, MUTED, mono=True)
        self.text('ESPAÇO  ESQUIVA', (463, 59), 10, MUTED, mono=True)
        self.text('Q  PULSO EMP', (663, 47), 12, CYAN if world.emp_cd <= 0 and world.energy >= 45 else MUTED, mono=True)
        objectives = world.objectives()
        if not self.expanded_objectives:
            current = next((row for row in objectives if not row[2] and not row[1].startswith('Opcional')), objectives[-1])
            objectives = [current]
        panel_h = 51 + 25 * len(objectives)
        self.panel(pygame.Rect(20, 104, 292, panel_h), (12, 23, 33))
        self.text('MISSÃO ATUAL          O / LISTA', (36, 118), 11, GOLD, True, mono=True)
        for i, (_, label, complete) in enumerate(objectives):
            y = 147 + i * 25
            pygame.draw.circle(self.screen, CYAN if complete else (63, 79, 90), (40, y + 8), 4, 0 if complete else 1)
            self.text(label, (53, y), 14, MUTED if complete else WHITE)
        if world.ally is not None:
            self.panel(pygame.Rect(20, 116 + panel_h, 292, 56))
            label = 'CAIU · use E' if world.ally_hp <= 0 else 'ESPERANDO · C seguir' if world.ally_waiting else 'SEGUINDO · C esperar'
            self.text(world.ally_name + ' / ' + label, (35, 127 + panel_h), 12, GOLD)
            self.bar((35, 151 + panel_h, 260, 4), world.ally_hp / 100, GOLD)
        if world.timer is not None:
            self.panel(pygame.Rect(883, 104, 295, 63), (39, 22, 29), RED)
            self.text('COLAPSO EM', (900, 115), 11, RED, mono=True)
            self.text(f'{int(world.timer) // 60:02d}:{int(world.timer) % 60:02d}', (1107, 137), 30, RED, True, True, True)
        boss = next((e for e in world.enemies if e.kind == 'boss' and e.active and e.pos.distance_to(world.player) < 700), None)
        if boss:
            self.panel(pygame.Rect(389, 103, 422, 56))
            self.text('VOSS / CONSCIÊNCIA COLETIVA', (410, 112), 12, RED, True, mono=True)
            self.bar((410, 138, 380, 6), boss.hp / boss.max_hp, RED)
        # Radar da estação: paredes, terminais, alvo ativo e escolta.
        rect = pygame.Rect(978, 472, 200, 145)
        self.panel(rect)
        ox, oy, scale = rect.x + 10, rect.y + 11, 5
        for x, y in world.walls:
            pygame.draw.rect(self.screen, (52, 68, 82), (ox + x * scale, oy + y * scale, 4, 4))
        def mini(pos):
            return (ox + pos.x / TILE * scale, oy + pos.y / TILE * scale)
        target = world.target()
        for n in world.nodes:
            if not n.done and n.kind not in ('med',):
                pygame.draw.circle(self.screen, GOLD if n.kind == 'npc' else (94, 146, 156), mini(n.pos), 2)
        if target is not None:
            pygame.draw.circle(self.screen, GOLD, mini(target), 5, 1)
        if world.ally is not None:
            pygame.draw.circle(self.screen, GOLD, mini(world.ally), 3)
        pygame.draw.circle(self.screen, WHITE, mini(world.player), 3)
        self.text('MAPA / ALVO EM AMARELO', (rect.x + 10, rect.bottom - 17), 9, MUTED, mono=True)
        if target is not None:
            route = self.guidance(world)
            waypoint = next((p for p in route if p.distance_to(world.player) > 16), target)
            delta = waypoint - world.player
            if world.player.distance_to(target) > 100 and delta.length_squared():
                p = self.world_to_screen(world.player) + delta.normalize() * 99
                angle = delta.as_polar()[1]
                points = [p + V(v).rotate(angle) for v in ((8, 0), (-5, -5), (-5, 5))]
                pygame.draw.polygon(self.screen, GOLD, points)
        near = world.nearest()
        hint = None
        if world.ally is not None and world.ally_hp <= 0 and world.player.distance_to(world.ally) < 90:
            hint = 'E   AJUDAR ' + world.ally_name
        elif near:
            hint = 'E   ' + near.name
        if hint:
            width = self.font(17, True).size(hint)[0] + 40
            self.panel(pygame.Rect((W - width) // 2, 589, width, 42), (20, 45, 52), CYAN)
            self.text(hint, (W // 2, 610), 17, WHITE, True, True)
        if notices:
            text = notices[-1][0]
            self.panel(pygame.Rect(330, 168, 544, 70), (25, 38, 45), GOLD)
            self.wrap(text, (346, 178), 509, 16, GOLD, 22)
        pygame.draw.rect(self.screen, INK, (0, 652, W, 68))
        self.text('WASD mover   J/ESQ plasma   K/DIR dispersor   E interagir   ESPAÇO esquiva   Q pulso   H curar', (24, 666), 12, MUTED, mono=True)
        self.text('G mapa   C escolta   TAB diário   O objetivos   ESC pausa   M som' + (' [OFF]' if muted else ' [ON]'), (24, 691), 11, (101, 129, 144), mono=True)
        modules = 'ARMA +' + str(world.flags.get('weapon', 0)) + '  CASCO +' + str(world.flags.get('armor', 0)) + '  REATOR +' + str(world.flags.get('reactor', 0))
        self.text(modules, (851, 691), 10, GOLD, mono=True)

    def menu(self, t):
        self.screen.fill(INK)
        # Ilustração em camadas da estação, gerada no próprio jogo.
        for y in range(0, H, 48):
            pygame.draw.line(self.screen, (16, 29, 40), (535, y), (W, y))
        for x in range(555, W, 48):
            pygame.draw.line(self.screen, (16, 29, 40), (x, 0), (x, H))
        pygame.draw.polygon(self.screen, (19, 32, 45), [(575, 145), (1115, 75), (1199, 554), (656, 630)])
        for x in (697, 885, 1073):
            pygame.draw.rect(self.screen, (40, 59, 74), (x, 113, 16, 377), border_radius=5)
            pygame.draw.rect(self.screen, (71, 160, 171), (x + 4, 145, 3, 148))
        for y in (155, 435):
            pygame.draw.line(self.screen, (55, 81, 95), (633, y), (1159, y), 8)
        light = pygame.transform.smoothscale(self.lights['cyan'], (600, 600))
        self.screen.blit(light, (626, 10))
        chamber = pygame.Rect(865, 188, 188, 278)
        pygame.draw.rect(self.screen, (20, 57, 66), chamber, border_radius=56)
        pygame.draw.rect(self.screen, (82, 174, 175), chamber, 3, border_radius=56)
        self.screen.blit(pygame.transform.scale(self.sprites[('NINA', 0, -1)], (144, 192)), (887, 245))
        glass = pygame.Surface((188, 278), pygame.SRCALPHA)
        glass.fill((86, 210, 202, 22))
        self.screen.blit(glass, chamber)
        for y in range(215, 448, 29):
            pygame.draw.line(self.screen, (53, 111, 119), (881, y), (1038, y))
        pygame.draw.ellipse(self.screen, (9, 14, 23), (629, 545, 210, 45))
        hero = pygame.transform.scale(self.sprites[('LIA', int(t * 1.5) % 2, 1)], (192, 256))
        self.screen.blit(hero, (636, 324))
        monster = pygame.transform.scale(self.monsters[('crawler', 0)], (128, 152))
        monster.set_alpha(130)
        self.screen.blit(monster, (1091, 414))
        for i in range(30):
            x = 590 + (i * 71) % 610
            y = (i * 97 - t * (4 + i % 3)) % H
            pygame.draw.circle(self.screen, (74, 143, 156), (int(x), int(y)), 1)
        pygame.draw.line(self.screen, (51, 78, 89), (52, 59), (142, 59), 2)
        self.text('TRANSMISSÃO INTERCEPTADA / 2179', (52, 77), 12, CYAN, mono=True)
        self.text('ECO—7', (45, 115), 91, WHITE, True)
        self.text('PROTOCOLO AURORA', (53, 220), 28, CYAN, True)
        self.wrap('Sua irmã está viva. A estação não quer deixá-la sair.', (54, 279), 430, 24, WHITE)
        self.text('5 CAPÍTULOS  /  UMA PROMESSA', (54, 365), 12, GOLD, mono=True)
        self.text('AVENTURA DE RESGATE · FICÇÃO CIENTÍFICA', (54, 665), 11, MUTED, mono=True)
        self.text('NINA / SINAL VITAL DETECTADO', (806, 587), 12, CYAN, mono=True)
        self.screen.blit(self.grain, (0, 0))

    def dialogue(self, speaker, text, index, total):
        self.shade(110)
        rect = pygame.Rect(55, 424, 1090, 242)
        self.panel(rect, (13, 24, 37), (74, 117, 132))
        name = speaker.split(' · ')[0]
        portrait = self.sprites.get((name, 0, 1))
        if portrait:
            self.screen.blit(pygame.transform.scale(portrait, (120, 160)), (83, 463))
        elif name == 'VOSS':
            self.screen.blit(pygame.transform.scale(self.monsters[('boss', 0)], (143, 161)), (73, 460))
        else:
            pygame.draw.circle(self.screen, CYAN, (142, 531), 47, 2)
            for i in range(9):
                h = 13 + (i * 17) % 46
                pygame.draw.line(self.screen, CYAN, (109 + i * 8, 531 - h / 2), (109 + i * 8, 531 + h / 2), 3)
        self.text(speaker, (236, 448), 16, CYAN, True)
        self.wrap(text, (236, 483), 857, 22, WHITE, 32)
        self.text(f'E / ENTER  continuar                         {index + 1:02d}/{total:02d}', (236, 627), 13, MUTED, mono=True)
