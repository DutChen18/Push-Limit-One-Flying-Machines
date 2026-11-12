# PUSHc(X) pushes constant c in {0,1} to the stack, goes to X
# POP(X, Y) - pops a bit from stack, goes to X if 0, else Y.
# ADDc(x, Y) - adds c to x (-16 <= c <= 15) then goes to Y.
# EQUALS(x, y, Z, W) goes to Z if x == y else W.
# GE2(x, Y, Z) goes to Y if x >= 2, else Z.
# COPY(x, y, Z) copies x to y, then goes to Z
# FETCH(cargo, X)
# FETCH_BASE(cargo, X)
# RETURN(cargo, X)
# RETURN_BASE(cargo, X)
# PULSE(cargo, X)

stack = 0

Y_AXIS = 0b00
Z_AXIS = 0b01
X_AXIS = 0b10
NO_AXIS = 0b11

STACK_FINISHED = 0b000
AXIS_ADJUSTED = 0b111
CONTEXT_1 = 0b001
CONTEXT_2 = 0b010
CONTEXT_3 = 0b011
CONTEXT_4 = 0b100
CONTEXT_5 = 0b101

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}


y_height = 2  # 32
y_buffer = 3
n = 4

variables = {
    "just_installed": 1,
    "active_axis": 0,
    "y1":  3 * y_height + y_height + y_buffer,
    "y2":  0,
    "z1": 0,
    "z2": n,
    "x": 2,
    "dx": 0,
    "dy": 0,
    "dz": 0,

    # constants, don't modify until optimizing later
    "y_height": y_height,
    "n": n,
    "ZERO": 0,
    "c1": 3 * y_height + y_height + y_buffer,
    "c2": y_height + y_buffer,
    "c3": n + 2,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "Y_AXIS": Y_AXIS,
    "X_AXIS": X_AXIS,
    "Z_AXIS": Z_AXIS,
    "NO_AXIS": NO_AXIS,
}


def PUSHc(c, X):
    assert c in {0, 1}

    def push():
        global stack
        stack <<= 1
        stack |= c
        return X
    return push


def POP(X, Y):
    def pop():
        global stack
        bit = stack & 1
        stack >>= 1
        return X if bit == 0 else Y
    return pop


def ADDc(c, x, Y):
    assert -16 <= c < 16

    def add():
        global variables
        variables[x] += c
        return Y
    return add


def EQUALS(x, y, Z, W):
    def equals():
        global variables
        return Z if variables[x] == variables[y] else W
    return equals


def GE2(x, Y, Z):
    def ge2():
        global variables
        return Y if variables[x] in {0, 1} else Z
    return ge2


def COPY(x, y, Z):
    def copy():
        variables[y] = variables[x]
        return Z
    return copy


def UNDEFINED():
    def undefined():
        print("Hit undefined behavior")
        assert False
    return undefined


def FETCH(X, cargo):
    global variables

    def fetch():
        nonlocal cargo
        if variables["active_axis"] != Y_AXIS and cargo == "p":
            cargo = "sp"
        sign = ""
        if variables["active_axis"] == Z_AXIS:
            sign = "-" if variables["negative_z"] else "+"
        print(f"install {_name_map[variables["active_axis"]]}{cargo}{sign}")
        return X
    return fetch


def FETCH_BASE(X):
    global variables

    def fetch():
        if variables['dy'] == 1:
            print("toggle y")
        if variables['dz'] == variables['negative_z']:
            print("toggle z")
        if variables['dx'] == 1:
            print("toggle x")
        return X
    return fetch


def RETURN(X, cargo):
    global variables

    def ret():
        nonlocal cargo
        if variables["active_axis"] != Y_AXIS and cargo == "p":
            cargo = "sp"
        sign = ""
        if variables["active_axis"] == Z_AXIS:
            sign = "-" if variables["negative_z"] else "+"
        print(f"remove {_name_map[variables["active_axis"]]}{cargo}{sign}")
        return X

    return ret

def RETURN_BASE(X):
    global variables

    def fetch():
        if variables['dx'] == 1:
            print("toggle x")
        if variables['dz'] == variables['negative_z']:
            print("toggle z")
        if variables['dy'] == 1:
            print("toggle y")
        return X
    return fetch

TODO = -1
UNUSED = -2

instructions = {
    -1: UNDEFINED(),
    -2: UNDEFINED(),
    # begin first main y while loop
    0: EQUALS("y1", "c2", TODO, 1),
    1: ADDc(3, "y1", 2),
    # begin first main z while loop
    2: EQUALS("z2", "ZERO", TODO, 3),
    3: ADDc(1, "z1", 4),
    # begin first main x while loop
    4: EQUALS("x", "c3", TODO, 5),
    5: COPY("x", "dx", 6),
    6: COPY("y2", "dy", 7),
    7: COPY("z1", "dz", 8),
    8: COPY("ONE", "negative_z", 9),

    # recursively_remove_1
    # begins with inlined call to determine_active_axis()
    # handle y
    9: GE2("dy", 10, 11),
    10: COPY("Y_AXIS", "active_axis", 26),
    11: EQUALS("active_axis", "Y_AXIS", 12, 15),
    12: PUSHc((AXIS_ADJUSTED) & 1, 13),
    13: PUSHc((AXIS_ADJUSTED >> 1) & 1, 14),
    14: PUSHc((AXIS_ADJUSTED >> 2) & 1, 15),
    # handle z
    15: GE2("dz", 16, 17),
    16: COPY("Z_AXIS", "active_axis", 26),
    17: GE2("active_axis", 18, 21),
    18: PUSHc((AXIS_ADJUSTED) & 1, 19),
    19: PUSHc((AXIS_ADJUSTED >> 1) & 1, 20),
    20: PUSHc((AXIS_ADJUSTED >> 2) & 1, 21),
    # handle x
    21: GE2("dx", 22, 23),
    22: COPY("X_AXIS", "active_axis", 26),
    23: PUSHc((AXIS_ADJUSTED) & 1, 24),
    24: PUSHc((AXIS_ADJUSTED >> 1) & 1, 25),
    25: PUSHc((AXIS_ADJUSTED >> 2) & 1, 26),

    26: EQUALS("active_axis", "NO_AXIS", 27,  TODO),

}


def run_instructions(start=0):
    current_instruction = instructions[start]
    while True:
        new_code = current_instruction()
        print(new_code)
        current_instruction = instructions[new_code]


run_instructions()