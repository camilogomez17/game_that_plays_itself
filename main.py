"""Minimal autonomous settlement MVP. Run with: python main.py"""
from math import cos, sin, pi
from random import Random

from panda3d.core import loadPrcFileData
loadPrcFileData("", "win-size 1280 800")

from ursina import (
    AmbientLight, DirectionalLight, Entity, Sky, Text, Ursina, Vec3,
    camera, color, destroy, time, window,
)

app = Ursina()
window.title = "Tiny Kingdom — Autonomous Settlement"
window.color = color.rgb(135, 190, 225)
camera.position = (0, 22, -28)
camera.look_at(Vec3(0, 0, 0))
camera.fov = 55
DirectionalLight(y=12, z=-4, shadows=False)
AmbientLight(color=color.rgba(160, 160, 160, 255))
Sky()

grass = Entity(model="plane", scale=60, color=color.rgb(91, 151, 83))
hud = Text(position=(-0.86, 0.45), scale=1, background=True)
message = Text(position=(-0.86, 0.39), scale=0.75, background=True)
Text("AUTONOMOUS SETTLEMENT  |  ESC: quit", position=(-0.86, -0.46), scale=0.7)

resources, buildings, enemies = [], [], []
wood = food = gold = 0
health, age, timer, build_timer, raid_timer = 100, 0.0, 0.0, 0.0, 10.0
carrying = None
target = None
state = "gather"
lost = False
rng = Random(41)


def block(parent, model, tint, pos, size, rotation=(0, 0, 0)):
    return Entity(parent=parent, model=model, color=tint, position=pos, scale=size, rotation=rotation)


town = Entity(position=(0, 0, 0))
block(town, "cube", color.rgb(190, 168, 126), (0, 1, 0), (3.8, 2, 3.4))
block(town, "cube", color.rgb(135, 63, 47), (0, 2.2, 0), (3.5, 0.5, 3.2), (0, 45, 0))
town.kind = "town"
buildings.append(town)

worker = Entity(position=(0, 0, -4))
block(worker, "cube", color.rgb(48, 95, 170), (0, 1, 0), (0.6, 0.9, 0.4))
block(worker, "sphere", color.rgb(224, 178, 133), (0, 1.7, 0), (0.4, 0.4, 0.4))

for kind, x, z in [
    ("wood", -8, -3), ("wood", -10, 4), ("wood", 9, 4), ("wood", 11, -5),
    ("food", -5, 8), ("food", 5, 9), ("food", 10, 8),
    ("gold", 7, -9), ("gold", -8, -9), ("gold", 3, 12),
]:
    node = Entity(position=(x, 0, z))
    node.kind, node.stock = kind, 5
    if kind == "wood":
        block(node, "cube", color.rgb(105, 72, 43), (0, 0.8, 0), (0.35, 1.6, 0.35))
        block(node, "sphere", color.rgb(43, 117, 53), (0, 1.9, 0), (1.5, 1.5, 1.5))
    elif kind == "food":
        block(node, "sphere", color.rgb(45, 130, 48), (0, 0.45, 0), (1.2, 0.7, 1))
        for bx, bz in [(-0.25, 0), (0.2, 0.15), (0, -0.2)]:
            block(node, "sphere", color.rgb(190, 45, 55), (bx, 0.8, bz), (0.22, 0.22, 0.22))
    else:
        block(node, "sphere", color.rgb(95, 94, 99), (0, 0.4, 0), (1.2, 0.8, 1))
        block(node, "sphere", color.rgb(222, 177, 48), (0.1, 0.7, 0), (0.5, 0.3, 0.5))
    resources.append(node)


def move(entity, destination, speed, dt):
    delta = Vec3(destination.x - entity.x, 0, destination.z - entity.z)
    distance = max((delta.x * delta.x + delta.z * delta.z) ** 0.5, 0.001)
    if distance > 0.05:
        entity.position += delta.normalized() * min(speed * dt, distance)
    return distance


def build(kind, x, z):
    house = Entity(position=(x, 0, z))
    block(house, "cube", color.rgb(204, 188, 146), (0, 0.7, 0), (2, 1.4, 1.8))
    block(house, "cube", color.rgb(139, 67, 48), (0, 1.55, 0), (2.2, 0.45, 2), (0, 45, 0))
    house.kind = kind
    buildings.append(house)


def raid():
    enemy = Entity(position=(worker.x + rng.choice([-1, 1]) * 14, 0, worker.z + rng.choice([-1, 1]) * 12))
    block(enemy, "cube", color.rgb(155, 45, 45), (0, 1, 0), (0.8, 1, 0.6))
    block(enemy, "sphere", color.rgb(205, 150, 110), (0, 1.7, 0), (0.4, 0.4, 0.4))
    enemy.hp = 3
    enemies.append(enemy)


def update():
    global wood, food, gold, health, age, timer, build_timer, raid_timer
    global carrying, target, state, lost
    if lost:
        return
    dt = min(time.dt, 0.05)
    age += dt
    timer += dt
    build_timer -= dt
    raid_timer -= dt

    if state == "gather":
        available = [r for r in resources if r.enabled and r.stock > 0]
        if target not in available:
            preferred = "food" if health < 65 else None
            choices = [r for r in available if r.kind == preferred] if preferred else available
            target = min(choices or available, key=lambda r: (r.x-worker.x)**2 + (r.z-worker.z)**2) if available else None
            timer = 0
        if target is not None:
            distance = move(worker, target.position, 3.2, dt)
            if distance < 1.8 and timer >= 1.5:
                carrying = target.kind
                target.stock -= 1
                timer = 0
                if target.stock <= 0:
                    target.enabled = False
                state = "return"
    else:
        if move(worker, town.position, 4, dt) < 3.5:
            if carrying == "wood":
                wood += 1
            elif carrying == "food":
                food += 1
            else:
                gold += 1
            carrying, target, state = None, None, "gather"

    if build_timer <= 0 and wood >= 5 and gold >= 3 and sum(b.kind == "house" for b in buildings) < 4:
        wood, gold = wood - 5, gold - 3
        count = sum(b.kind == "house" for b in buildings)
        build("house", cos(count * pi / 2) * 6, sin(count * pi / 2) * 6)
        build_timer = 2

    if raid_timer <= 0 and not enemies:
        raid()
        raid_timer = max(7, 16 - age / 60)
    for enemy in enemies[:]:
        if move(enemy, worker.position, 2, dt) < 1.5:
            health -= dt * 12
            enemy.hp -= dt * 0.8
            if enemy.hp <= 0:
                enemies.remove(enemy)
                destroy(enemy)
                gold += 2
    if food and health < 80 and timer > 2:
        food -= 1
        health = min(100, health + 20)
        timer = 0
    if health <= 0:
        lost = True
        message.text = "SETTLEMENT LOST"
        return
    cargo = f" | CARRYING {carrying.upper()}" if carrying else ""
    hud.text = f"HP {int(health)}   FOOD {food}   WOOD {wood}   GOLD {gold}   HOUSES {len(buildings)-1}"
    message.text = f"WORKER: {state.upper()}{cargo}   |   DAY {int(age // 60) + 1}"


app.run()
