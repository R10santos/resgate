"""Regressões das melhorias de combate, progressão e câmera."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import tempfile
import unittest
from pathlib import Path
import pygame
from pygame import Vector2 as V
from src.echo.model import Campaign, at
from src.echo.save import SaveSlot
from src.echo.app import Game


class Improvements(unittest.TestCase):
    def test_ally_waits_then_follows_without_losing_exit_requirement(self):
        w = Campaign(1)
        w.enemies.clear()
        w.join('IVO', w.node('ivo'))
        w.player = w.ally + V(200, 0)
        w.command_ally()
        pos = w.ally.copy()
        for _ in range(20):
            w.update(.05)
        self.assertEqual(w.ally, pos)
        for key in ('relay_a', 'relay_b'):
            w.node(key).done = True
        w.player = w.node('exit').pos.copy()
        w.exit_level()
        self.assertIsNone(w.outcome)
        w.command_ally()
        w.update(.05)
        self.assertNotEqual(w.ally, pos)

    def test_route_uses_corridors_and_changes_with_objective(self):
        w = Campaign()
        # Posição livre junto à divisória oeste.
        w.player = at(10, 9)
        w.node('power').done = True
        w.node('key').done = True
        route = w.objective_route()
        self.assertTrue(route)
        self.assertTrue(all(not w.solid(p) for p in route))
        self.assertEqual(route[-1], w.node('teo').pos)
        w.node('teo').done = True
        self.assertEqual(w.objective_route()[-1], w.node('exit').pos)

    def test_scatter_cost_cooldown_and_spread(self):
        w = Campaign()
        self.assertTrue(w.scatter((1, 0)))
        self.assertEqual(w.energy, 80)
        self.assertEqual(len(w.shots), 5)
        self.assertFalse(w.scatter((1, 0)))
        self.assertEqual(w.energy, 80)
        self.assertTrue(any(s.velocity.y < 0 for s in w.shots))
        self.assertTrue(any(s.velocity.y > 0 for s in w.shots))
        w.secondary_cd = 0
        w.energy = 19
        self.assertFalse(w.scatter())

    def test_upgrade_is_once_and_survives_next_chapter(self):
        w = Campaign()
        self.assertFalse(w.upgrade('armor'))
        w.player = w.node('upgrade').pos.copy()
        w.interact()
        self.assertIn(('upgrade', None), w.events)
        self.assertTrue(w.upgrade('armor'))
        self.assertEqual(w.hp, 125)
        self.assertFalse(w.upgrade('weapon'))
        next_w = Campaign(1, w.flags)
        self.assertEqual(next_w.max_hp, 125)
        self.assertEqual(next_w.hp, 125)

    def test_weapon_and_reactor_have_effect(self):
        normal, upgraded = Campaign(), Campaign(flags={'weapon': 2, 'reactor': 2})
        normal.shoot()
        upgraded.shoot()
        self.assertEqual(upgraded.shots[0].damage - normal.shots[0].damage, 10)
        normal.energy = upgraded.energy = 0
        normal.update(.1)
        upgraded.update(.1)
        self.assertAlmostEqual(upgraded.energy - normal.energy, 1)

    def test_difficulty_changes_damage_and_health(self):
        easy, normal, hard = [Campaign(flags={'difficulty': mode}) for mode in ('explore', 'normal', 'survival')]
        self.assertEqual(easy.hp, 140)
        self.assertGreater(hard.enemies[0].hp, normal.enemies[0].hp)
        for w in (easy, normal, hard):
            w.hurt(20)
        self.assertEqual(easy.hp, 128)
        self.assertEqual(normal.hp, 80)
        self.assertEqual(hard.hp, 73)

    def test_electrical_floor_warns_before_damage_and_dash_protects(self):
        w = Campaign(1)
        w.enemies.clear()
        w.player = at(*w.hazard_tiles[0])
        w.elapsed = 4
        self.assertEqual(w.hazard_state(0), 'warning')
        w.update(.1)
        self.assertEqual(w.hp, 100)
        w.elapsed = 5
        w.update(.01)
        self.assertEqual(w.hp, 88)
        w.invincible = 0
        w.dash()
        w.update(.01)
        self.assertEqual(w.hp, 88)

    def test_boss_summons_only_once(self):
        w = Campaign(3)
        boss = next(e for e in w.enemies if e.kind == 'boss')
        w.enemies = [boss]
        boss.active = True
        boss.hp = boss.max_hp / 3
        w.player = boss.pos + (0, 200)
        w.update(.01)
        self.assertEqual(len(w.enemies), 3)
        w.update(.1)
        self.assertEqual(len(w.enemies), 3)

    def test_old_and_new_saves_are_compatible(self):
        with tempfile.TemporaryDirectory() as folder:
            slot = SaveSlot(Path(folder) / 'save.json')
            slot.write(2, {'ivo': True}, [])
            self.assertEqual(Campaign(**slot.read()).difficulty, 'normal')
            slot.write(3, {'difficulty': 'survival', 'armor': 2, 'weapon': 1, 'reactor': 3}, [])
            loaded = Campaign(**slot.read())
            self.assertEqual(loaded.max_hp, 150)
            self.assertEqual(loaded.flags['reactor'], 3)
            slot.write(3, {'armor': True, 'weapon': 999, 'reactor': -1}, [])
            self.assertEqual(slot.read()['flags'], {})

    def test_escort_uses_body_clearance_at_door_corner(self):
        w = Campaign(4)
        w.enemies.clear()
        w.join('NINA', w.node('nina'))
        w.ally = V(562.734, 904.93)
        w.player = at(20, 19)
        self.assertTrue(w.visible(w.ally, w.player))
        self.assertFalse(w.visible(w.ally, w.player, 16))
        for _ in range(500):
            w.update(.02)
            if w.ally.distance_to(w.player) < 70:
                break
        self.assertLess(w.ally.distance_to(w.player), 70)


class ImprovedInterface(unittest.TestCase):
    def test_tactical_map_pauses_time_and_closes_with_g(self):
        self.g.load(dict(chapter=0, flags={}, logs=[]), intro=False, persist=False)
        self.g.keyboard_shooting = True
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g))
        self.assertEqual(self.g.state, 'map')
        self.assertFalse(self.g.keyboard_shooting)
        before = self.g.world.elapsed
        self.g.update(.1)
        self.assertEqual(self.g.world.elapsed, before)
        self.g.draw()
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g))
        self.assertEqual(self.g.state, 'playing')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.g = Game(Path(self.tmp.name) / 'save.json', allow_save=False)

    def tearDown(self):
        pygame.quit()
        self.tmp.cleanup()

    def test_zoom_and_mouse_aim_round_trip(self):
        r = self.g.renderer
        self.g.load(dict(chapter=0, flags={}, logs=[]), intro=False, persist=False)
        self.g.world.player = at(18, 17)
        self.g.draw()
        for point in (V(100, 200), V(700, 550), self.g.world.player):
            self.assertLess(r.screen_to_world(r.world_to_screen(point)).distance_to(point), .0001)
        self.assertEqual(r.world_to_screen(self.g.world.player), V(600, 360))

    def test_new_screens_and_difficulty_selection(self):
        self.g.action('difficulty')
        self.g.draw()
        self.g.action('difficulty_explore')
        self.assertEqual(self.g.world.max_hp, 140)
        self.g.state = 'playing'
        self.g.world.player = self.g.world.node('upgrade').pos.copy()
        self.g.world.interact()
        self.g.consume_events()
        self.assertEqual(self.g.state, 'upgrade')
        self.g.draw()
        self.g.action('module_weapon')
        self.assertEqual(self.g.world.flags['weapon'], 1)
        self.assertEqual(self.g.state, 'playing')

    def test_secondary_stops_on_focus_loss_and_objectives_toggle(self):
        self.g.load(dict(chapter=0, flags={}, logs=[]), intro=False, persist=False)
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_k))
        self.assertTrue(self.g.keyboard_secondary)
        self.g.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o))
        self.assertTrue(self.g.renderer.expanded_objectives)
        self.g.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertFalse(self.g.keyboard_secondary)
        self.assertFalse(self.g.secondary)


if __name__ == '__main__':
    unittest.main()
