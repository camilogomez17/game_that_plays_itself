"""Tiny Age-of-Empires-inspired autonomous settlement. Run: python3 main.py"""
# Request a modern OpenGL context before Ursina initializes Panda3D.
from panda3d.core import loadPrcFileData
loadPrcFileData("", "gl-version 3 2")
from ursina import AmbientLight, DirectionalLight, Entity, Sky, Text, Ursina, Vec3, application, camera, color, destroy, lerp, time, window
from random import Random
from math import cos, floor, pi as PI, sin

app = Ursina()
window.title = "Tiny Kingdom — Autonomous RTS"
window.color = color.rgb(145, 190, 225)
window.fps_counter.enabled = True
camera.fov = 55

CHUNK = 28
RADIUS = 2
SEED = 41
BASE = Vec3(0, 0, 0)
world, resources, enemies, buildings = {}, [], [], []
age, health, food, wood, coins = 0.0, 100.0, 0, 0, 0
enemy_next, eat_timer = 10.0, 0.0
worker_state, target, work_timer, carry_kind, carry_amount = "gather", None, 0.0, None, 0
build_timer = 0.0
game_over = False

ground_color = color.rgb(91, 151, 83)
hud = Text(position=(-0.86, 0.46), scale=0.95, background=True)
status = Text(position=(-0.86, 0.39), scale=0.75, background=True)
tips = Text("AUTONOMOUS SETTLEMENT  |  ESC: quit", position=(-0.86, -0.46), scale=0.7)


def part(parent, model, tint, pos, scale, rotation=(0, 0, 0)):
    return Entity(parent=parent, model=model, color=tint, position=pos, scale=scale, rotation=rotation)


def make_worker():
    root = Entity(position=(0, 0, -2))
    # A readable low-poly villager assembled from simple meshes.
    part(root, "cube", color.rgb(48, 95, 170), (0, 1.05, 0), (0.58, 0.78, 0.34))
    part(root, "sphere", color.rgb(224, 178, 133), (0, 1.68, 0), (0.38, 0.4, 0.36))
    part(root, "sphere", color.rgb(116, 76, 43), (0, 1.94, 0), (0.48, 0.22, 0.48))
    for side in (-1, 1):
        part(root, "cube", color.rgb(224, 178, 133), (side * 0.39, 1.08, 0), (0.16, 0.62, 0.18), (0, 0, side * -8))
        part(root, "cube", color.rgb(65, 65, 82), (side * 0.17, 0.43, 0), (0.19, 0.5, 0.22))
    return root


worker = make_worker()


def make_tree(parent, scale=1.0):
    part(parent, "cylinder", color.rgb(105, 72, 43), (0, 0.8, 0), (0.32, 1.6, 0.32))
    part(parent, "sphere", color.rgb(43, 117, 53), (0, 1.85, 0), (1.15, 1.25, 1.1))
    part(parent, "sphere", color.rgb(57, 137, 59), (0.35, 2.15, 0.05), (0.78, 0.85, 0.82))


def make_node(kind, x, z, stock):
    root = Entity(position=(x, 0, z))
    root.kind, root.stock = kind, stock
    if kind == "wood":
        make_tree(root)
    elif kind == "food":
        part(root, "sphere", color.rgb(45, 130, 48), (0, 0.45, 0), (1.0, 0.65, 0.9))
        for bx, bz in ((-.22, -.12), (.18, -.08), (0.05, .2)):
            part(root, "sphere", color.rgb(190, 45, 55), (bx, 0.72, bz), (0.18, 0.18, 0.18))
    else:
        part(root, "sphere", color.rgb(95, 94, 99), (0, 0.42, 0), (1.1, 0.8, 0.9))
        for ox, oz in ((-.22, 0), (.18, .12), (0, -.2)):
            part(root, "sphere", color.rgb(222, 177, 48), (ox, 0.68, oz), (0.24, 0.2, 0.22))
    resources.append(root)
    return root


def make_building(kind, x, z):
    root = Entity(position=(x, 0, z))
    if kind == "town":
        part(root, "cube", color.rgb(190, 168, 126), (0, 1.05, 0), (3.8, 2.1, 3.4))
        part(root, "cone", color.rgb(135, 63, 47), (0, 2.55, 0), (3.6, 1.5, 3.6))
        part(root, "cube", color.rgb(94, 65, 42), (0, 0.65, -1.73), (0.75, 1.3, 0.12))
        part(root, "cube", color.rgb(231, 205, 143), (0, 2.05, -1.75), (0.85, 0.18, 0.1))
    elif kind == "house":
        part(root, "cube", color.rgb(204, 188, 146), (0, 0.65, 0), (2.0, 1.3, 1.8))
        part(root, "cone", color.rgb(139, 67, 48), (0, 1.65, 0), (2.3, 1.1, 2.2))
        part(root, "cube", color.rgb(89, 59, 40), (0, 0.4, -0.93), (0.42, 0.8, 0.08))
    else:
        part(root, "cube", color.rgb(159, 151, 131), (0, 1.2, 0), (1.25, 2.4, 1.25))
        part(root, "cone", color.rgb(118, 61, 48), (0, 2.75, 0), (1.5, 0.9, 1.5))
        part(root, "cube", color.rgb(111, 77, 50), (0, 2.0, -0.65), (0.16, 0.8, 0.12))
    buildings.append(root)
    root.kind = kind
    return root


town_center = make_building("town", 0, 0)


def chunk_key(x, z):
    return floor(x / CHUNK), floor(z / CHUNK)


def make_chunk(cx, cz):
    rng = Random(SEED + cx * 73856093 + cz * 19349663)
    base = Entity(model="plane", scale=CHUNK, position=(cx * CHUNK, 0, cz * CHUNK),
                  color=ground_color, collider="box")
    props = [base]
    # Small patches of flowers add depth without requiring texture assets.
    for _ in range(3):
        x = cx * CHUNK + rng.uniform(-CHUNK/2, CHUNK/2)
        z = cz * CHUNK + rng.uniform(-CHUNK/2, CHUNK/2)
        flower = Entity(model="sphere", color=color.rgb(232, 218, 165),
                        scale=0.12, position=(x, 0.08, z))
        props.append(flower)
    for _ in range(7):
        x = cx * CHUNK + rng.uniform(-CHUNK/2 + 2, CHUNK/2 - 2)
        z = cz * CHUNK + rng.uniform(-CHUNK/2 + 2, CHUNK/2 - 2)
        if abs(x) < 5 and abs(z) < 5:
            continue
        kind = rng.choice(("wood", "wood", "food", "gold"))
        node = make_node(kind, x, z, {"wood": 5, "food": 4, "gold": 5}[kind])
        props.append(node)
    world[(cx, cz)] = props


def update_world():
    cx, cz = chunk_key(worker.x, worker.z)
    wanted = {(x, z) for x in range(cx-RADIUS, cx+RADIUS+1)
              for z in range(cz-RADIUS, cz+RADIUS+1)}
    for key in wanted - world.keys():
        make_chunk(*key)
    for key in set(world) - wanted:
        for obj in world.pop(key):
            if obj in resources:
                resources.remove(obj)
            destroy(obj)


def move_toward(entity, point, speed, dt):
    delta = Vec3(point.x-entity.x, 0, point.z-entity.z)
    distance = max((delta.x*delta.x + delta.z*delta.z)**0.5, 0.001)
    if distance > 0.02:
        entity.position += delta.normalized() * min(speed*dt, distance)
        entity.rotation_y = 0 if abs(delta.x) + abs(delta.z) < 0.001 else __import__("math").degrees(__import__("math").atan2(delta.x, delta.z))
    return distance


def spawn_enemy():
    rng = Random(SEED + int(age * 1000))
    angle = rng.uniform(0, 2*PI)
    enemy = Entity(position=(worker.x + cos(angle)*15, 0, worker.z + sin(angle)*15))
    part(enemy, "cube", color.rgb(150, 48, 48), (0, 1.0, 0), (0.75, 0.95, 0.5))
    part(enemy, "sphere", color.rgb(195, 142, 104), (0, 1.68, 0), (0.42, 0.42, 0.42))
    part(enemy, "cone", color.rgb(66, 54, 48), (0, 1.96, 0), (0.5, 0.25, 0.5))
    enemy.hp = 3
    enemies.append(enemy)


def update():
    global age, health, food, wood, coins, enemy_next, eat_timer
    global worker_state, target, work_timer, carry_kind, carry_amount, build_timer, game_over
    if game_over:
        return
    dt = min(time.dt, 0.05)
    age += dt
    eat_timer -= dt
    build_timer -= dt
    update_world()

    # The worker gathers by working at a source, then carries a load to the town center.
    if worker_state == "gather":
        candidates = [r for r in resources if r.enabled and r.stock > 0]
        if not candidates:
            worker.x += 1.5 * dt
            target = None
        else:
            if target not in candidates:
                # Prioritize food when hurt, otherwise choose the nearest workable source.
                desired = "food" if health < 65 and food < 2 else None
                options = [r for r in candidates if r.kind == desired] if desired else candidates
                target = min(options or candidates, key=lambda r: (r.x-worker.x)**2 + (r.z-worker.z)**2)
                work_timer = 0
            if target is not None:
                distance = move_toward(worker, target.position, 3.2, dt)
                if distance < 1.8:
                    work_timer += dt
                    worker.rotation_y = sin(age * 9) * 12
                    if work_timer >= 2.0:
                        carry_kind = target.kind
                        carry_amount = 1
                        target.stock -= 1
                        work_timer = 0
                        if target.stock <= 0:
                            target.enabled = False
                            for child in target.children:
                                child.enabled = False
                        worker_state = "return"
    elif worker_state == "return":
        distance = move_toward(worker, town_center.position, 4.0, dt)
        if distance < 3.4:
            if carry_kind == "wood":
                wood += carry_amount
            elif carry_kind == "food":
                food += carry_amount
            else:
                coins += carry_amount
            carry_kind, carry_amount, target = None, 0, None
            worker_state = "gather"

    # Spend stored materials on a settlement: houses raise capacity visually, towers defend.
    if build_timer <= 0:
        if wood >= 6 and coins >= 3 and sum(1 for b in buildings if b.kind == "house") < 4:
            wood -= 6
            coins -= 3
            idx = sum(1 for b in buildings if b.kind == "house")
            angle = idx * (PI/2) + PI/4
            make_building("house", cos(angle)*6, sin(angle)*6)
            build_timer = 3
        elif wood >= 10 and coins >= 5 and not any(b.kind == "tower" for b in buildings):
            wood -= 10
            coins -= 5
            make_building("tower", 4.8, -4.8)
            build_timer = 3

    # Raids grow more frequent over time; the worker and tower automatically defend.
    if age >= enemy_next and not enemies:
        spawn_enemy()
        enemy_next = age + max(5, 12 - age/50)
    for enemy in enemies[:]:
        dist = move_toward(enemy, worker.position, 2.0, dt)
        if dist < 1.55:
            enemy.hp -= dt * (0.65 + wood * 0.01)
            health -= dt * 2.2
            if enemy.hp <= 0:
                enemies.remove(enemy)
                destroy(enemy)
                coins += 2
    if any(b.kind == "tower" for b in buildings):
        for enemy in enemies[:]:
            if (enemy.x-4.8)**2 + (enemy.z+4.8)**2 < 11:
                enemy.hp -= dt * 1.8
                if enemy.hp <= 0:
                    enemies.remove(enemy)
                    destroy(enemy)
                    coins += 2
    if food > 0 and health < 80 and eat_timer <= 0:
        food -= 1
        health = min(100, health+20)
        eat_timer = 3
    if health <= 0:
        game_over = True
        status.text = "SETTLEMENT LOST — close the window and rerun"
        return

    carrying = f" | CARRYING {carry_kind.upper()}" if carry_kind else ""
    hud.text = f"HP {int(health)}   FOOD {food}   WOOD {wood}   GOLD {coins}   HOUSES {sum(1 for b in buildings if b.kind == 'house')}"
    status.text = f"WORKER: {worker_state.upper()}{carrying}   |   RAIDS {int(age//12)}"
    camera.position = lerp(camera.position, Vec3(worker.x+1, 19, worker.z-23), dt*2)
    camera.rotation_x = 38
    camera.look_at(Vec3(worker.x, 0, worker.z))


DirectionalLight(y=12, z=4, shadows=False)
AmbientLight(color=color.rgba(150, 150, 150, 255))
Sky()
update_world()
app.run()
