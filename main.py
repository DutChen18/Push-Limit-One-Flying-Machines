from collections import defaultdict

# some constants
y_height = 2
y_buffer = 3
# list of observers relative to original center required to move flying machine
# + (0, 1)
# with layout
# DDL
# R_L
# RUU
flight_sequence = [
    (1, 0),
    (0, 0),
    (2, 0),
    (1, 0),
    (3, 0), # image 1 reached
    (0, -1),
    (1, -1),
    (1, 0),
    (1, -1), # image 2 reached
    (3, 0),
    (1, 0),
    (2, 0),
    (0, 0),
    (0, -1), # image 3 reached
    (0, 1),
    (2, 1),
    (1, 1),
    (3, 1), # image 4 reached
    (1, 0),
    (0, -1),
    (1, -1), # image 5 reached
    (0, 1),
    (-1, -1),
    (-1, 1),
    (-1, 0),
    (0, 1), # image 6 reached
    (0, 0),
    (1, 1),
    (1, 0),
    (1, 2),
    (0, 0), # image 7 reached
    (3, 1),
    (1, 1),
    (2, 1),
    (0, 1),
    (1, 1) # flight cycle completed
]

# list of observers relative to original center required to move C + (1, 0)
# with layout

# C
# _
# _
# DDL
# R_L
# RUU

push_sequence_part_1 = [
    (1, 0),
    (0, 0),
    (2, 0),
    (1, 0),
    (3, 0), # picture 1 reached
    (0, 1),
    (-1, -1),
    (-1, 1),
    (-1, 0),
    (0, 1), # picture 2 reached
    (0, 0),
    (0, 2),
    (0, 1),
    (0, 3), # picture 3 reached
    (1, 1),
    (1, 0),
    (1, 2),
    (1, 0),
    (-1, 0),
    (0, 0),
    (0, 2),
    (1, 1),
    (-1, 1),
    (-1, 3)
]

push_sequence = push_sequence_part_1 + push_sequence_part_1[-2::-1] # + flight_sequence


def simulate_flight_sequence(sequence, board, origin):
    for r in board:
        print("".join(r))
    print("=" * 20)
    if not sequence:
        return
    next_move = sequence[0]
    piston_source = (origin[0] + next_move[0], origin[1] + next_move[1])
    print(piston_source)
    active_piston = board[piston_source[0]][piston_source[1]]
    if active_piston == "U":
        board[piston_source[0] - 2][piston_source[1]], board[piston_source[0] - 1][piston_source[1]] = \
            board[piston_source[0] - 1][piston_source[1]], board[piston_source[0] - 2][piston_source[1]]
    if active_piston == "D":
        board[piston_source[0] + 2][piston_source[1]], board[piston_source[0] + 1][piston_source[1]] = \
            board[piston_source[0] + 1][piston_source[1]], board[piston_source[0] + 2][piston_source[1]]
    if active_piston == "R":
        board[piston_source[0]][piston_source[1] + 2], board[piston_source[0]][piston_source[1] + 1] = \
            board[piston_source[0]][piston_source[1] + 1], board[piston_source[0]][piston_source[1] + 2]
    if active_piston == "L":
        board[piston_source[0]][piston_source[1] - 2], board[piston_source[0]][piston_source[1] - 1] = \
            board[piston_source[0]][piston_source[1] - 1], board[piston_source[0]][piston_source[1] - 2]
    simulate_flight_sequence(sequence[1:], board, origin)


class FlyingMachine:

    def __init__(self, n):
        self.n = n

    def move_machine(self):
        x_machine_width = self.n
        z_machine_width = self.n
        z_jump_size = z_machine_width

        # x z y iteration order
        # machine flies in + z
        for y in range(y_height):
            for z in range(0, -z_machine_width, -1):
                for x in range(2, x_machine_width + 2):
                    self.move((x, y, z), (x, 3 * (y_height - y - 1) + y_height + y_buffer, z + z_jump_size))
        for y in range(y_height - 1, -1, -1):
            for z in range(0, -z_machine_width, -1):
                for x in range(2, x_machine_width + 2):
                    self.move((x, 3 * (y_height - y - 1) + y_height + y_buffer, z), (x, y, z + z_jump_size))
        # TODO poke ? to start next machine

    # All arms should go x direction, then z, then y out from active machine.
    def move(self, v1, v2):
        dx1, dy1, dz1 = v1
        dx2, dy2, dz2 = v2
        self.remove(dx1, 1-dz1, dy1, "special", negative_z=True)
        self.install(dx2, dz2, dy2, "special", negative_z=False)

    def install(self, dx, dz, dy, cargo, negative_z):
        if dy > 1:
            self.install(dx, dz, dy - 1, cargo, negative_z)
            self.install(dx, dz, dy - 2, "yp", negative_z)
            self.pulse(dx, dz, dy - 2, negative_z)
            self.remove(dx, dz, dy - 2, "yp", negative_z)
        elif dz > 1:
            z_direction = "-" if negative_z else "+"
            self.install(dx, dz - 1, dy, cargo, negative_z)
            self.install(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
            self.pulse(dx, dz - 2, dy, negative_z)
            self.remove(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
        elif dx > 1:
            self.install(dx - 1, dz, dy, cargo, negative_z)
            self.install(dx - 2, dz, dy, f"xsp", negative_z)
            self.pulse(dx - 2, dz, dy, negative_z)
            self.remove(dx - 2, dz, dy, f"xsp", negative_z)
        else:
            if cargo != "special":
                print(f"install {cargo}")
            if dy == 1:
                print("toggle y")
            if (dz if negative_z else 1 - dz) == 1:
                print("toggle z")
            if dx == 1:
                print("toggle x")

    def remove(self, dx, dz, dy, cargo, negative_z):
        if dy > 1:
            self.install(dx, dz, dy - 2, "ysp", negative_z)
            self.pulse(dx, dz, dy - 2, negative_z)
            self.remove(dx, dz, dy - 2, "ysp", negative_z)
            self.remove(dx, dz, dy - 1, cargo, negative_z)
        elif dz > 1:
            z_direction = "-" if negative_z else "+"
            self.install(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
            self.pulse(dx, dz - 2, dy, negative_z)
            self.remove(dx, dz - 2, dy, f"zsp{z_direction}", negative_z)
            self.remove(dx, dz - 1, dy, cargo, negative_z)
        elif dx > 1:
            self.install(dx - 2, dz, dy, "xsp", negative_z)
            self.pulse(dx - 2, dz, dy, negative_z)
            self.remove(dx - 2, dz, dy, "xsp", negative_z)
            self.remove(dx - 1, dz, dy, cargo, negative_z)
        else:
            if dx == 1:
                print("toggle x")
            if (dz if negative_z else 1-dz) == 1:
                print("toggle z")
            if dy == 1:
                print("toggle y")
            if cargo != "special":
                print(f"remove {cargo}")

    def pulse(self, dx, dz, dy, negative_z):
        if dy > 1:
            self.install(dx, dz, dy - 1, "yo", negative_z)
            self.remove(dx, dz, dy - 1, "yo", negative_z)
        elif dz > 1:
            z_direction = "-" if negative_z else "+"
            self.install(dx, dz - 1, dy, f"zo{z_direction}", negative_z)
            self.remove(dx, dz - 1, dy, f"zo{z_direction}", negative_z)
        elif dx > 1:
            self.install(dx - 1, dz, dy, "xo", negative_z)
            self.remove(dx - 1, dz,  dy, "xo", negative_z)
        else:
            print(f"pulse {dx}")


# simulate_flight_sequence(flight_sequence, [
#     ["D","D","L","_","_","C","_"],
#     ["R","_","L","_","_","_","_"],
#     ["R","U","U","_","_","_","_"],
#     ["_","_","_","_","_","_","_"],
#     ["_","_","_","_","_","_","_"],
#     ["_","_","_","_","_","_","_"],
#     ["_","_","_","_","_","_","_"],
# ], (1, 1))
# install(3,3,3, "diamond")

f = FlyingMachine(2)
f.move_machine()