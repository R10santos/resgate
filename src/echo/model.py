"""Simulação da campanha: mapas, combate, IA, escolta e objetivos encadeados."""
from collections import deque
from dataclasses import dataclass, field
import pygame
from pygame import Vector2 as V
from .story import LOGS

TILE = 48
COLS, ROWS = 36, 23
WORLD_W, WORLD_H = COLS * TILE, ROWS * TILE


def at(x, y):
    return V((x + .5) * TILE, (y + .5) * TILE)


@dataclass
class Node:
    id: str
    name: str
    kind: str
    pos: V
    done: bool = False


@dataclass
class Enemy:
    kind: str
    pos: V
    hp: float
    max_hp: float
    cooldown: float = 1.0
    windup: float = 0
    stun: float = 0
    path_timer: float = 0
    path: list = field(default_factory=list)
    facing: V = field(default_factory=lambda: V(-1, 0))
    active: bool = True
    flash: float = 0
    enraged: bool = False


@dataclass
class Shot:
    pos: V
    velocity: V
    friendly: bool
    damage: float
    life: float = 1.5


class Campaign:
    def __init__(self, chapter=0, flags=None, logs=None):
        self.chapter = chapter
        self.flags = dict(flags or {})
        self.logs = list(logs or [])
        self.player = at(3, 5 if chapter == 4 else 17)
        self.facing = V(1, 0)
        self.difficulty = self.flags.get('difficulty', 'normal')
        self.max_hp = (140 if self.difficulty == 'explore' else 100) + 25 * self.flags.get('armor', 0)
        self.hp, self.energy = float(self.max_hp), 100.
        self.medkits = 3
        self.invincible = self.shot_cd = self.dash_left = self.emp_cd = 0.
        self.elapsed = 0.
        self.moving = False
        self.secondary_cd = 0.
        self.muzzle = 0.
        self.floaters = []
        self.corpses = []
        self.pending_upgrade = False
        self.hazard_tiles = [(13, 13), (22, 13), (29, 10)] if chapter in (1, 4) else []
        self.shots = []
        self.effects = []
        self.dangers = []
        self.events = []
        self.outcome = None
        self.reason = ''
        self.kills = 0
        self.timer = None
        self.ally = None
        self.ally_name = ''
        self.ally_waiting = False
        self.ally_hp = 100.
        self.ally_path = []
        self.ally_tick = 0.
        self.ally_invincible = 0.
        self.nodes = []
        self.walls = self.make_map()
        self.build_nodes()
        positions = [(8, 7), (18, 8), (28, 7), (8, 19), (20, 18), (29, 19), (31, 14)]
        if chapter > 0:
            positions += [(16, 15), (29, 3)]
        if chapter > 2:
            positions += [(10, 3), (22, 7)]
        self.enemies = []
        for i, pos in enumerate(positions):
            kind = ('crawler', 'spitter', 'brute')[(i + chapter) % 3]
            hp = {'crawler': 58, 'spitter': 48, 'brute': 115}[kind]
            self.enemies.append(Enemy(kind, at(*pos), hp, hp, cooldown=.5 + i * .12))
        if chapter == 3:
            hp = 530 if self.flags.get('protocol') == 'purge' else 680
            self.enemies.append(Enemy('boss', at(29, 17), hp, hp, active=False))
        if self.difficulty == 'survival':
            for enemy in self.enemies:
                enemy.hp *= 1.2
                enemy.max_hp = enemy.hp

    def make_map(self):
        walls = {(x, y) for x in range(COLS) for y in range(ROWS)
                 if x in (0, COLS - 1) or y in (0, ROWS - 1)}
        for x in (12, 24):
            for y in range(1, ROWS - 1):
                if self.chapter in (2, 3) and y > 11:
                    continue  # enfermaria aberta e arena ampla
                if self.chapter == 1 and 9 <= y <= 15:
                    continue  # passarela industrial contínua
                if y not in (4, 5, 6, 16, 17, 18):
                    walls.add((x, y))
        for x in range(1, COLS - 1):
            if self.chapter == 1 and 12 < x < 24:
                continue
            if x not in (4, 5, 6, 7, 16, 17, 18, 19, 28, 29, 30, 31):
                walls.add((x, 11))
        # Pilares fora dos corredores e pontos de missão.
        for x, y in ([(3, 8), (21, 3), (32, 8), (15, 20)] if self.chapter % 2 == 0
                     else [(9, 3), (15, 8), (32, 20), (3, 14)]):
            walls.add((x, y))
        covers = [
            [(3, 3), (4, 3), (9, 8), (10, 8), (17, 19), (18, 19), (28, 3), (32, 8)],
            [(8, 8), (9, 8), (8, 9), (9, 9), (20, 8), (21, 8), (20, 9), (21, 9), (27, 15), (28, 15)],
            [(x, 7) for x in (3, 6, 9, 15, 18, 21, 27, 30, 33)],
            [(26, 14), (32, 14), (26, 20), (32, 20)],
            [(9, 8), (10, 8), (20, 14), (21, 14), (27, 20), (28, 20)],
        ][self.chapter]
        self.covers = set(covers)
        walls.update(covers)
        return walls

    def build_nodes(self):
        layouts = [
            [('power', 'Gerador das docas', 'console', 6, 17), ('key', 'Crachá de segurança', 'key', 6, 5),
             ('teo', 'Teo · tripulante ferido', 'npc', 18, 5), ('exit', 'Abrigo / elevador', 'exit', 31, 17),
             ('dock_log', 'Manifesto de carga', 'log', 30, 5)],
            [('ivo', 'Ivo · engenheiro', 'npc', 6, 17), ('relay_a', 'Relé oeste', 'console', 6, 5),
             ('relay_b', 'Relé leste', 'console', 18, 5), ('exit', 'Elevador do laboratório', 'exit', 31, 17),
             ('engine_log', 'Mensagem não enviada', 'log', 30, 5)],
            [('formula', 'Fórmula do estabilizador', 'console', 6, 5), ('sample', 'Amostra de Aurora', 'sample', 18, 5),
             ('decision', 'Arquivo central', 'console', 30, 5), ('maia', 'Dra. Maia · sobrevivente', 'npc', 18, 17),
             ('exit', 'Acesso à contenção', 'exit', 31, 17), ('lab_log', 'Relatório clínico', 'log', 5, 18)],
            [('seal_a', 'Selo oeste', 'console', 6, 5), ('seal_b', 'Selo central', 'console', 18, 5),
             ('seal_c', 'Selo leste', 'console', 30, 5), ('exit', 'Porta do núcleo', 'exit', 32, 18),
             ('core_log', 'Ordens de Voss', 'log', 18, 17)],
            [('nina', 'Nina · suporte neural', 'npc', 6, 5), ('stabilizer', 'Preparar estabilizador', 'console', 18, 5),
             ('valve', 'Válvula de emergência', 'console', 18, 17), ('broadcast', 'Antena de transmissão', 'console', 30, 5),
             ('exit', 'Nave de evacuação', 'exit', 31, 17), ('escape_log', 'Último registro de Íris', 'log', 5, 18)],
        ]
        for id_, name, kind, x, y in layouts[self.chapter]:
            self.nodes.append(Node(id_, name, kind, at(x, y)))
        for i, pos in enumerate(((8, 15), (20, 3), (33, 15))):
            self.nodes.append(Node('med' + str(i), 'Kit médico', 'med', at(*pos)))
        self.nodes.append(Node('upgrade', 'Bancada de aprimoramento', 'upgrade', at(20, 19)))

    def node(self, id_):
        return next((n for n in self.nodes if n.id == id_), None)

    def done(self, id_):
        n = self.node(id_)
        return bool(n and n.done)

    def notice(self, text):
        self.events.append(('notice', text))

    def say(self, speaker, text):
        self.events.append(('dialogue', [(speaker, text)]))

    def solid(self, pos, radius=15):
        for x in range(int((pos.x - radius) // TILE), int((pos.x + radius) // TILE) + 1):
            for y in range(int((pos.y - radius) // TILE), int((pos.y + radius) // TILE) + 1):
                if (x, y) in self.walls or not (0 <= x < COLS and 0 <= y < ROWS):
                    rect = pygame.Rect(x * TILE, y * TILE, TILE, TILE)
                    nearest = V(max(rect.left, min(pos.x, rect.right)), max(rect.top, min(pos.y, rect.bottom)))
                    if pos.distance_squared_to(nearest) < radius ** 2:
                        return True
        return False

    def move(self, pos, movement, radius=15):
        for axis in (0, 1):
            candidate = pos.copy()
            candidate[axis] += movement[axis]
            if not self.solid(candidate, radius):
                pos[axis] = candidate[axis]

    def path(self, start, target):
        a = (int(start.x // TILE), int(start.y // TILE))
        b = (int(target.x // TILE), int(target.y // TILE))
        queue = deque([a])
        came = {a: None}
        while queue:
            here = queue.popleft()
            if here == b:
                result = []
                while here != a:
                    result.append(at(*here))
                    here = came[here]
                return result[::-1]
            x, y = here
            for cell in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 < cell[0] < COLS - 1 and 0 < cell[1] < ROWS - 1 and cell not in self.walls and cell not in came:
                    came[cell] = here
                    queue.append(cell)
        return []

    def visible(self, a, b, radius=3):
        distance = a.distance_to(b)
        steps = max(1, int(distance / 18))
        return all(not self.solid(a.lerp(b, i / steps), radius) for i in range(1, steps + 1))

    def shoot(self, direction=None, secondary=False):
        if secondary:
            return self.scatter(direction)
        if self.outcome or self.shot_cd > 0:
            return
        if direction is not None and V(direction).length_squared() > 0:
            self.facing = V(direction).normalize()
        self.shot_cd = .21
        self.shots.append(Shot(self.player + self.facing * 20, self.facing * 690, True, 24 + self.flags.get('weapon', 0) * 5))
        self.muzzle = .065
        self.events.append(('sound', 'shoot'))

    def scatter(self, direction=None):
        if self.outcome or self.secondary_cd > 0 or self.energy < 20:
            return False
        if direction is not None and V(direction).length_squared():
            self.facing = V(direction).normalize()
        self.energy -= 20
        self.secondary_cd = .8
        self.muzzle = .12
        for angle in (-16, -8, 0, 8, 16):
            aim = self.facing.rotate(angle)
            self.shots.append(Shot(self.player + aim * 21, aim * 650, True, 15 + self.flags.get('weapon', 0) * 2, .43))
        self.events.append(('sound', 'scatter'))
        return True

    def dash(self):
        if not self.outcome and self.energy >= 25 and self.dash_left <= 0:
            self.energy -= 25
            self.dash_left = .18
            self.invincible = max(self.invincible, .24)
            self.events.append(('sound', 'dash'))

    def emp(self):
        if self.outcome or self.energy < 45 or self.emp_cd > 0:
            return
        self.energy -= 45
        self.emp_cd = 3
        self.effects.append([self.player.copy(), .55, 'emp'])
        for e in self.enemies:
            if e.active and e.hp > 0 and e.pos.distance_to(self.player) < 195 and self.visible(self.player, e.pos):
                e.hp -= 45
                e.stun = 1.8 if e.kind != 'boss' else .4
        self.events.append(('sound', 'emp'))

    def heal(self):
        if self.medkits and self.hp < self.max_hp and not self.outcome:
            self.medkits -= 1
            self.hp = min(self.max_hp, self.hp + 65)
            self.effects.append([self.player.copy(), .6, 'heal'])
            self.events.append(('sound', 'heal'))

    def nearest(self):
        nodes = [n for n in self.nodes if not n.done and n.pos.distance_to(self.player) < 86]
        return min(nodes, key=lambda n: n.pos.distance_squared_to(self.player)) if nodes else None

    def join(self, name, node):
        self.ally = node.pos.copy()
        self.ally_name = name
        self.ally_waiting = False
        self.ally_hp = 100
        self.ally_tick = 0
        self.ally_path = []
        node.done = True

    def command_ally(self):
        if self.ally is None:
            self.notice('Nenhum aliado está em escolta neste momento.')
            return
        if self.ally_hp <= 0:
            self.notice('Aproxime-se e use E para levantar ' + self.ally_name + '.')
            return
        self.ally_waiting = not self.ally_waiting
        self.ally_tick = 0
        self.ally_path.clear()
        self.notice(self.ally_name + (' vai esperar aqui. C para voltar a seguir.' if self.ally_waiting else ' está seguindo você.'))

    def objective_route(self):
        """Rota de navegação até o objetivo, sem alterar a física ou o objetivo."""
        target = self.target()
        if target is None:
            return []
        if self.visible(self.player, target, 16):
            return [target.copy()]
        return self.path(self.player, target)

    def interact(self):
        if self.outcome:
            return
        if self.ally is not None and self.ally_hp <= 0 and self.player.distance_to(self.ally) < 90:
            self.ally_hp = 60
            self.ally_invincible = 4
            self.notice(self.ally_name + ' voltou a caminhar. Proteja a escolta!')
            return
        n = self.nearest()
        if not n:
            return
        id_ = n.id
        if n.kind == 'upgrade':
            self.pending_upgrade = True
            self.events.append(('upgrade', None))
        elif n.kind == 'log':
            n.done = True
            if id_ not in self.logs:
                self.logs.append(id_)
            title, text = LOGS[id_]
            self.say(title, text)
        elif n.kind == 'med':
            n.done = True
            self.medkits += 1
            self.notice('Kit médico recolhido. Pressione H para recuperar vida.')
        elif id_ == 'exit':
            self.exit_level()
        elif self.chapter == 0:
            if id_ == 'power':
                n.done = True
                self.say('ÍRIS', 'Energia auxiliar restaurada. Um crachá está na sala oeste. Detecto um sobrevivente na enfermaria central.')
            elif id_ == 'key':
                if not self.done('power'):
                    self.notice('O armário está travado. Ligue o gerador das docas.')
                else:
                    n.done = True
                    self.notice('Crachá adquirido. Encontre Teo na enfermaria central.')
            elif id_ == 'teo':
                if not self.done('key'):
                    self.notice('O leito está lacrado. Encontre o crachá de segurança.')
                else:
                    self.join('TEO', n)
                    self.say('TEO', 'Nina mandou Ivo se esconder na manutenção. Eu posso indicar o acesso, mas não consigo correr. Me leve ao abrigo nas docas leste.')
        elif self.chapter == 1:
            if id_ == 'ivo':
                self.join('IVO', n)
                self.say('IVO', 'Vou seguir você. Para operar cada relé, preciso estar perto. Se eu cair, volte e me ajude com E.')
            elif id_.startswith('relay'):
                if self.ally is None or self.ally.distance_to(n.pos) > 155 or self.ally_hp <= 0:
                    self.notice('Ivo precisa estar de pé e perto do relé para repará-lo.')
                else:
                    n.done = True
                    self.notice('Relé reparado. ' + ('Acesso ao elevador liberado.' if self.done('relay_a') and self.done('relay_b') else 'Falta o outro relé.'))
        elif self.chapter == 2:
            if id_ in ('formula', 'sample'):
                n.done = True
                self.say('NINA · REGISTRO', 'A fórmula vai manter meu coração estável fora da rede.' if id_ == 'formula' else 'Esta amostra conserva a terapia original. Voss ainda depende dela para regenerar o próprio corpo.')
            elif id_ == 'decision':
                if not self.done('formula') or not self.done('sample'):
                    self.notice('Recupere a fórmula e a amostra antes de abrir o arquivo central.')
                else:
                    self.events.append(('choice', None))
            elif id_ == 'maia':
                self.join('MAIA', n)
                self.say('MAIA', 'Eu assinei os primeiros relatórios. Achei que era uma cura. Se você me tirar daqui, vou testemunhar contra Voss.')
        elif self.chapter == 3:
            if id_.startswith('seal'):
                n.done = True
                self.notice('Selo de contenção desativado.')
                if all(self.done(s) for s in ('seal_a', 'seal_b', 'seal_c')):
                    boss = next(e for e in self.enemies if e.kind == 'boss')
                    boss.active = True
                    self.say('VOSS', 'Você abriu todas as portas. Agora vai ouvir o que eu ouço!')
        elif self.chapter == 4:
            if id_ == 'stabilizer':
                n.done = True
                self.say('LIA', 'Estabilizador pronto. Agora posso desconectar Nina. O colapso começa quando eu a retirar do suporte.')
            elif id_ == 'nina':
                if not self.done('stabilizer'):
                    self.notice('Prepare primeiro o estabilizador na bancada central.')
                else:
                    self.join('NINA', n)
                    self.timer = 180.
                    self.say('NINA', 'Estou com você. A válvula no anel inferior pode atrasar o colapso. Não deixe a pesquisa desaparecer se ainda pudermos enviar as provas.')
            elif id_ == 'valve':
                if self.timer is None:
                    self.notice('A válvula só responde durante a evacuação.')
                else:
                    n.done = True
                    self.timer += 60
                    self.notice('Pressão reduzida. +60 segundos para evacuar.')
            elif id_ == 'broadcast':
                if self.flags.get('protocol') != 'preserve':
                    self.notice('O arquivo foi destruído. Não há pesquisa para transmitir.')
                elif not self.done('nina'):
                    self.notice('Nina precisa ser libertada para autenticar a transmissão.')
                elif self.ally is None or self.ally.distance_to(n.pos) > 155 or self.ally_hp <= 0:
                    self.notice('Traga Nina até a antena para autenticar as provas.')
                else:
                    n.done = True
                    self.flags['broadcast'] = True
                    self.say('ÍRIS', 'Provas enviadas. Incluí os nomes das vítimas. Obrigada por me deixar escolher, Lia.')
        self.events.append(('sound', 'interact'))

    def upgrade(self, module):
        if not self.pending_upgrade or module not in ('weapon', 'armor', 'reactor') or self.done('upgrade'):
            return False
        self.pending_upgrade = False
        self.node('upgrade').done = True
        self.flags[module] = min(5, self.flags.get(module, 0) + 1)
        if module == 'armor':
            self.max_hp += 25
            self.hp = min(self.max_hp, self.hp + 25)
        self.notice({'weapon': 'Plasma aprimorado: +5 de dano por disparo.', 'armor': 'Blindagem aprimorada: +25 de vida máxima.',
                     'reactor': 'Reator aprimorado: +5 de energia recuperada por segundo.'}[module])
        self.events.append(('sound', 'heal'))
        return True

    def hazard_state(self, index):
        phase = (self.elapsed + index * 1.7) % 6
        return 'active' if phase >= 4.8 else 'warning' if phase >= 3.8 else 'off'

    def choose(self, protocol):
        if self.chapter != 2 or protocol not in ('preserve', 'purge') or not self.done('formula') or not self.done('sample'):
            return
        self.flags['protocol'] = protocol
        self.node('decision').done = True
        self.say('LIA', 'Vou preservar a fórmula e expor o que Voss fez. A cura não pertence a ele.' if protocol == 'preserve'
                 else 'Desative a regeneração de Voss e apague a pesquisa. Não vou deixar que repitam isso.')

    def exit_level(self):
        requirements = [('power', 'key', 'teo'), ('ivo', 'relay_a', 'relay_b'), ('formula', 'sample', 'decision'),
                        ('seal_a', 'seal_b', 'seal_c'), ('stabilizer', 'nina')][self.chapter]
        if not all(self.done(s) for s in requirements):
            self.notice('Acesso bloqueado. Conclua os objetivos da missão.')
            return
        if self.chapter == 3 and any(e.kind == 'boss' and e.hp > 0 for e in self.enemies):
            self.notice('Voss ainda controla a porta. Derrote-o primeiro.')
            return
        if self.ally is not None and (self.ally.distance_to(self.node('exit').pos) > 180 or self.ally_hp <= 0):
            self.notice('Não deixe ' + self.ally_name + ' para trás. ' + ('Use C para voltar a seguir.' if self.ally_waiting else 'Traga a escolta até a saída.'))
            return
        if self.chapter in (0, 1):
            self.flags[('teo', 'ivo')[self.chapter]] = True
        if self.chapter == 2 and self.ally_name == 'MAIA':
            self.flags['maia'] = True
        self.outcome = 'victory' if self.chapter == 4 else 'chapter'

    def objectives(self):
        rows = [
            [('power', 'Religar o gerador'), ('key', 'Obter o crachá'), ('teo', 'Libertar Teo'), ('exit', 'Escoltar Teo ao abrigo')],
            [('ivo', 'Encontrar Ivo'), ('relay_a', 'Reparar o relé oeste com Ivo'), ('relay_b', 'Reparar o relé leste com Ivo'), ('exit', 'Escoltar Ivo ao elevador')],
            [('formula', 'Recuperar a fórmula'), ('sample', 'Coletar a amostra'), ('decision', 'Decidir o destino da pesquisa'), ('exit', 'Chegar à contenção'), ('maia', 'Opcional: resgatar Dra. Maia')],
            [('seal_a', 'Desativar o selo oeste'), ('seal_b', 'Desativar o selo central'), ('seal_c', 'Desativar o selo leste'), ('boss', 'Derrotar Voss'), ('exit', 'Entrar no núcleo')],
            [('stabilizer', 'Preparar o estabilizador'), ('nina', 'Libertar Nina'), ('exit', 'Escoltar Nina até a nave')],
        ][self.chapter]
        if self.chapter == 4:
            rows = rows + [('valve', 'Opcional: ganhar +60 segundos')]
            if self.flags.get('protocol') == 'preserve':
                rows = rows + [('broadcast', 'Opcional: transmitir as provas')]
        return [(id_, label, (not any(e.kind == 'boss' and e.hp > 0 for e in self.enemies) if id_ == 'boss' else self.done(id_))) for id_, label in rows]

    def target(self):
        for id_, label, complete in self.objectives():
            if label.startswith('Opcional:'):
                continue
            if not complete:
                if id_ == 'boss':
                    e = next((e for e in self.enemies if e.kind == 'boss'), None)
                    return e.pos if e else None
                return self.node(id_).pos

    def hurt(self, amount, ally=False):
        amount *= {'explore': .6, 'normal': 1, 'survival': 1.35}.get(self.difficulty, 1)
        if ally:
            if self.ally is not None and self.ally_invincible <= 0 and self.ally_hp > 0:
                self.ally_hp = max(0, self.ally_hp - amount)
                self.ally_invincible = 1.1
                if self.ally_hp <= 0:
                    self.notice(self.ally_name + ' caiu! Aproxime-se e pressione E para ajudar.')
        elif self.invincible <= 0:
            self.hp = max(0, self.hp - amount)
            self.invincible = .7
            self.effects.append([self.player.copy(), .3, 'hit'])
            self.events.append(('sound', 'hit'))
            if self.hp <= 0:
                self.outcome = 'lost'
                self.reason = 'Lia foi abatida. Reinicie do começo deste capítulo.'

    def update(self, dt, direction=(0, 0)):
        if self.outcome:
            return
        remaining = min(.1, max(0, dt))
        while remaining > 1e-8 and not self.outcome:
            step = min(remaining, 1 / 90)
            self.step(step, V(direction))
            remaining -= step

    def step(self, dt, direction):
        self.elapsed += dt
        for name in ('invincible', 'shot_cd', 'emp_cd', 'ally_invincible', 'secondary_cd', 'muzzle'):
            setattr(self, name, max(0, getattr(self, name) - dt))
        self.energy = min(100, self.energy + dt * (17 + self.flags.get('reactor', 0) * 5))
        self.moving = bool(direction.length_squared())
        if self.moving:
            direction = direction.normalize()
            if self.dash_left <= 0:
                self.facing = direction
        self.move(self.player, (self.facing * 610 if self.dash_left > 0 else direction * 185) * dt)
        self.dash_left = max(0, self.dash_left - dt)
        if self.timer is not None:
            self.timer = max(0, self.timer - dt)
            if self.timer == 0:
                self.outcome = 'lost'
                self.reason = 'A estação colapsou antes da evacuação. Recomece o capítulo.'
        self.update_ally(dt)
        for i, tile in enumerate(self.hazard_tiles):
            if self.hazard_state(i) == 'active' and self.player.distance_to(at(*tile)) < 35:
                self.hurt(12)
        for enemy in self.enemies:
            enemy.flash = max(0, enemy.flash - dt)
            if enemy.hp > 0 and enemy.active:
                self.update_enemy(enemy, dt)
        for shot in self.shots[:]:
            shot.life -= dt
            shot.pos += shot.velocity * dt
            dead = shot.life <= 0 or self.solid(shot.pos, 4)
            if not dead and shot.friendly:
                for e in self.enemies:
                    if e.hp > 0 and e.active and shot.pos.distance_to(e.pos) < (36 if e.kind == 'boss' else 23):
                        e.hp -= shot.damage
                        e.flash = .11
                        self.floaters.append([e.pos.copy(), .65, str(int(shot.damage))])
                        self.effects.append([shot.pos.copy(), .16, 'spark'])
                        dead = True
                        break
            elif not dead:
                if shot.pos.distance_to(self.player) < 18:
                    self.hurt(shot.damage)
                    dead = True
                elif self.ally is not None and shot.pos.distance_to(self.ally) < 18:
                    self.hurt(shot.damage, True)
                    dead = True
            if dead:
                self.shots.remove(shot)
        for e in self.enemies[:]:
            if e.hp <= 0:
                self.kills += 1
                self.corpses.append((e.pos.copy(), e.kind))
                self.effects.append([e.pos.copy(), .8, 'death'])
                self.enemies.remove(e)
                if e.kind == 'boss':
                    self.say('ÍRIS', 'Voss perdeu o controle da rede. Nina está viva no núcleo. Vá. Eu mantenho a porta aberta.')
                elif self.kills % 4 == 0:
                    self.nodes.append(Node('drop' + str(self.kills), 'Kit médico', 'med', e.pos.copy()))
        for danger in self.dangers[:]:
            danger[1] -= dt
            if danger[1] <= 0:
                if self.player.distance_to(danger[0]) < danger[2]:
                    self.hurt(28)
                if self.ally is not None and self.ally.distance_to(danger[0]) < danger[2]:
                    self.hurt(25, True)
                self.effects.append([danger[0], .45, 'blast'])
                self.dangers.remove(danger)
        for effect in self.effects:
            effect[1] -= dt
        self.effects = [e for e in self.effects if e[1] > 0]
        for floater in self.floaters:
            floater[0].y -= dt * 34
            floater[1] -= dt
        self.floaters = [f for f in self.floaters if f[1] > 0]

    def update_ally(self, dt):
        if self.ally is None or self.ally_hp <= 0 or self.ally_waiting:
            return
        self.ally_tick -= dt
        distance = self.ally.distance_to(self.player)
        if distance < 64:
            return
        if self.visible(self.ally, self.player, 16):
            delta = self.player - self.ally
        else:
            if self.ally_tick <= 0:
                self.ally_path = self.path(self.ally, self.player)
                self.ally_tick = .5
            while self.ally_path and self.ally.distance_to(self.ally_path[0]) < 8:
                self.ally_path.pop(0)
            delta = self.ally_path[0] - self.ally if self.ally_path else V()
        if delta.length_squared():
            self.move(self.ally, delta.normalize() * (160 if distance > 220 else 137) * dt)

    def update_enemy(self, e, dt):
        e.stun = max(0, e.stun - dt)
        if e.stun > 0:
            return
        target = self.player
        ally_target = False
        if self.ally is not None and self.ally_hp > 0 and e.pos.distance_to(self.ally) < e.pos.distance_to(target) * .8:
            target, ally_target = self.ally, True
        distance = e.pos.distance_to(target)
        if distance > (900 if e.kind == 'boss' else 620):
            return
        e.cooldown -= dt
        e.path_timer -= dt
        delta = target - e.pos
        if delta.length_squared():
            e.facing = delta.normalize()
        sight = self.visible(e.pos, target)
        if e.kind == 'boss':
            if e.hp < e.max_hp / 2 and not e.enraged:
                e.enraged = True
                self.notice('Voss rompeu a contenção! Mutantes estão entrando na arena.')
                for pos in (at(27, 17), at(31, 17)):
                    self.enemies.append(Enemy('crawler', pos, 58, 58, cooldown=1.5))
            if e.cooldown <= 0:
                e.cooldown = 2.0 if e.hp < e.max_hp / 2 else 2.8
                self.dangers.append([target.copy(), 1.05, 93])
                for i in range(10 if e.hp < e.max_hp / 2 else 7):
                    velocity = V(220, 0).rotate(i * 360 / (10 if e.hp < e.max_hp / 2 else 7) + self.elapsed * 15)
                    self.shots.append(Shot(e.pos.copy(), velocity, False, 19, 3))
            speed = 63
        elif e.kind == 'spitter':
            if sight and distance < 490 and e.cooldown <= 0:
                e.cooldown = 1.75
                self.shots.append(Shot(e.pos + e.facing * 25, e.facing * 280, False, 15, 2.4))
            if sight and 170 < distance < 380:
                return
            speed = 78
        else:
            if e.windup > 0:
                e.windup -= dt
                if e.windup <= 0:
                    if distance < 85 and sight:
                        self.hurt(24 if e.kind == 'brute' else 14, ally_target)
                    e.cooldown = 1.3
                return
            if distance < 65 and e.cooldown <= 0 and sight:
                e.windup = .6 if e.kind == 'brute' else .38
                return
            if distance < 40:
                return
            speed = 67 if e.kind == 'brute' else 105
        if not self.visible(e.pos, target, 26 if e.kind == 'boss' else 18):
            if e.path_timer <= 0:
                e.path = self.path(e.pos, target)
                e.path_timer = .65
            while e.path and e.pos.distance_to(e.path[0]) < 8:
                e.path.pop(0)
            delta = e.path[0] - e.pos if e.path else V()
        if delta.length_squared():
            self.move(e.pos, delta.normalize() * speed * dt, 25 if e.kind == 'boss' else 17)
