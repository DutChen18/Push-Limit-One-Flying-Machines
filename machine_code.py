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
    "y2":  0,
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
    "ZERO": 0,
    "ONE": 1,
    "TWO": 2,
    "THREE": 3,
    "MINUS_ONE": -1,
    "MINUS_TWO": -2,
    "MINUS_THREE": -3,
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


def POP(IF_ONE, IF_ZERO):
    def pop():
        global stack
        bit = stack & 1
        stack >>= 1
        return IF_ONE if bit == 1 else IF_ZERO
    return pop


def ADD(x, y, Y):
    def add():
        global variables
        variables[y] += variables[x]
        return Y
    return add


def EQUALS(x, y, IF_TRUE, IF_FALSE):
    def equals():
        global variables
        return IF_TRUE if variables[x] == variables[y] else IF_FALSE
    return equals


def G1(x, IF_TRUE, IF_FALSE):
    def ge2():
        global variables
        return IF_TRUE if variables[x] > 1 else IF_FALSE
    return ge2


def COPY(x, y, Z):
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
    global variables
    def pulse():
        print(f"pulse {variables["dx"]}")
        return X
    return pulse

TODO = -1
UNUSED = -2
HALT = -3

instructions = {
    -1: UNDEFINED(),
    -2: UNDEFINED(),
    -3: UNDEFINED(),
    # begin first main y while loop
    0: EQUALS("C2", "y1", 138, 1),
    1: ADD("MINUS_THREE", "y1", 20001),
    20001: COPY("ZERO", "z1", 20002),
    20002: COPY("N", "z2", 2),
    # begin first main z while loop
    2: EQUALS("ZERO", "z2", 137, 3),
    3: ADD("ONE", "z1", 40001),
    40001: COPY("TWO", "x", 4),
    # begin first main x while loop
    4: EQUALS("C3", "x", 136, 5),
    5: COPY("x", "dx", 6),
    6: COPY("y2", "dy", 7),
    7: COPY("z1", "dz", 8),
    8: COPY("ONE", "negative_z", 901),
    # after stack processing, update temp variables
    801: COPY("x", "dx", 802),
    802: COPY("z2", "dz", 803),
    803: COPY("y1", "dy", 804),
    804: COPY("ZERO", "negative_z", 51),
    # after second stack processing, update temp variables
    # increment x counter in x while loop
    135: ADD("ONE", "x", 4),
    # increment z counter in z while loop
    136: ADD("MINUS_ONE", "z2", 2),
    # increment y counter in y while loop
    137: ADD("ONE", "y2", 0),

    # second main loop
    138: COPY("Y_HEIGHT", "y2", 139),
    139: COPY("C2", "y1", 140),
    140: COPY("ZERO", "first_loop", 141),
    141: EQUALS("ZERO", "y2", 160, 142),
    142: ADD("MINUS_ONE", "y2", 143),
    143: COPY("ZERO", "z1", 144),
    144: COPY("N", "z2", 145),
    145: EQUALS("ZERO", "z2", 159, 146),
    146: ADD("ONE", "z1", 147),
    147: COPY("TWO", "x", 148),
    148: EQUALS("C3", "x", 158, 149),
    149: COPY("x", "dx", 150),
    150: COPY("y1", "dy", 151),
    151: COPY("z1", "dz", 152),
    152: COPY("ONE", "negative_z", 901),
    # after processing first stack
    153: COPY("x", "dx", 154),
    154: COPY("z2", "dz", 155),
    155: COPY("y2", "dy", 156),
    156: COPY("ZERO", "negative_z", 51),
    # after processing second stack
    157: ADD("ONE", "x", 148),
    158: ADD("MINUS_ONE", "z2", 145),
    159: ADD("THREE", "y1", 141),

    # restore the variables to their initial states
    160: COPY("ONE", "first_loop", HALT),

    # recursively_remove_1
    901: COPY("ZERO", "dummy", 9),
    # determine_active_axis()
    9: G1("dy", 10, 11),
    10: COPY("Y_AXIS", "active_axis", 26),
    11: EQUALS("Y_AXIS", "active_axis", 12, 15),
    12: PUSHc(1, 13),
    13: PUSHc(1, 14),
    14: PUSHc(1, 15),
    # handle z
    15: G1("dz", 16, 17),
    16: COPY("Z_AXIS", "active_axis", 26),
    17: G1("active_axis", 18, 21),
    18: PUSHc(1, 19),
    19: PUSHc(1, 20),
    20: PUSHc(1, 21),
    # handle x
    21: G1("dx", 22, 23),
    22: COPY("X_AXIS", "active_axis", 26),
    23: PUSHc(1, 24),
    24: PUSHc(1, 25),
    25: PUSHc(1, 2601),
    2601: COPY("NO_AXIS", "active_axis", 26),
    # decode where we called determine_active_axis
    26: G1("dummy", 28, 27),
    27: EQUALS("ZERO", "dummy", 29, 52),
    28: EQUALS("TWO", "dummy", 81, 112),

    # recursively_remove_1 after call to determine_active_axis
    29: EQUALS("NO_AXIS", "active_axis", 30, 3208),
    30: RETURN_BASE(31),
    31: COPY("ONE", "just_removed", 61),  # return from rr1

    # Call modify_active_axis with various values of dummy
    3208: COPY("MINUS_TWO", "dummy", 33),
    3209: COPY("MINUS_ONE", "dummy", 33),
    3201: COPY("ONE", "dummy", 33),
    3202: COPY("TWO", "dummy", 33),

    # modify_active_axis(dummy)
    33: EQUALS("Y_AXIS", "active_axis", 34, 35),
    34: ADD("dummy", "dy", 38),
    35: EQUALS("Z_AXIS", "active_axis", 36, 37),
    36: ADD("dummy", "dz", 38),
    37: ADD("dummy", "dx", 38),
    # decode where we called modify_active_axis
    # if true we were called in rr1
    38: EQUALS("MINUS_TWO", "dummy", 47, 39),
    # if true we were called in ri6
    39: EQUALS("TWO", "dummy", 61, 40),
    40: EQUALS("ONE", "dummy", 41, 44),
    # called with 1
    41: POP(42, 43),
    42: POP(901, 61),  # _1 1
    43: POP(901, 901),  # _0 1
    # called with -1
    44: POP(45, 46),
    # 01 -1 on the stack means called in rr2
    45: POP(51, 51),  # _1 -1
    # 00 on the stack means called in ri1
    # 10 on the stack means called in ri1
    46: POP(51, 51),  # _0 -1

    # finish recursively_remove_1
    47: FETCH(48, "sp"),
    48: PUSHc(1, 49),
    49: PUSHc(0, 50),
    50: PUSHc(1, 51),

    # recursively install 1
    # call determine_active_axis
    51: COPY("ONE", "dummy", 9),
    52: EQUALS("NO_AXIS", "active_axis", 53, 55),
    53: FETCH_BASE(54),
    54: COPY("ZERO", "just_removed", 61),  # return from RI1
    55: PUSHc(0, 56),
    56: PUSHc(0, 57),
    57: PUSHc(1, 58),
    # first call to modify_active_axis with -1 as argument
    58: PUSHc(0, 59),
    59: PUSHc(0, 3209),

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

    72: POP(76, 132),  # _11 1
    73: POP(118, 96),  # _01 1
    74: POP(UNUSED, 90),  # _10 1
    75: POP(129, 7601),  # _00 1
    # 111 on stack, just_removed anything
    76: ADD("ONE", "active_axis", 61),
    7601: EQUALS("ONE", "negative_z", 7602, 7603),
    7602: EQUALS("ONE", "first_loop", 801, 153),
    7603: EQUALS("ONE", "first_loop", 135, 157),

    # rr2
    77: PUSHc(0, 78),
    78: PUSHc(1, 79),
    79: PUSHc(0, 80),
    80: COPY("TWO", "dummy", 9),
    81: EQUALS("NO_AXIS", "active_axis", 82, 86),
    82: PULSE(8301),
    8301: POP(8302, 8302),
    8302: POP(8303, 8303),
    8303: POP(83, 83),
    83: ADD("ONE", "active_axis", 901),
    84: PUSHc(0, 85),
    85: PUSHc(1, 3209),
    86: FETCH(87, "o"),
    87: PUSHc(1, 88),
    88: PUSHc(0, 89),
    89: PUSHc(0, 84),

    # rr5
    90: RETURN(93, "sp"),
    91: PUSHc(0, 92),
    92: PUSHc(0, 3201),
    93: PUSHc(0, 94),
    94: PUSHc(0, 95),
    95: PUSHc(1, 91),

    # rr6
    96: COPY("ONE", "just_removed", 97),
    97: PUSHc(0, 98),
    98: PUSHc(1, 3201),

    # rr3
    99: PUSHc(0, 100),
    100: PUSHc(1, 101),
    101: PUSHc(1, 901),

    # ri2
    102: FETCH(103, "p"),
    103: PUSHc(0, 104),
    104: PUSHc(1, 105),
    105: PUSHc(0, 106),
    106: PUSHc(1, 107),
    107: PUSHc(0, 3209),

    # ri3
    108: PUSHc(1, 109),
    109: PUSHc(0, 110),
    110: PUSHc(1, 111),
    111: COPY("THREE", "dummy", 9),
    112: EQUALS("NO_AXIS", "active_axis", 113, 120),
    113: PULSE(114),
    114: POP(115, 115),
    115: POP(116, 116),
    116: POP(117, 117),
    117: ADD("ONE", "active_axis", 901),

    # ri6
    118: RETURN(119, "p"),
    119: COPY("ZERO", "just_removed", 3202),

    # other branch of ri3
    120: FETCH(121, "o"),
    121: PUSHc(0, 122),
    122: PUSHc(1, 123),
    123: PUSHc(1, 124),
    # call modify_active_axis
    124: PUSHc(1, 125),
    125: PUSHc(1, 3209),

    # ri4
    126: PUSHc(1, 127),
    127: PUSHc(0, 128),
    128: PUSHc(0, 901),

    # ri5
    129: RETURN(130, "o"),
    130: PUSHc(1, 131),
    131: PUSHc(0, 3201),

    # rr4
    132: RETURN(133, "o"),
    133: PUSHc(1, 134),
    134: PUSHc(1, 3201),

}


def run_instructions(start=0):
    new_code = start

    print(len(variables), len(instructions))
    print(variables)
    with open("test42b.txt", "w", encoding="utf-8") as f:
        out = sys.stdout
        sys.stdout = f
        while new_code != HALT:


            # print(new_code)
            # print(bin(stack))
            # print(variables)
            current_instruction = instructions[new_code]
            new_code = current_instruction()
            # time.sleep(0.1)
        sys.stdout = out
    print(len(variables), len(instructions))
    print(variables)
run_instructions()