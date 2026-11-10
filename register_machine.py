# All arms should go x direction, then z, then y out from active machine.

def push_to_stack(code, bits):
    global stack
    stack <<= bits
    stack ^= code


def pop_from_stack(bits):
    global stack
    code = stack & ((1 << bits) - 1)
    stack >>= bits
    return code


def determine_active_axis():
    global dx
    global dy
    global dz
    global active_axis
    if dy > 1:
        active_axis = 0
    elif dz > 1:
        active_axis = 1
    elif dx > 1:
        active_axis = 2


def modify_active_axis(modification):
    global dx
    global dy
    global dz
    global active_axis
    if active_axis == 0:
        dy += modification
    if active_axis == 1:
        dz += modification
    if active_axis == 2:
        dx += modification


def fetch_from_store(cargo):
    print(f"install {cargo}")


def return_to_store(cargo):
    print(f"remove {cargo}")


def recursively_install():
    global dx
    global dy
    global dz
    global negative_z
    if dy > 1:
        dy -= 1
        recursively_install()
        dy -= 1
        fetch_from_store("yp")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store("yp")
        dy += 2
    elif dz > 1:
        z_direction = "+" if negative_z == 0 else "-"
        dz -= 1
        recursively_install()
        dz -= 1
        fetch_from_store(f"zsp{z_direction}")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store(f"zsp{z_direction}")
        dz += 2
    elif dx > 1:
        dx -= 1
        recursively_install()
        dx -= 1
        fetch_from_store("xsp")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store("xsp")
        dx += 2
    else:
        if dy == 1:
            print("toggle y")
        if dz ^ negative_z == 0:
            print("toggle z")
        if dx == 1:
            print("toggle x")


def recursively_remove():
    global dx
    global dy
    global dz
    global negative_z
    if dy > 1:
        dy -= 2
        fetch_from_store("ysp")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store("ysp")
        dy += 1
        recursively_remove()
        dy += 1
    elif dz > 1:
        dz -= 2
        z_direction = "+" if negative_z == 0 else "-"
        fetch_from_store(f"zsp{z_direction}")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store(f"zsp{z_direction}")
        dz += 1
        recursively_remove()
        dz += 1
    elif dx > 1:
        dx -= 2
        fetch_from_store("xsp")
        recursively_install()
        recursively_pulse()
        recursively_remove()
        return_to_store("xsp")
        dx += 1
        recursively_remove()
        dx += 1
    else:
        if dx == 1:
            print("toggle x")
        if dz ^ negative_z == 0:
            print("toggle z")
        if dy == 1:
            print("toggle y")


def recursively_pulse():
    global dx
    global dy
    global dz
    global negative_z
    if dy > 1:
        dy -= 1
        fetch_from_store("yo")
        recursively_install()
        recursively_remove()
        return_to_store("yo")
        dy += 1
    elif dz > 1:
        dz -= 1
        observer = f"zo{"+" if negative_z == 0 else "-"}"
        fetch_from_store(observer)
        recursively_install()
        recursively_remove()
        return_to_store(observer)
        dz += 1
    elif dx > 1:
        dx -= 1
        fetch_from_store("xo")
        recursively_install()
        recursively_remove()
        return_to_store("xo")
        dx += 1
    else:
        print(f"pulse {dx}")


y_height = 2 # 32
y_buffer = 3
n = 2  # 256
active_axis = 0

for y in range(y_height):
    for z in range(0, -n, -1):
        for x in range(2, n + 2):
            dx = x
            dy = y
            dz = 1-z
            negative_z = 1
            recursively_remove()
            dx = x
            dy = 3 * (y_height - y - 1) + y_height + y_buffer
            dz = z + n
            negative_z = 0
            recursively_install()
for y in range(y_height - 1, -1, -1):
    for z in range(0, -n, -1):
        for x in range(2, n + 2):
            dx = x
            dz = 1-z
            dy = 3 * (y_height - y - 1) + y_height + y_buffer
            negative_z = 1
            recursively_remove()
            dx = x
            dz = z + n
            dy = y
            negative_z = 0
            recursively_install()



