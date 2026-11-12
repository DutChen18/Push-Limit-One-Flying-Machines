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
import time

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
y_buffer = 2
n = 4

variables = {
    "just_removed": 0,
    "active_axis": 0,
    "y1":  3 * y_height + y_height + y_buffer,
    "y2":  0,
    "z1": 0,
    "z2": n,
    "x": 2,
    "dx": 0,
    "dy": 0,
    "dz": 0,
    "dummy": 0,

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
    0: EQUALS("C2", "y1", TODO, 1),
    1: ADD("MINUS_THREE", "y1", 2),
    # begin first main z while loop
    2: EQUALS("ZERO", "z2", TODO, 3),
    3: ADD("ONE", "z1", 4),
    # begin first main x while loop
    4: EQUALS("C3", "x", TODO, 5),
    5: COPY("x", "dx", 6),
    6: COPY("y2", "dy", 7),
    7: COPY("z1", "dz", 8),
    8: COPY("ONE", "negative_z", 9),

    # recursively_remove_1
    # begins with call to determine_active_axis()
    # in the first call "dummy" is 0 already, so we don't need to set that code
    # In later calls we need to call this with COPY("ZERO", "dummy", 9)

    # determine_active_axis()
    9: G1("dy", 10, 11),
    10: COPY("Y_AXIS", "active_axis", 26),
    11: EQUALS("Y_AXIS", "active_axis", 12, 15),
    12: PUSHc((AXIS_ADJUSTED) & 1, 13),
    13: PUSHc((AXIS_ADJUSTED >> 1) & 1, 14),
    14: PUSHc((AXIS_ADJUSTED >> 2) & 1, 15),
    # handle z
    15: G1("dz", 16, 17),
    16: COPY("Z_AXIS", "active_axis", 26),
    17: G1("active_axis", 18, 21),
    18: PUSHc((AXIS_ADJUSTED) & 1, 19),
    19: PUSHc((AXIS_ADJUSTED >> 1) & 1, 20),
    20: PUSHc((AXIS_ADJUSTED >> 2) & 1, 21),
    # handle x
    21: G1("dx", 22, 23),
    22: COPY("X_AXIS", "active_axis", 26),
    23: PUSHc((AXIS_ADJUSTED) & 1, 24),
    24: PUSHc((AXIS_ADJUSTED >> 1) & 1, 25),
    25: PUSHc((AXIS_ADJUSTED >> 2) & 1, 26),
    # decode where we called determine_active_axis
    26: G1("dummy", 28, 27),
    27: EQUALS("ZERO", "dummy", 29, 52),
    28: EQUALS("TWO", "dummy", TODO, TODO),

    # recursively_remove_1 after call to determine_active_axis
    29: EQUALS("NO_AXIS", "active_axis", 30, 32),
    30: RETURN_BASE(31),
    31: COPY("ONE", "just_removed", TODO),  # return from rr1

    # Call modify_active_axis(dummy = -2)
    32: COPY("MINUS_TWO", "dummy", 33),

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
    39: EQUALS("TWO", "dummy", TODO, 40),
    40: EQUALS("ONE", "dummy", 41, 44),
    # called with 1
    41: POP(42, 43),
    # ?1 on the stack
    42: POP(TODO, TODO),
    # ?0 on the stack
    43: POP(TODO, TODO),
    # called with -1
    44: POP(45, 46),
    # ?1 on the stack
    45: POP(TODO, TODO),
    # 00 on the stack means called in ri1
    46: POP(TODO, 51),

    # finish recursively_remove_1
    47: FETCH(48, "sp"),
    48: PUSHc(CONTEXT_5 & 1, 49),
    49: PUSHc((CONTEXT_5 >> 1) & 1, 50),
    50: PUSHc((CONTEXT_5 >> 2) & 1, 51),

    # recursively install 1
    # call determine_active_axis
    51: COPY("ONE", "dummy", 9),
    52: EQUALS("NO_AXIS", "active_axis", 53, 55),
    53: FETCH_BASE(54),
    54: COPY("ZERO", "just_removed", TODO), # return from RI1
    55: PUSHc(CONTEXT_1 & 1, 56),
    56: PUSHc((CONTEXT_1 >> 1) & 1, 57),
    57: PUSHc((CONTEXT_1 >> 2) & 1, 58),
    # first call to modify_active_axis with -1 as argument
    58: PUSHc(0 & 1, 59),
    59: PUSHc((0 >> 1) & 1, 60),
    60: COPY("MINUS_ONE", "dummy", 33),
}


def run_instructions(start=0):
    current_instruction = instructions[start]
    while True:
        new_code = current_instruction()
        print(new_code)
        print(bin(stack))
        print(variables)
        current_instruction = instructions[new_code]
        time.sleep(0.5)


run_instructions()