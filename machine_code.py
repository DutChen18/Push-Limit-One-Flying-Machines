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
import sys
import time

stack = 0

Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

STACK_FINISHED = 0b000
AXIS_ADJUSTED = 0b111
CONTEXT_1 = 0b001
CONTEXT_2 = 0b010
CONTEXT_3 = 0b011
CONTEXT_4 = 0b100
CONTEXT_5 = 0b101

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}


y_height = 2  # 32
y_buffer = 2
n = 4

variables = {
    "just_removed": 0,
    "active_axis": Y_AXIS,
    "y1":  3 * y_height + y_height + y_buffer,
    "y2": -1,
    "z1": n,
    "z2": 0,
    "x": n + 2,
    "dx": n + 1,
    "dy": 0,
    "dz": 1,
    "dummy": 2,
    "first_loop": 1,
    "negative_z": 0,

    # constants, don't modify until optimizing later
    "Y_HEIGHT": y_height,
    "N": n,
    "C1": 3 * y_height + y_height + y_buffer,
    "C2": y_height + y_buffer,
    "C3": n + 2,
    "C4": y_height + y_buffer - 3,
    "ZERO": 0,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "MINUS_ONE": -1,
    "MINUS_TWO": -2,
    "MINUS_THREE": -3,
}


states = set()


def PUSHc(c, X):
    assert c in {0, 1}
    v = ("push", c, X)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)

    def push():
        global stack
        stack <<= 1
        stack |= c
        return X
    return push


def POP(IF_ONE, IF_ZERO):
    v = ("pop", IF_ONE, IF_ZERO)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    def pop():
        global stack
        bit = stack & 1
        stack >>= 1
        return IF_ONE if bit == 1 else IF_ZERO
    return pop


def ADD(x, y, Y):
    v = ("ADD", x, y, Y)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    def add():
        global variables
        variables[y] += variables[x]
        return Y
    return add


def EQUALS(x, y, IF_TRUE, IF_FALSE):
    v = ("EQUALS", x, y, IF_TRUE, IF_FALSE)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    def equals():
        global variables
        return IF_TRUE if variables[x] == variables[y] else IF_FALSE
    return equals


def G1(x, IF_TRUE, IF_FALSE):
    v = ("G1", x, IF_TRUE, IF_FALSE)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    def ge2():
        global variables
        return IF_TRUE if variables[x] > 1 else IF_FALSE
    return ge2


def COPY(x, y, Z):
    v = ("COPY", x, y, Z)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    def copy():
        variables[y] = variables[x]
        return Z
    return copy


def UNDEFINED():
    def undefined():
        sys.stderr.write("Hit undefined behavior\n")
        assert False
    return undefined


def FETCH(X, cargo):
    v = ("FETCH", X, cargo)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    global variables

    def fetch():
        nonlocal cargo
        new_cargo = cargo
        if _name_map[variables["active_axis"]] != "y" and new_cargo == "p":
            new_cargo = "sp"
        sign = ""
        if variables["active_axis"] == Z_AXIS:
            sign = "-" if variables["negative_z"] else "+"
        print(f"install {_name_map[variables["active_axis"]]}{new_cargo}{sign}")
        return X
    return fetch


def FETCH_BASE(X):
    v = ("FETCH_BASE", X)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
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
    v = ("RETURN", X)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    global variables

    def ret():
        nonlocal cargo
        new_cargo = cargo
        if _name_map[variables["active_axis"]] != "y" and new_cargo == "p":
            new_cargo = "sp"
        sign = ""
        if variables["active_axis"] == Z_AXIS:
            sign = "-" if variables["negative_z"] else "+"
        print(f"remove {_name_map[variables["active_axis"]]}{new_cargo}{sign}")
        return X

    return ret

def RETURN_BASE(X):
    v = ("RETURN_BASE", X)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
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

def PULSE(X):
    v = ("PULSE", X)
    if v in states:
        print(f"duplicate state {v}")
    states.add(v)
    global variables
    def pulse():
        print(f"pulse {variables["dx"]}")
        return X
    return pulse

TODO = -1
UNUSED = -2
HALT = -3

instructions = {
    # begin main loop
    0: EQUALS("ONE", "first_loop", 10001, 10002),
    10001: EQUALS("C2", "y1", 138, 10003),
    10002: EQUALS("ZERO", "y1", 160, 10004),
    10003: ADD("MINUS_THREE", "y1", 10005),
    10004: ADD("MINUS_ONE", "y1", 10006),
    10005: ADD("ONE", "y2", 20001),
    10006: ADD("THREE", "y2", 20001),

    20001: COPY("ZERO", "z1", 20002),
    20002: COPY("N", "z2", 2),
    # begin first main z while loop
    2: EQUALS("ZERO", "z2", 0, 3),
    3: ADD("ONE", "z1", 40001),
    40001: COPY("TWO", "x", 4),
    # begin first main x while loop
    4: EQUALS("C3", "x", 136, 5),
    5: COPY("y2", "dy", 6),
    6: COPY("x", "dx", 7),
    7: COPY("z1", "dz", 8),
    8: COPY("ONE", "negative_z", 901),
    # after stack processing, update temp variables
    801: COPY("y1", "dy",  802),
    802: COPY("z2", "dz", 803),
    803: COPY("x", "dx", 804),
    804: COPY("ZERO", "negative_z", 51),
    # after second stack processing, update temp variables
    # increment x counter in x while loop
    135: ADD("ONE", "x", 4),
    # increment z counter in z while loop
    136: ADD("MINUS_ONE", "z2", 2),
    # increment y counter in y while loop

    # second main loop
    138: COPY("Y_HEIGHT", "y1", 139),
    139: COPY("C4", "y2", 140),
    140: COPY("ZERO", "first_loop", 0),

    # restore the variables to their initial states
    160: COPY("ONE", "first_loop", 161),
    161: COPY("MINUS_ONE", "y2", 162),
    162: COPY("C1", "y1", HALT),

    # recursively_remove_1
    901: COPY("ZERO", "dummy", 9),
    # determine_active_axis()
    9: G1("dy", 10, 11),
    10: COPY("THREE", "active_axis", 26),
    11: EQUALS("THREE", "active_axis", 12, 15),
    12: PUSHc(1, 13),
    13: PUSHc(1, 14),
    14: PUSHc(1, 15),
    # handle z
    15: G1("dz", 16, 17),
    16: COPY("TWO", "active_axis", 26),
    17: G1("active_axis", 18, 21),
    18: PUSHc(1, 19),
    19: PUSHc(1, 20),
    20: PUSHc(1, 21),
    # handle x
    21: G1("dx", 22, 23),
    22: COPY("ONE", "active_axis", 26),
    23: PUSHc(1, 24),
    24: PUSHc(1, 25),
    25: PUSHc(1, 2601),
    2601: COPY("ZERO", "active_axis", 26),
    # decode where we called determine_active_axis
    26: G1("dummy", 28, 27),
    27: EQUALS("ZERO", "dummy", 29, 52),
    28: EQUALS("TWO", "dummy", 81, 112),

    # recursively_remove_1 after call to determine_active_axis
    29: EQUALS("ZERO", "active_axis", 30, 3208),
    30: RETURN_BASE(31),
    31: COPY("ONE", "just_removed", 61),  # return from rr1

    # Call modify_active_axis with various values of dummy
    3208: COPY("MINUS_TWO", "dummy", 33),
    3209: COPY("MINUS_ONE", "dummy", 33),
    3201: COPY("ONE", "dummy", 33),
    3202: COPY("TWO", "dummy", 33),

    # modify_active_axis(dummy)
    33: EQUALS("THREE", "active_axis", 34, 35),
    34: ADD("dummy", "dy", 38),
    35: EQUALS("TWO", "active_axis", 36, 37),
    36: ADD("dummy", "dz", 38),
    37: ADD("dummy", "dx", 38),
    # decode where we called modify_active_axis
    # if true we were called in rr1
    38: EQUALS("MINUS_TWO", "dummy", 47, 39),
    # if true we were called in ri6
    39: EQUALS("TWO", "dummy", 61, 40),
    40: EQUALS("ONE", "dummy", 41, 51),
    # called with 1
    41: POP(61, 901),

    # finish recursively_remove_1
    47: FETCH(48, "sp"),
    48: PUSHc(1, 49),
    49: PUSHc(0, 50),
    50: PUSHc(1, 51),

    # recursively install 1
    # call determine_active_axis
    51: COPY("ONE", "dummy", 9),
    52: EQUALS("ZERO", "active_axis", 53, 55),
    53: FETCH_BASE(54),
    54: COPY("ZERO", "just_removed", 61),  # return from RI1
    55: PUSHc(0, 56),
    56: PUSHc(0, 57),
    57: PUSHc(1, 3209),

    # process_stack_instruction
    61: EQUALS("ZERO", "just_removed", 62, 69),
    62: POP(63, 64),  # ___ 0

    63: POP(65, 66),  # __1 0
    64: POP(67, 68),  # __0 0

    65: POP(76, 126),  # _11 0
    66: POP(77, 102),  # _01 0
    67: POP(UNUSED, 108),  # _10 0
    68: POP(99, 7601),  # _00 0

    69: POP(70, 71),  # ___ 1

    70: POP(72, 73),  # __1 1
    71: POP(74, 75),  # __0 1

    72: POP(76, 129),  # _11 1
    73: POP(118, 96),  # _01 1
    74: POP(UNUSED, 90),  # _10 1
    75: POP(129, 7601),  # _00 1
    # 111 on stack, just_removed anything
    76: ADD("ONE", "active_axis", 61),
    7601: EQUALS("ONE", "negative_z", 801, 135),
    # 7603: EQUALS("ONE", "first_loop", 135, 157),

    # rr2
    77: PUSHc(0, 78),
    78: PUSHc(1, 79),
    79: PUSHc(0, 80),
    80: COPY("TWO", "dummy", 9),
    81: EQUALS("ZERO", "active_axis", 82, 86),
    82: PULSE(8301),
    8301: POP(8302, 8302),
    8302: POP(8303, 8303),
    8303: POP(83, 83),
    83: ADD("ONE", "active_axis", 901),
    86: FETCH(87, "o"),
    87: PUSHc(1, 88),
    88: PUSHc(0, 89),
    89: PUSHc(0, 3209),

    # rr5
    90: RETURN(93, "sp"),

    92: PUSHc(0, 3201),
    93: PUSHc(0, 94),
    94: PUSHc(0, 95),
    95: PUSHc(1, 92),

    # rr6
    96: COPY("ONE", "just_removed", 98),
    98: PUSHc(1, 3201),

    # rr3
    99: PUSHc(0, 100),
    100: PUSHc(1, 101),
    101: PUSHc(1, 901),

    # ri2
    102: FETCH(103, "p"),
    103: PUSHc(0, 104),
    104: PUSHc(1, 89),

    # ri3
    108: PUSHc(1, 109),
    109: PUSHc(0, 110),
    110: PUSHc(1, 111),
    111: COPY("THREE", "dummy", 9),
    112: EQUALS("ZERO", "active_axis", 82, 120),

    # ri6
    118: RETURN(119, "p"),
    119: COPY("ZERO", "just_removed", 3202),

    # other branch of ri3
    120: FETCH(121, "o"),
    121: PUSHc(0, 122),
    122: PUSHc(1, 57),
    # call modify_active_axis

    # ri4
    126: PUSHc(1, 127),
    127: PUSHc(0, 128),
    128: PUSHc(0, 901),

    # ri5
    129: RETURN(92, "o"),

    # rr4 is ri5???

}


def run_instructions(start=0):
    new_code = start

    print(len(variables), len(instructions))
    print(variables)
    witnessed_variables = set()
    with open("test42b.txt", "w", encoding="utf-8") as f:
        out = sys.stdout
        sys.stdout = f
        while new_code != HALT:
            witnessed_variables.add(new_code)

            # print(new_code)
            # print(bin(stack))
            # print(variables)
            current_instruction = instructions[new_code]
            new_code = current_instruction()
            # time.sleep(0.1)
        sys.stdout = out
    print(len(variables), len(instructions), len(witnessed_variables))
    print(variables)
run_instructions()