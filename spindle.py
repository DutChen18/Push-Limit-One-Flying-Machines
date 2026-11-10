# This is where the piston arm is growing from.
origin = (0, 0, 0)
# The resulting sequence of elementary moves
seq: list[str] = []


def switch_root(new_origin):
    global origin
    origin = new_origin


def pulse(*segments):
    global seq
    if not segments:
        # print(f"[P{origin}]")
        seq.append(f"[P{origin}]")
        return

    n, facing = segments[-1]
    push(*segments[:-1], (n - 1, facing), cargo=f"[O{facing}]")
    pull(*segments[:-1], (n - 1, facing))


def push(*segments, cargo):

    if len(segments) == 0:
        return

    n, facing = segments[-1]

    if n == 0:
        # Spawn cargo
        push(*segments[:-1], cargo=cargo)
        return
    if n == 1:
        push(*segments[:-1], cargo=cargo)
        # Bring an auxiliary pushing piston, pulse it and remove
        switch_root(tuple(map(lambda x: -x, facing)))
        push(*segments[:-1], cargo=f"[S{facing}]")
        pulse(*segments[:-1])
        pull(*segments[:-1])
        switch_root((0, 0, 0))
        return
    if n == 2:
        push(*segments[:-1], (1, facing), cargo=cargo)
        # Bring an auxiliary pushing piston, pulse it and remove
        push(*segments[:-1], cargo=f"[S{facing}]")
        pulse(*segments[:-1])
        pull(*segments[:-1])
        return

    push(*segments[:-1], (n - 1, facing), cargo=cargo)
    push(*segments[:-1], (n - 2, facing), cargo=f"[S{facing}]")
    push(*segments[:-1], (n - 3, facing), cargo=f"[O{facing}]")
    pull(*segments[:-1], (n - 3, facing))
    pull(*segments[:-1], (n - 2, facing))


def pull(*segments: tuple[int, tuple[int, int, int]]):

    if len(segments) == 0:
        return

    n, facing = segments[-1]

    if n == 0:
        # Remove cargo
        pull(*segments[:-1])
        return
    if n == 1:
        # Bring an auxiliary pulling piston, pulse it and remove
        switch_root(tuple(map(lambda x: -x, facing)))
        push(*segments[:-1], cargo=f"[S{facing}]")
        pulse(*segments[:-1])
        pull(*segments[:-1])
        switch_root((0, 0, 0))
        # Finally, pull the cargo along the remaining arm
        pull(*segments[:-1])
        return
    if n == 2:
        # Bring an auxiliary pulling piston, pulse it and remove
        push(*segments[:-1], cargo=f"[S{facing}]")
        pulse(*segments[:-1])
        pull(*segments[:-1])
        # Reduction to the case n=1
        pull(*segments[:-1], (1, facing))
        return

    push(*segments[:-1], (n - 2, facing), cargo=f"[S{facing}]")
    push(*segments[:-1], (n - 3, facing), cargo=f"[O{facing}]")
    pull(*segments[:-1], (n - 3, facing))
    pull(*segments[:-1], (n - 2, facing))
    pull(*segments[:-1], (n - 1, facing))


plus_x = (1, 0, 0)
plus_z = (0, 0, 1)
plus_y = (0, 1, 0)

# push 5 blocks towards +X, 5 blocks towards +Z, and 5 blocks towards +Y
push((2, plus_x), (2, plus_z), (2, plus_y), cargo="[diamond_block]")
print(seq)