"""Tiny 3D auto-survival MVP. Run with: python3 -m pip install -r requirements.txt && python3 main.py"""
from ursina import *
from random import Random
from math import floor

app = Ursina()
window.title = "Self-Playing Survival"
window.color = color.rgb(135, 190, 225)
window.fps_counter.enabled = True

CHUNK = 24
RADIUS = 2
SEED = 41
player = Entity(model="cube", color=color.azure, scale=(0.8, 1.6, 0.8), position=(0, 1, 0))
camera.position = (0, 12, -18)
camera.rotation_x = 28
camera.parent = scene
camera.fov = 85

food = wood = coins = 0
health = 100
age = 0
eat_timer = 0
enemy_next = 8
world = {}
enemies = []
resources = []
hud = Text(position=(-0.86, 0.46), scale=1.1)
help_text = Text("AUTOPILOT ON  |  ESC: quit", position=(-0.86, 0.40), scale=0.8, color=color.white)
ground_color = color.rgb(80, 145, 80)


def chunk_key(x, z):
    return floor(x / CHUNK), floor(z / CHUNK)


def make_chunk(cx, cz):
    key = (cx, cz)
    rng = Random(SEED + cx * 73856093 + cz * 19349663)
    base = Entity(model="plane", scale=CHUNK, position=(cx * CHUNK, 0, cz * CHUNK),
                  color=ground_color, collider="box")
    props = [base]
    for _ in range(9):
        x, z = cx * CHUNK + rng.uniform(-CHUNK / 2, CHUNK / 2), cz * CHUNK + rng.uniform(-CHUNK / 2, CHUNK / 2)
        kind = rng.choice(("food", "wood", "coin", "tree"))
        if kind == "tree":
            obj = Entity(model="cube", color=color.rgb(35, 105, 45), scale=(1.4, 2.8, 1.4), position=(x, 1.4, z))
            props.append(obj)
        else:
            shade = {"food": color.lime, "wood": color.rgb(130, 82, 45), "coin": color.yellow}[kind]
            obj = Entity(model="sphere" if kind == "coin" else "cube", color=shade,
                         scale=0.65 if kind == "coin" else (0.8, 0.8, 0.8), position=(x, 0.55, z))
            obj.kind = kind
            resources.append(obj)
            props.append(obj)
    world[key] = props


def update_world():
    cx, cz = chunk_key(player.x, player.z)
    wanted = {(x, z) for x in range(cx - RADIUS, cx + RADIUS + 1)
              for z in range(cz - RADIUS, cz + RADIUS + 1)}
    for key in wanted - world.keys():
        make_chunk(*key)
    for key in set(world) - wanted:
        for obj in world.pop(key):
            if hasattr(obj, "kind") and obj in resources:
                resources.remove(obj)
            destroy(obj)


def spawn_enemy():
    angle = Random(int(age * 1000) + SEED).uniform(0, 6.283)
    distance = 13
    enemy = Entity(model="cube", color=color.rgb(190, 55, 55), scale=(1, 1.5, 1),
                   position=(player.x + distance * __import__("math").cos(angle), 0.75,
                             player.z + distance * __import__("math").sin(angle)))
    enemy.hp = 2
    enemies.append(enemy)


def update():
    global food, wood, coins, health, age, eat_timer, enemy_next
    dt = min(time.dt, 0.05)
    age += dt
    eat_timer -= dt
    update_world()

    # The agent seeks the nearest visible resource; if none exist, it explores.
    targets = [r for r in resources if r.enabled]
    if targets:
        target = min(targets, key=lambda r: (r.x-player.x)**2 + (r.z-player.z)**2)
        dx, dz = target.x-player.x, target.z-player.z
        distance = max((dx*dx + dz*dz) ** 0.5, 0.001)
        if distance > 1.15:
            player.position += Vec3(dx/distance, 0, dz/distance) * 4 * dt
        else:
            if target.kind == "food":
                food += 1
            elif target.kind == "wood":
                wood += 1
            else:
                coins += 1
            resources.remove(target)
            destroy(target)
    else:
        player.x += 2 * dt

    # Enemies approach and are automatically fought at close range.
    if age >= enemy_next and not enemies:
        spawn_enemy()
        enemy_next = age + 8
    for enemy in enemies[:]:
        direction = Vec3(player.x-enemy.x, 0, player.z-enemy.z)
        distance = max((direction.x**2 + direction.z**2) ** 0.5, 0.001)
        if distance > 1.4:
            enemy.position += direction.normalized() * 2.2 * dt
        else:
            enemy.hp -= dt * (1 + wood * 0.03)
            health -= dt * 3
            if enemy.hp <= 0:
                enemies.remove(enemy)
                destroy(enemy)
                coins += 2
    if food > 0 and health <= 85 and eat_timer <= 0:
        food -= 1
        health = min(100, health + 15)
        eat_timer = 3
    if health <= 0:
        help_text.text = "DEFEATED — close window and rerun to restart"
        application.pause()
    hud.text = f"HP {int(health)}   FOOD {food}   WOOD {wood}   COINS {coins}   WORLD {int(player.x)},{int(player.z)}"
    camera.position = lerp(camera.position, Vec3(player.x, 12, player.z-18), dt * 2)
    camera.look_at(player.position)


def input(key):
    if key == "escape":
        application.quit()


# A small, persistent sun and low-cost lighting.
DirectionalLight(y=10, z=5, shadows=False)
Sky()
update_world()
app.run()
