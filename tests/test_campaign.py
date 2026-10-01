"""Validação de progressão, combate, escolta, checkpoints e UI da campanha."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import tempfile
import unittest
from pathlib import Path
import pygame
from pygame import Vector2 as V
from src.echo.model import Campaign, Enemy, at
from src.echo.save import SaveSlot
from src.echo.story import ending, LOGS
from src.echo.app import Game


def interact(w, name, bring_ally=False):
    w.player = w.node(name).pos.copy()
    if bring_ally and w.ally is not None:
        w.ally = w.player + V(40, 0)
    w.interact()


class CampaignTests(unittest.TestCase):
    def test_all_objectives_reachable_and_actors_outside_walls(self):
        signatures = set()
        for chapter in range(5):
            w = Campaign(chapter)
            signatures.add(frozenset(w.walls))
            self.assertFalse(w.solid(w.player))
            for n in w.nodes:
                with self.subTest(chapter=chapter, node=n.id):
                    self.assertFalse(w.solid(n.pos))
                    self.assertTrue(w.path(w.player, n.pos))
            for e in w.enemies:
                self.assertFalse(w.solid(e.pos, 25 if e.kind == 'boss' else 17))
        self.assertEqual(len(signatures), 5)

    def test_full_story_both_choices(self):
        for choice in ('preserve', 'purge'):
            flags = {}
            for chapter in range(5):
                w = Campaign(chapter, flags)
                interact(w, 'exit')
                self.assertIsNone(w.outcome)
                if chapter == 0:
                    interact(w, 'teo')
                    self.assertIsNone(w.ally)
                    interact(w, 'key')
                    self.assertFalse(w.done('key'))
                    for id_ in ('power', 'key', 'teo'):
                        interact(w, id_)
                    interact(w, 'exit')
                    self.assertIsNone(w.outcome, 'escort must reach exit')
                elif chapter == 1:
                    interact(w, 'relay_a')
                    self.assertFalse(w.done('relay_a'))
                    interact(w, 'ivo')
                    for id_ in ('relay_a', 'relay_b'):
                        interact(w, id_, True)
                elif chapter == 2:
                    interact(w, 'decision')
                    self.assertFalse(w.done('decision'))
                    for id_ in ('formula', 'sample', 'maia', 'decision'):
                        interact(w, id_)
                    self.assertIn(('choice', None), w.events)
                    w.choose(choice)
                    self.assertEqual(w.flags['protocol'], choice)
                elif chapter == 3:
                    boss = next(e for e in w.enemies if e.kind == 'boss')
                    self.assertFalse(boss.active)
                    for id_ in ('seal_a', 'seal_b', 'seal_c'):
                        interact(w, id_)
                    self.assertTrue(boss.active)
                    interact(w, 'exit')
                    self.assertIsNone(w.outcome)
                    boss.hp = 0  # progressão após combate é testada separadamente
                else:
                    interact(w, 'nina')
                    self.assertIsNone(w.timer)
                    interact(w, 'stabilizer')
                    interact(w, 'nina')
                    self.assertEqual(w.timer, 180)
                    interact(w, 'valve')
                    self.assertEqual(w.timer, 240)
                    interact(w, 'broadcast', True)
                    self.assertEqual(w.flags.get('broadcast', False), choice == 'preserve')
                interact(w, 'exit', True)
                self.assertEqual(w.outcome, 'victory' if chapter == 4 else 'chapter')
                flags = w.flags.copy()
            title, _, _, saved = ending(flags)
            self.assertEqual(saved, 4)
            self.assertEqual(title, 'AMANHÃ AINDA EXISTE' if choice == 'preserve' else 'AS CINZAS DE AURORA')
        self.assertEqual(ending({'protocol': 'preserve'})[0], 'A CURA NO ESCURO')

    def test_ally_follows_path_through_doorways_and_can_be_revived(self):
        w = Campaign(1)
        w.enemies.clear()
        interact(w, 'ivo')
        w.player = at(18, 5)
        for _ in range(1600):
            w.update(.02)
            if w.ally.distance_to(w.player) < 70:
                break
        self.assertLess(w.ally.distance_to(w.player), 70)
        w.ally_hp = 0
        w.ally_invincible = 0
        w.interact()
        self.assertEqual(w.ally_hp, 60)

    def test_projectiles_cannot_cross_walls_and_hit_mutants(self):
        w = Campaign()
        w.player = at(10, 9)
        e = Enemy('crawler', at(14, 9), 58, 58, stun=10)
        w.enemies = [e]
        w.shoot(V(1, 0))
        for _ in range(40):
            w.update(.025)
        self.assertEqual(e.hp, 58)
        w.player = at(18, 17)
        e.pos = w.player + V(100, 0)
        e.active = True
        e.stun = 10
        for _ in range(3):
            w.shoot(V(1, 0))
            for _ in range(15):
                w.update(.02)
        self.assertNotIn(e, w.enemies)
        self.assertEqual(w.kills, 1)

    def test_boss_regeneration_choice_telegraph_and_phase(self):
        preserve = Campaign(3, {'protocol': 'preserve'})
        purge = Campaign(3, {'protocol': 'purge'})
        boss = next(e for e in preserve.enemies if e.kind == 'boss')
        self.assertGreater(boss.hp, next(e.hp for e in purge.enemies if e.kind == 'boss'))
        preserve.enemies = [boss]
        boss.active = True
        boss.cooldown = 0
        preserve.player = boss.pos + V(-150, 0)
        preserve.update(.02)
        self.assertEqual(len(preserve.dangers), 1)
        self.assertEqual(len(preserve.shots), 7)
        preserve.shots.clear()
        boss.hp = boss.max_hp / 3
        boss.cooldown = 0
        preserve.update(.02)
        self.assertEqual(len(preserve.shots), 10)

    def test_energy_health_timeout_and_immutable_result(self):
        w = Campaign(4)
        w.enemies.clear()
        w.hp = 20
        w.heal()
        self.assertEqual(w.hp, 85)
        self.assertEqual(w.medkits, 2)
        w.dash()
        self.assertEqual(w.energy, 75)
        w.hurt(100)
        self.assertEqual(w.hp, 85)
        w.emp()
        self.assertEqual(w.energy, 30)
        w.timer = .01
        w.update(.02)
        self.assertEqual(w.outcome, 'lost')
        p = w.player.copy()
        w.update(.1, (1, 0))
        self.assertEqual(w.player, p)

    def test_collectibles_do_not_repeat_and_optional_maia(self):
        w = Campaign(2)
        interact(w, 'lab_log')
        interact(w, 'lab_log')
        self.assertEqual(w.logs, ['lab_log'])
        for id_ in ('formula', 'sample', 'decision'):
            interact(w, id_)
        w.choose('preserve')
        interact(w, 'exit')
        self.assertEqual(w.outcome, 'chapter')
        self.assertNotIn('maia', w.flags)


class SaveTests(unittest.TestCase):
    def test_round_trip_validation_and_invalid_json(self):
        with tempfile.TemporaryDirectory() as folder:
            slot = SaveSlot(Path(folder) / 'save.json')
            self.assertIsNone(slot.read())
            slot.write(3, {'protocol': 'preserve', 'ivo': True}, ['lab_log'])
            data = slot.read()
            self.assertEqual(data['chapter'], 3)
            self.assertEqual(data['flags']['protocol'], 'preserve')
            for value in ('broken', '[]', '{"version":1,"chapter":99}', '{"version":1,"chapter":true}', '{"version":1,"chapter":1,"flags":[]}'):
                slot.path.write_text(value)
                self.assertIsNone(slot.read())

    def test_write_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            blocker = Path(folder) / 'block'
            blocker.write_text('x')
            slot = SaveSlot(blocker / 'save.json')
            slot.write(0, {}, [])
            self.assertTrue(slot.warning)


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.g = Game(Path(self.tmp.name) / 'save.json')

    def tearDown(self):
        pygame.quit()
        self.tmp.cleanup()

    def key(self, key):
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))

    def test_intro_pause_focus_and_checkpoint_retry(self):
        g = self.g
        g.action('new')
        self.assertEqual(g.state, 'dialogue')
        for _ in range(4):
            self.key(pygame.K_RETURN)
        self.assertEqual(g.state, 'playing')
        self.key(pygame.K_ESCAPE)
        elapsed = g.world.elapsed
        g.update(.1)
        self.assertEqual(g.world.elapsed, elapsed)
        self.key(pygame.K_ESCAPE)
        g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(g.state, 'paused')
        g.world.hp = 2
        g.world.flags['protocol'] = 'purge'
        g.action('retry')
        self.assertEqual(g.world.hp, 100)
        self.assertNotIn('protocol', g.world.flags)

    def test_all_screens_and_journal_render(self):
        g = self.g
        for state in ('menu', 'help', 'paused', 'journal', 'choice', 'lost', 'chapter', 'victory'):
            g.state = state
            g.world.logs = list(LOGS)
            g.draw()
        g.load(dict(chapter=2, flags={}, logs=[]), persist=False)
        g.draw()
        for chapter in range(5):
            g.load(dict(chapter=chapter, flags={}, logs=[]), intro=False, persist=False)
            g.draw()
            g.present()

    def test_mouse_scaled_coordinates(self):
        self.g.viewport = pygame.Rect(0, 100, 600, 360)
        self.assertEqual(self.g.logical_mouse((300, 280)), V(600, 360))

    def test_completed_chapter_saves_next_checkpoint_before_menu(self):
        g = self.g
        g.action('new')
        g.world.flags['teo'] = True
        g.world.outcome = 'chapter'
        g.consume_events()
        self.assertEqual(g.slot.read()['chapter'], 1)
        g.action('menu')
        g.action('continue')
        self.assertEqual(g.world.chapter, 1)
        self.assertTrue(g.world.flags['teo'])

    def test_preview_does_not_overwrite_real_checkpoint(self):
        g = self.g
        g.slot.write(1, {'teo': True}, [])
        original = g.slot.path.read_bytes()
        g.allow_save = False
        g.load(dict(chapter=3, flags={}, logs=[]))
        g.world.outcome = 'chapter'
        g.consume_events()
        g.action('next')
        self.assertEqual(g.slot.path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
