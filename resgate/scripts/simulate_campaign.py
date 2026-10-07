"""Percorre a campanha pelas regras reais, sem teleporte ou vida infinita.

O piloto automatizado usa caminhos, plasma, pulso e kits. Não mede diversão
nem substitui uma partida humana; detecta rotas bloqueadas e resgates inviáveis.
Execute da raiz: python scripts/simulate_campaign.py.
"""
import os
import sys
import json
from pathlib import Path
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pygame import Vector2 as V
from src.echo.model import Campaign
from src.echo.story import ending


def run(choice, difficulty='normal'):
    flags, logs, results = {'difficulty': difficulty}, [], []
    for chapter in range(5):
        w = Campaign(chapter, flags, logs)
        goals = [
            ['power', 'key', 'teo', 'dock_log', 'exit'],
            ['ivo', 'relay_a', 'relay_b', 'engine_log', 'exit'],
            ['formula', 'sample', 'maia', 'lab_log', 'decision', 'exit'],
            ['seal_a', 'seal_b', 'seal_c', 'boss', 'core_log', 'exit'],
            ['stabilizer', 'nina', 'valve', 'escape_log'] + (['broadcast'] if choice == 'preserve' else []) + ['exit'],
        ][chapter]
        goals.insert(-1, 'upgrade')
        for goal in goals:
            for tick in range(18000):
                if w.outcome == 'lost':
                    raise AssertionError(f'{choice}: chapter {chapter + 1}, goal {goal}: {w.reason}; player={w.player}; ally={w.ally}; ally_hp={w.ally_hp}; near={w.nearest()}')
                if goal == 'boss':
                    boss = next((e for e in w.enemies if e.kind == 'boss'), None)
                    if boss is None:
                        break
                    target = boss.pos.copy()
                else:
                    n = w.node(goal)
                    if n.done or w.outcome:
                        break
                    target = n.pos.copy()
                # Uma escolta caída é atendida antes de retomar o objetivo.
                revive = w.ally is not None and w.ally_hp <= 0
                if revive:
                    target = w.ally.copy()
                distance = w.player.distance_to(target)
                if distance < 55:
                    if revive:
                        w.interact()
                    elif goal != 'boss':
                        w.interact()
                        if goal == 'decision':
                            w.choose(choice)
                        elif goal == 'upgrade':
                            w.upgrade(('weapon', 'armor', 'reactor', 'weapon', 'armor')[chapter])
                targets = [e for e in w.enemies if e.active and e.hp > 0 and e.pos.distance_to(w.player) < 550 and w.visible(w.player, e.pos)]
                closest = min(targets, key=lambda e: e.pos.distance_squared_to(w.player)) if targets else None
                if w.hp < 50:
                    w.heal()
                if closest and closest.pos.distance_to(w.player) < 155:
                    w.emp()
                direction = V()
                # Mantém distância de combate ao chefe; desvia do impacto anunciado.
                danger = next((d for d in w.dangers if w.player.distance_to(d[0]) < d[2] + 24), None)
                if danger:
                    direction = w.player - danger[0]
                    if direction.length_squared() < 1:
                        direction = V(-1, -1)
                elif goal == 'boss' and distance < 290 and w.visible(w.player, target):
                    direction = V()
                elif distance > 40:
                    if w.visible(w.player, target, 16):
                        direction = target - w.player
                    else:
                        path = w.path(w.player, target)
                        if path:
                            direction = path[0] - w.player
                w.update(1 / 30, direction)
                if closest:
                    if closest.pos.distance_to(w.player) < 190 and w.energy > 65:
                        w.scatter(closest.pos - w.player)
                    else:
                        w.shoot(closest.pos - w.player)
                # O bot lê os diálogos instantaneamente; não altera as regras.
                w.events.clear()
            else:
                raise AssertionError(f'{choice}: stalled chapter {chapter + 1} goal {goal}; player={w.player}, ally={w.ally}')
        expected = 'victory' if chapter == 4 else 'chapter'
        assert w.outcome == expected, (chapter, w.outcome)
        flags, logs = dict(w.flags), list(w.logs)
        results.append(dict(chapter=chapter + 1, seconds=round(w.elapsed, 1), hp=round(w.hp), kills=w.kills,
                            ally_hp=round(w.ally_hp), seconds_left=round(w.timer, 1) if w.timer is not None else None))
    return dict(choice=choice, difficulty=difficulty, chapters=results, ending=ending(flags)[0], logs=len(logs),
                modules={key: flags.get(key, 0) for key in ('weapon', 'armor', 'reactor')})


if __name__ == '__main__':
    print(json.dumps([run(choice, difficulty) for difficulty in ('explore', 'normal', 'survival')
                      for choice in ('preserve', 'purge')], ensure_ascii=False, indent=2))
