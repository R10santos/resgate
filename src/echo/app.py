"""Estados de interface e loop da campanha ECO-7."""
from pathlib import Path
import pygame
from pygame import Vector2 as V
from .model import Campaign
from .story import CHAPTERS, LOGS, ending
from .save import SaveSlot
from .art import Renderer, W, H, CYAN, WHITE, MUTED, GOLD, RED
from .sound import Sound


class Game:
    def __init__(self, save_path=None, allow_save=True):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        self.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
        self.screen = pygame.Surface((W, H))
        pygame.display.set_caption('ECO-7 | Protocolo Aurora')
        self.renderer = Renderer(self.screen)
        pygame.display.set_icon(self.renderer.sprites[('LIA', 0, 1)])
        self.clock = pygame.time.Clock()
        self.audio = Sound()
        self.slot = SaveSlot(save_path)
        self.allow_save = allow_save
        self.saved = self.slot.read()
        self.world = Campaign()
        self.checkpoint = dict(chapter=0, flags={}, logs=[])
        self.state = 'menu'
        self.running = True
        self.selected = 0
        self.time = 0.
        self.notices = []
        self.dialogue = []
        self.dialog_index = 0
        self.dialog_after = 'playing'
        self.return_state = 'menu'
        self.mouse = V(W / 2, H / 2)
        self.shooting = False
        self.keyboard_shooting = False
        self.secondary = self.keyboard_secondary = False
        self.viewport = pygame.Rect(0, 0, W, H)
        self.result_saved = False

    def load(self, data, intro=True, persist=True):
        self.checkpoint = dict(chapter=data['chapter'], flags=dict(data.get('flags', {})), logs=list(data.get('logs', [])))
        self.world = Campaign(**self.checkpoint)
        self.renderer.floor_chapter = -1
        self.selected = 0
        self.notices.clear()
        self.result_saved = False
        self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
        if persist and self.allow_save:
            self.slot.write(**self.checkpoint)
            self.saved = self.slot.read()
        self.state = 'playing'
        if intro:
            self.show_dialogue(CHAPTERS[self.world.chapter]['intro'])

    def show_dialogue(self, lines):
        self.dialogue = list(lines)
        self.dialog_index = 0
        self.dialog_after = 'playing'
        self.state = 'dialogue'
        self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False

    def advance_dialogue(self):
        self.dialog_index += 1
        if self.dialog_index >= len(self.dialogue):
            self.state = self.dialog_after

    def options(self):
        if self.state == 'menu':
            entries = [('NOVA CAMPANHA', 'difficulty')]
            if self.saved:
                entries.insert(0, (f'CONTINUAR · CAPÍTULO {self.saved["chapter"] + 1}', 'continue'))
            return entries + [('COMO JOGAR', 'help'), ('SAIR', 'quit')]
        return {
            'paused': [('RETOMAR MISSÃO', 'resume'), ('DIÁRIO DA MISSÃO', 'journal'), ('REINICIAR CAPÍTULO', 'retry'), ('MENU PRINCIPAL', 'menu')],
            'chapter': [('AVANÇAR PARA O PRÓXIMO CAPÍTULO', 'next'), ('MENU PRINCIPAL', 'menu')],
            'lost': [('REINICIAR ESTE CAPÍTULO', 'retry'), ('MENU PRINCIPAL', 'menu')],
            'victory': [('NOVA CAMPANHA', 'difficulty'), ('MENU PRINCIPAL', 'menu')],
            'difficulty': [('EXPLORAÇÃO', 'difficulty_explore'), ('NORMAL', 'difficulty_normal'), ('SOBREVIVÊNCIA', 'difficulty_survival')],
            'upgrade': [('MELHORAR ARMA', 'module_weapon'), ('MELHORAR BLINDAGEM', 'module_armor'), ('MELHORAR REATOR', 'module_reactor')],
            'help': [('VOLTAR', 'back')],
            'journal': [('VOLTAR À MISSÃO', 'resume')],
            'map': [('VOLTAR À MISSÃO · G / ESC', 'resume')],
            'choice': [('1 · PRESERVAR A PESQUISA', 'preserve'), ('2 · DESTRUIR O ARQUIVO', 'purge')],
        }.get(self.state, [])

    def buttons(self):
        options = self.options()
        if self.state == 'menu':
            return [(pygame.Rect(54, 420 + i * 54, 411, 43), label, action) for i, (label, action) in enumerate(options)]
        if self.state == 'choice':
            return [(pygame.Rect(113 + i * 504, 562, 470, 51), label, action) for i, (label, action) in enumerate(options)]
        if self.state in ('difficulty', 'upgrade'):
            return [(pygame.Rect(63 + i * 368, 538, 337, 51), label, action) for i, (label, action) in enumerate(options)]
        y = 389 if self.state == 'paused' else 498
        if self.state in ('help', 'journal', 'map'):
            y = 626
        return [(pygame.Rect(365, y + i * 56, 470, 46), label, action) for i, (label, action) in enumerate(options)]

    def action(self, action):
        self.selected = 0
        self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
        if action == 'new':
            self.load(dict(chapter=0, flags={}, logs=[]))
        elif action.startswith('difficulty_'):
            self.load(dict(chapter=0, flags={'difficulty': action.removeprefix('difficulty_')}, logs=[]))
        elif action.startswith('module_'):
            self.world.upgrade(action.removeprefix('module_'))
            self.state = 'playing'
            self.consume_events()
        elif action == 'continue' and self.saved:
            self.load(self.saved)
        elif action == 'next':
            self.load(dict(chapter=self.world.chapter + 1, flags=self.world.flags, logs=self.world.logs))
        elif action == 'retry':
            self.load(self.checkpoint)
        elif action == 'quit':
            self.running = False
        elif action == 'resume':
            self.state = 'playing'
        elif action == 'back':
            self.state = self.return_state
        elif action == 'help':
            self.return_state = self.state
            self.state = 'help'
        elif action in ('preserve', 'purge'):
            self.world.choose(action)
            self.state = 'playing'
            self.consume_events()
        else:
            self.state = action

    def logical_mouse(self, pos):
        return V((pos[0] - self.viewport.x) * W / max(1, self.viewport.w),
                 (pos[1] - self.viewport.y) * H / max(1, self.viewport.h))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
            if self.state == 'playing':
                self.state = 'paused'
                self.selected = 0
        elif event.type == pygame.MOUSEMOTION:
            self.mouse = self.logical_mouse(event.pos)
            for i, (rect, _, _) in enumerate(self.buttons()):
                if rect.collidepoint(self.mouse):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.shooting = False
            elif event.button == 3:
                self.secondary = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.state == 'playing':
            self.mouse = self.logical_mouse(event.pos)
            self.secondary = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.mouse = self.logical_mouse(event.pos)
            if self.state == 'playing':
                self.shooting = True
            elif self.state == 'dialogue':
                self.advance_dialogue()
            else:
                for rect, _, action in self.buttons():
                    if rect.collidepoint(self.mouse):
                        self.action(action)
                        break
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_j:
                self.keyboard_shooting = False
            elif event.key == pygame.K_k:
                self.keyboard_secondary = False
        elif event.type == pygame.KEYDOWN:
            key = event.key
            if key == pygame.K_m:
                self.audio.muted = not self.audio.muted
            elif self.state == 'dialogue':
                if key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                    self.advance_dialogue()
            elif key == pygame.K_ESCAPE:
                if self.state == 'playing':
                    self.state = 'paused'
                    self.selected = 0
                    self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
                elif self.state in ('paused', 'journal', 'map'):
                    self.state = 'playing'
                elif self.state == 'help':
                    self.state = self.return_state
                elif self.state == 'difficulty':
                    self.state = 'menu'
                elif self.state == 'upgrade':
                    self.world.pending_upgrade = False
                    self.state = 'playing'
            elif self.state == 'playing':
                if key == pygame.K_e:
                    self.world.interact()
                    self.consume_events()
                elif key == pygame.K_SPACE:
                    self.world.dash()
                elif key == pygame.K_q:
                    self.world.emp()
                elif key == pygame.K_h:
                    self.world.heal()
                elif key == pygame.K_j:
                    self.keyboard_shooting = True
                elif key == pygame.K_k:
                    self.keyboard_secondary = True
                elif key == pygame.K_o:
                    self.renderer.expanded_objectives = not self.renderer.expanded_objectives
                elif key == pygame.K_c:
                    self.world.command_ally()
                    self.consume_events()
                elif key == pygame.K_g:
                    self.state = 'map'
                    self.selected = 0
                    self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
                elif key == pygame.K_TAB:
                    self.state = 'journal'
                    self.selected = 0
                    self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
            elif self.state == 'map' and key == pygame.K_g:
                self.state = 'playing'
            elif self.state == 'choice' and key in (pygame.K_1, pygame.K_2):
                self.action('preserve' if key == pygame.K_1 else 'purge')
            elif self.options():
                if key in (pygame.K_DOWN, pygame.K_s):
                    self.selected = (self.selected + 1) % len(self.options())
                elif key in (pygame.K_UP, pygame.K_w):
                    self.selected = (self.selected - 1) % len(self.options())
                elif key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.action(self.options()[self.selected][1])

    def consume_events(self):
        lines = []
        for kind, payload in self.world.events:
            if kind == 'notice':
                self.notices.append([payload, 4.5])
            elif kind == 'dialogue':
                lines.extend(payload)
            elif kind in ('choice', 'upgrade'):
                self.state = kind
                self.selected = 0
                self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False
            elif kind == 'sound':
                self.audio.play(payload)
        self.world.events.clear()
        if lines:
            self.show_dialogue(lines)
        if self.world.outcome:
            if self.world.outcome == 'chapter' and not self.result_saved and self.allow_save:
                self.slot.write(self.world.chapter + 1, self.world.flags, self.world.logs)
                self.saved = self.slot.read()
                self.result_saved = True
            self.state = self.world.outcome
            self.selected = 0
            self.shooting = self.keyboard_shooting = self.secondary = self.keyboard_secondary = False

    def update(self, dt):
        self.time += dt
        for notice in self.notices:
            notice[1] -= dt
        self.notices = [n for n in self.notices if n[1] > 0]
        if self.state != 'playing':
            return
        keys = pygame.key.get_pressed()
        direction = (int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                     int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
        self.world.update(dt, direction)
        if self.shooting or self.secondary:
            self.world.shoot(self.renderer.screen_to_world(self.mouse) - self.world.player, secondary=self.secondary)
        elif self.keyboard_shooting or self.keyboard_secondary:
            targets = [e for e in self.world.enemies if e.active and e.hp > 0 and e.pos.distance_to(self.world.player) < 550 and self.world.visible(self.world.player, e.pos)]
            target = min(targets, key=lambda e: e.pos.distance_squared_to(self.world.player)) if targets else None
            self.world.shoot(target.pos - self.world.player if target else None, secondary=self.keyboard_secondary)
        self.consume_events()

    def draw_help(self):
        r = self.renderer
        r.shade(235)
        r.text('MANUAL DE SOBREVIVÊNCIA', (70, 51), 37, WHITE, True)
        r.text('A missão é trazer pessoas de volta. Mantenha sua escolta por perto.', (72, 104), 20, CYAN)
        rows = [
            ('01 / EXPLORE', 'WASD ou setas movem Lia. O triângulo dourado e o radar indicam o próximo objetivo.'),
            ('02 / COMBATA', 'Mouse esquerdo / J: plasma. Direito / K: dispersor de curto alcance, por 20 energia. J e K têm mira assistida.'),
            ('03 / SOBREVIVA', 'Espaço esquiva (25 energia). Q libera um pulso que causa dano e atordoa (45 energia). H usa um kit.'),
            ('04 / RESGATE', 'E opera terminais, recolhe registros e liberta pessoas. Traga os aliados até a saída; E levanta quem cair.'),
            ('05 / EVOLUA', 'Bancadas douradas oferecem um módulo por fase: dano, blindagem ou reator. A escolha acompanha a campanha.'),
            ('06 / CONTINUE', 'O início de cada capítulo é salvo automaticamente. Derrota ou saída retomam esse checkpoint.'),
        ]
        for i, (title, body) in enumerate(rows):
            y = 166 + i * 71
            r.text(title, (74, y), 15, GOLD, True, mono=True)
            r.wrap(body, (263, y - 1), 865, 17, WHITE, 23)
        r.text('G: mapa com rota   C: aliado esperar/seguir   TAB: diário   O: objetivos   ESC: pausa   M: áudio', (74, 601), 14, MUTED)

    def draw_selection(self):
        r = self.renderer
        r.shade(239)
        upgrade = self.state == 'upgrade'
        r.text('PREPARE SEU EQUIPAMENTO' if upgrade else 'ESCOLHA SUA EXPERIÊNCIA', (600, 116), 40, WHITE, True, True)
        r.text('Um módulo nesta bancada. A melhoria segue com você para os próximos capítulos.' if upgrade else
               'A história é a mesma. Escolha quanto quer arriscar para chegar ao final.', (600, 182), 19, MUTED, center=True)
        cards = [
            ('PLASMA', '+5 DANO', 'Disparos mais fortes. O dispersor também ganha +2 de dano por projétil.', CYAN),
            ('BLINDAGEM', '+25 VIDA', 'Amplia a vida máxima e recupera 25 pontos imediatamente.', GOLD),
            ('REATOR', '+5 ENERGIA / S', 'Recupere energia mais rápido para esquivar, usar o pulso e disparar o dispersor.', (166, 186, 250)),
        ] if upgrade else [
            ('EXPLORAÇÃO', 'A HISTÓRIA EM PRIMEIRO LUGAR', '140 de vida e 40% menos dano recebido. Mais espaço para conhecer a estação e resgatar todos.', CYAN),
            ('NORMAL', 'COMBATE E DESCOBERTA', '100 de vida, dano padrão e os recursos originais. Use cobertura, cure-se e proteja a escolta.', GOLD),
            ('SOBREVIVÊNCIA', 'CADA DECISÃO PESA', 'Inimigos com 20% mais vida. Você e a escolta recebem 35% mais dano.', RED),
        ]
        for i, (title, metric, body, color) in enumerate(cards):
            x = 63 + i * 368
            r.panel(pygame.Rect(x, 249, 337, 264), (16, 28, 40), color)
            r.text(f'0{i+1}', (x + 23, 267), 13, color, mono=True)
            r.text(title, (x + 23, 302), 26, WHITE, True)
            r.text(metric, (x + 23, 345), 11, color, True, mono=True)
            r.wrap(body, (x + 23, 388), 288, 19, MUTED, 28)
        r.text('ESC / voltar sem escolher', (600, 635), 14, MUTED, center=True)
        if not upgrade and self.saved:
            r.text('Iniciar uma nova campanha substitui o checkpoint anterior.', (600, 670), 13, GOLD, center=True)

    def draw_journal(self):
        r = self.renderer
        r.shade(240)
        r.text('DIÁRIO DA MISSÃO', (62, 42), 38, WHITE, True)
        r.text(CHAPTERS[self.world.chapter]['title'], (65, 97), 18, CYAN)
        r.wrap(CHAPTERS[self.world.chapter]['brief'], (65, 134), 1050, 20, WHITE)
        r.text('REGISTROS RECUPERADOS', (65, 197), 13, GOLD, True, mono=True)
        if not self.world.logs:
            r.wrap('Nenhum registro encontrado. Procure os dispositivos dourados nos setores para descobrir o que aconteceu com a tripulação.', (65, 239), 1020, 20, MUTED)
        y = 227
        for key in self.world.logs:
            if key not in LOGS:
                continue
            title, body = LOGS[key]
            r.text(title, (65, y), 16, CYAN, True)
            y = r.wrap(body, (65, y + 24), 1055, 15, MUTED, 19) + 12

    def draw_choice(self):
        r = self.renderer
        r.shade(231)
        r.text('O QUE MERECE SER SALVO?', (600, 119), 42, WHITE, True, True)
        r.wrap('A fórmula pode tratar as vítimas. Também mantém Voss vivo. Não há tempo para separar todos os arquivos.', (169, 192), 863, 23, MUTED)
        for x, title, subtitle, body, color in [
            (113, 'PRESERVAR', 'UMA CURA, UM RISCO', 'Guarde a pesquisa. Voss conserva sua regeneração e será mais resistente. No resgate final, Nina poderá transmitir as provas para fora da estação.', CYAN),
            (617, 'DESTRUIR', 'UM FIM, UMA PERDA', 'Apague o arquivo e corte a regeneração de Voss. O confronto será mais curto, mas a terapia e a possibilidade de publicar as provas se perderão.', RED),
        ]:
            r.panel(pygame.Rect(x, 300, 470, 238), (17, 28, 40), color)
            r.text(subtitle, (x + 24, 323), 12, color, True, mono=True)
            r.text(title, (x + 24, 350), 30, WHITE, True)
            r.wrap(body, (x + 24, 402), 420, 19, MUTED, 28)

    def draw_result(self):
        r, w = self.renderer, self.world
        r.shade(232)
        if self.state == 'paused':
            r.text('SINAL EM ESPERA', (600, 223), 45, WHITE, True, True)
            r.text('O tempo para enquanto você está aqui.', (600, 287), 21, CYAN, center=True)
            r.text('Checkpoint: início do capítulo ' + str(w.chapter + 1), (600, 328), 16, MUTED, center=True)
        elif self.state == 'lost':
            r.text('SINAL PERDIDO', (600, 202), 49, RED, True, True)
            r.wrap(w.reason, (270, 280), 670, 23, WHITE)
            r.wrap('Dica: use o pulso Q contra grupos, esquive das áreas vermelhas e use H antes de ficar sem vida.', (270, 360), 670, 20, MUTED)
        elif self.state == 'chapter':
            r.text('CAPÍTULO CONCLUÍDO', (600, 160), 42, CYAN, True, True)
            r.text(CHAPTERS[w.chapter]['title'], (600, 221), 23, WHITE, True, True)
            summaries = ['Teo está em segurança. Ele indicou onde Ivo está escondido.',
                         'Ivo reparou o acesso e alcançou o abrigo. O laboratório está aberto.',
                         'A decisão foi tomada. Agora é preciso atravessar a contenção.',
                         'Voss foi derrotado. Nina está viva do outro lado da porta.']
            r.wrap(summaries[w.chapter], (272, 285), 665, 24, WHITE)
            r.text(f'{w.kills} ameaças neutralizadas   ·   {len(w.logs)}/5 registros recuperados', (600, 391), 18, GOLD, center=True)
            r.text('O próximo capítulo começa com vida e suprimentos restaurados.', (600, 434), 16, MUTED, center=True)
        elif self.state == 'victory':
            title, body, epilogue, count = ending(w.flags)
            r.text('NINA RESGATADA / MISSÃO CONCLUÍDA', (600, 101), 15, CYAN, True, True, True)
            r.text(title, (600, 169), 43, WHITE, True, True)
            y = r.wrap(body, (172, 233), 856, 23, WHITE, 32)
            y = r.wrap(epilogue, (172, y + 19), 856, 19, MUTED, 27)
            r.text(f'{count} pessoas resgatadas  ·  {len(w.logs)}/5 registros  ·  5 capítulos concluídos', (600, 457), 18, GOLD, center=True)

    def draw(self):
        r = self.renderer
        if self.state == 'menu':
            r.menu(self.time)
        else:
            r.world(self.world, self.time)
            r.hud(self.world, self.time, self.notices, self.audio.muted)
            if self.state == 'dialogue':
                speaker, text = self.dialogue[self.dialog_index]
                r.dialogue(speaker, text, self.dialog_index, len(self.dialogue))
            elif self.state == 'help':
                self.draw_help()
            elif self.state == 'journal':
                self.draw_journal()
            elif self.state == 'map':
                r.tactical_map(self.world)
            elif self.state == 'choice':
                self.draw_choice()
            elif self.state in ('difficulty', 'upgrade'):
                self.draw_selection()
            elif self.state in ('paused', 'lost', 'chapter', 'victory'):
                self.draw_result()
        for i, (rect, label, _) in enumerate(self.buttons()):
            r.button(rect, label, i == self.selected, i == 0)
        pygame.mouse.set_visible(self.state != 'playing')
        if self.state == 'playing' and 87 < self.mouse.y < 652:
            r.aim(self.mouse, self.world.secondary_cd <= 0)
        if self.slot.warning:
            r.text(self.slot.warning, (25, 701), 12, GOLD)

    def present(self):
        width, height = self.window.get_size()
        ratio = min(width / W, height / H)
        size = max(1, int(W * ratio)), max(1, int(H * ratio))
        self.viewport = pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)
        self.window.fill((0, 0, 0))
        image = self.screen if size == (W, H) else pygame.transform.smoothscale(self.screen, size)
        self.window.blit(image, self.viewport)
        pygame.display.flip()

    def run(self, frames=None, screenshot=None):
        count = 0
        while self.running and (frames is None or count < frames):
            dt = min(self.clock.tick(60) / 1000, .1)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
            self.present()
            count += 1
        if screenshot:
            path = Path(screenshot)
            path.parent.mkdir(parents=True, exist_ok=True)
            pygame.image.save(self.screen, str(path))
        pygame.quit()
