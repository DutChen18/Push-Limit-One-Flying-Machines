import sys

stack = 0

Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

# STACK_FINISHED = 0b000
# AXIS_ADJUSTED = 0b11
# CONTEXT_1 = 0b001
# CONTEXT_2 = 0b010
# CONTEXT_3 = 0b110
# CONTEXT_4 = 0b100
# CONTEXT_5 = 0b101

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}

y_height = 24  # 32
y_buffer = 2
n = 164

dynamic_variables = {
    "just_removed": 0,
    "active_axis": Y_AXIS,
    "y1": 3 * y_height + y_height + y_buffer,
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
}

constants = {
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
}

constant_addresses = {c: i for (i, c) in enumerate(constants)}
dynamic_variable_addresses = {c: (16 + i) for (i, c) in enumerate(dynamic_variables)}

var_addresses = dynamic_variable_addresses | constant_addresses

address_to_var = {v : k for k, v in var_addresses.items()}

def to_binary_string(num, length):
    num &= ((1 << length) - 1)
    assert num >= 0
    return ("0"*length + bin(num)[2:])[-length:]



variables = constants | dynamic_variables

for v, val in variables.items():
    print(to_binary_string(var_addresses[v], 5) + " " + to_binary_string(val, 12))

supported_branch_instructions = {
    "NONE": 0,
    "POP": 1,
    "NONZERO": 2,
    "NEGATIVE": 3,
}

code_to_branch = {v: k for (k, v) in supported_branch_instructions.items()}

supported_register_instructions = {
    "ADD": 0,
    "SUB": 1,
    "COPY": 2,
    "XOR": 3,
}
code_to_reg = {v: k for (k, v) in supported_register_instructions.items()}


supported_stack_instructions = {
    "NONE": 0,
    "TOGGLE": 1,
    "PUSH_0": 2,
    "PUSH_1": 3,
}

code_to_stack = {v: k for (k, v) in supported_stack_instructions.items()}

supported_output = {
    "pulse",
    "return_toggle",
    "fetch_toggle",
    "fetch_yp",
    "fetch_sp",
    "fetch_ysp",
    "fetch_o",
    "return_p",
    "return_sp",
    "return_ysp",
    "return_o",
}

states = set()


def handle_output(output):
    match output:
        case "pulse":
            print(f"pulse {variables["dx"]}")
        case "fetch_toggle":
            assert variables["active_axis"] == 0
            if variables['dy'] & 1 == 1:
                print("toggle y")
            if variables['dz'] & 1 == variables['negative_z'] & 1:
                print("toggle z")
            if variables['dx'] & 1 == 1:
                print("toggle x")
        case "return_toggle":  # the two toggles can be merged if the output came at the end of the state,
            # in which case active_axis would do the job
            if variables['dx'] & 1 == 1:
                print("toggle x")
            if variables['dz'] & 1 == variables['negative_z'] & 1:
                print("toggle z")
            if variables['dy'] & 1 == 1:
                print("toggle y")
        case "fetch_yp":
            print(f"install yp")
        case "fetch_sp":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"install {name}{"sp"}{sign}")
        case "fetch_ysp":
            print(f"install ysp")
        case "fetch_o":
            sign = ""
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
            print(f"install {_name_map[variables["active_axis"]]}{"o"}{sign}")
        case "return_p":
            print(f"remove yp")
        case "return_sp":
            sign = ""
            name = "x"
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
                name = "z"
            print(f"remove {name}{"sp"}{sign}")
        case "return_ysp":
            print(f"remove ysp")
        case "return_o":
            sign = ""
            if variables["active_axis"] & 1 == 0:
                sign = "-" if variables["negative_z"] else "+"
            print(f"remove {_name_map[variables["active_axis"]]}{"o"}{sign}")



def to_int(binary_string):
    return eval("0b" + binary_string)


def instruction_from_string(s):
    address, instruction, output = s.split(" ")
    address = to_int(address)
    B = to_int(instruction[:5])
    A = to_int(instruction[5:10])
    O = to_int(instruction[10:12])
    C = to_int(instruction[12:14])
    S = to_int(instruction[14:16])
    T = to_int(instruction[16::2])
    F = to_int(instruction[17::2])

    i = Instruction(
        code_to_stack[S],
        code_to_reg[O],
        code_to_branch[C],
        address_to_var[A],
        address_to_var[B],
        T ^ F,
        F ^ address,
        output=output if output != "None" else None,
        address=address
    )
    assert str(i) == s
    return i

class Instruction:
    def __init__(self,
                 stack_instruction,
                 register_instruction,
                 branch_instruction,
                 first_register_address,
                 second_register_address,
                 true_branch,
                 false_branch,
                 output=None,
                 address=None):
        assert stack_instruction in supported_stack_instructions
        assert register_instruction in supported_register_instructions
        assert branch_instruction in supported_branch_instructions
        assert output is None or output in supported_output
        self.data = (stack_instruction,
                     register_instruction,
                     branch_instruction,
                     first_register_address,
                     second_register_address,
                     true_branch,
                     false_branch,
                     output)
        if self.data in states:
            print(f"duplicate state {self.data}")
        states.add(self.data)
        self.stack_instruction = stack_instruction
        self.register_instruction = register_instruction
        self.branch_instruction = branch_instruction
        self.first_register_address = first_register_address
        self.second_register_address = second_register_address
        self.true_branch = true_branch
        self.false_branch = false_branch
        self.output = output
        self.address = address

    def get_data(self):
        return self.data

    def __call__(self, *args, **kwargs):
        global stack
        global variables
        if self.output is not None:
            handle_output(self.output)
        match self.stack_instruction:
            case "TOGGLE":
                stack ^= 1
            case "PUSH_0":
                stack <<= 1
            case "PUSH_1":
                stack <<= 1
                stack |= 1
            case "NONE":
                pass
            case _:
                assert False
        match self.register_instruction:
            case "ADD":
                operation_result = variables[self.first_register_address] + variables[self.second_register_address]
            case "SUB":
                operation_result = variables[self.second_register_address] - variables[self.first_register_address]
            case "COPY":
                operation_result = variables[self.first_register_address]
            case "XOR":
                operation_result = variables[self.first_register_address] ^ variables[self.second_register_address]
            case _:
                assert False
        match self.branch_instruction:
            case "NONE":
                variables[self.second_register_address] = operation_result
                return self.true_branch
            case "POP":
                variables[self.second_register_address] = operation_result
                bit = stack & 1
                stack >>= 1
                return self.true_branch if bit == 1 else self.false_branch
            case "NONZERO":
                return self.true_branch if operation_result != 0 else self.false_branch
            case "NEGATIVE":
                return self.true_branch if operation_result < 0 else self.false_branch
            case _:
                assert False

    def __str__(self):

        global var_addresses

        ret_val = ("000000000" + bin(self.address)[2:])[-8:] + " "
        F = ("000000000" + bin(self.false_branch ^ self.address)[2:])[-8:]
        if "b" in F:
            print(bin(self.false_branch ^ self.address))
            assert False
        T = ("000000000" + bin(self.true_branch ^ self.false_branch ^ self.address)[2:])[-8:]

        TF = "".join(u + v for u, v in zip(T, F))

        S = ("000000000" + bin(supported_stack_instructions[self.stack_instruction])[2:])[-2:]
        C = ("000000000" + bin(supported_branch_instructions[self.branch_instruction])[2:])[-2:]
        O = ("000000000" + bin(supported_register_instructions[self.register_instruction])[2:])[-2:]
        A = ("000000000" + bin(var_addresses[self.first_register_address])[2:])[-5:]
        B = ("000000000" + bin(var_addresses[self.second_register_address])[2:])[-5:]

        return ret_val + B + A + O + C + S + TF + " " + str(self.output)


def PUSH(c, X, output=None):
    return Instruction(stack_instruction=f"PUSH_{c}",
                       register_instruction="COPY",
                       branch_instruction="NONZERO",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=X,
                       output=output)


def POP(X, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="POP",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=Y,
                       output=output)


def ADD(x, y, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="ADD",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Y,
                       false_branch=Y,
                       output=output)


def SUB(x, y, Y, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="SUB",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Y,
                       false_branch=Y,
                       output=output)


def EQUALS(x, y, IF_TRUE, IF_FALSE, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="XOR",
                       branch_instruction="NONZERO",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=IF_FALSE,
                       false_branch=IF_TRUE,
                       output=output)


def LE(x, y, IF_TRUE, IF_FALSE, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="SUB",
                       branch_instruction="NEGATIVE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=IF_FALSE,
                       false_branch=IF_TRUE,
                       output=output)


def COPY(x, y, Z, output=None):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="NONE",
                       first_register_address=x,
                       second_register_address=y,
                       true_branch=Z,
                       false_branch=Z,
                       output=output)


def OUTPUT(X, output):
    return Instruction(stack_instruction=f"NONE",
                       register_instruction="COPY",
                       branch_instruction="NONZERO",
                       first_register_address="ZERO",
                       second_register_address="ZERO",
                       true_branch=X,
                       false_branch=X,
                       output=output)


def RETURN(X, cargo):
    return OUTPUT(X, f"return_{cargo}")


HALT = 255

instructions = {
    # begin main loop
    0: EQUALS("ONE", "first_loop", 10001, 10002),
    10001: EQUALS("C2", "y1", 138, 10003),
    10002: EQUALS("ZERO", "y1", 160, 10004),
    10003: SUB("THREE", "y1", 10005),
    10004: SUB("ONE", "y1", 10006),
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
    801: COPY("y1", "dy", 802),
    802: COPY("z2", "dz", 803),
    803: COPY("x", "dx", 804),
    804: COPY("ZERO", "negative_z", 51),
    # after second stack processing, update temp variables
    # increment x counter in x while loop
    135: ADD("ONE", "x", 4),
    # increment z counter in z while loop
    136: SUB("ONE", "z2", 2),
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
    9: LE("TWO", "dy", 10, 11),
    10: COPY("THREE", "active_axis", 26),
    11: EQUALS("THREE", "active_axis", 12, 15),
    12: PUSH(1, 14),

    14: PUSH(1, 15),
    # handle z
    15: LE("TWO", "dz", 16, 17),
    16: COPY("TWO", "active_axis", 26),
    17: LE("TWO", "active_axis", 18, 21),
    18: PUSH(1, 20),

    20: PUSH(1, 21),
    # handle x
    21: LE("TWO", "dx", 22, 23),
    22: COPY("ONE", "active_axis", 26),
    23: PUSH(1, 25),

    25: PUSH(1, 2601),
    2601: COPY("ZERO", "active_axis", 26),
    # decode where we called determine_active_axis
    26: LE("TWO", "dummy", 28, 27),
    27: EQUALS("ZERO", "dummy", 29, 52),
    28: EQUALS("TWO", "dummy", 81, 112),

    # recursively_remove_1 after call to determine_active_axis
    29: EQUALS("ZERO", "active_axis", 31, 3208),
    31: COPY("ONE", "just_removed", 61, "return_toggle"),  # return from rr1

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
    38: EQUALS("MINUS_TWO", "dummy", 48, 39),
    # if true we were called in ri6
    39: EQUALS("TWO", "dummy", 61, 40),
    40: EQUALS("ONE", "dummy", 41, 51),
    # called with 1
    41: POP(61, 901),

    # finish recursively_remove_1
    # 47: FETCH(48),

    48: EQUALS("THREE", "active_axis", 4801, 4802),
    4801: PUSH(1, 49, "fetch_ysp"),
    4802: PUSH(1, 49, "fetch_sp"),
    49: PUSH(0, 50),
    50: PUSH(1, 51),

    # recursively install 1
    # call determine_active_axis
    51: COPY("ONE", "dummy", 9),
    52: EQUALS("ZERO", "active_axis", 54, 55),
    54: COPY("ZERO", "just_removed", 61, "fetch_toggle"),  # return from RI1
    55: PUSH(0, 56),
    56: PUSH(0, 57),
    57: PUSH(1, 3209),

    # process_stack_instruction
    61: EQUALS("ZERO", "just_removed", 62, 69),
    62: POP(63, 64),  # ___ 0

    63: POP(76, 66),  # __1 0
    64: POP(67, 68),  # __0 0

    66: POP(77, 103),  # _01 0
    67: POP(126, 108),  # _10 0
    68: POP(99, 7601),  # _00 0

    69: POP(70, 71),  # ___ 1

    70: POP(76, 73),  # __1 1
    71: POP(74, 75),  # __0 1

    73: POP(119, 96),  # _01 1
    74: POP(129, 93),  # _10 1
    75: POP(129, 7601),  # _00 1
    # 111 on stack, just_removed anything
    76: ADD("ONE", "active_axis", 61),
    7601: EQUALS("ONE", "negative_z", 801, 135),

    # rr2
    77: PUSH(0, 78),
    78: PUSH(1, 79),
    79: PUSH(0, 80),
    80: COPY("TWO", "dummy", 9),
    81: EQUALS("ZERO", "active_axis", 8301, 87),
    8301: POP(8303, 8303, "pulse"),

    8303: POP(83, 83),
    83: ADD("ONE", "active_axis", 901),

    87: PUSH(1, 88, "fetch_o"),
    88: PUSH(0, 89),
    89: PUSH(0, 3209),

    # rr5 is just 93

    92: PUSH(0, 3201),
    93: EQUALS("THREE", "active_axis", 9301, 9302),
    9301: PUSH(0, 94, "return_ysp"),
    9302: PUSH(0, 94, "return_sp"),
    94: PUSH(0, 95),
    95: PUSH(1, 92),

    # rr6
    96: COPY("ONE", "just_removed", 98),
    98: PUSH(1, 3201),

    # rr3
    99: PUSH(1, 100),
    100: PUSH(1, 101),
    101: PUSH(0, 901),

    # ri2
    103: EQUALS("THREE", "active_axis", 1031, 1032),
    1031: PUSH(0, 104, "fetch_yp"),
    1032: PUSH(0, 104, "fetch_sp"),
    104: PUSH(1, 89),

    # ri3
    108: PUSH(1, 109),
    109: PUSH(0, 110),
    110: PUSH(1, 111),
    111: COPY("THREE", "dummy", 9),
    112: EQUALS("ZERO", "active_axis", 8301, 121),

    # ri6
    119: EQUALS("THREE", "active_axis", 11901, 11902),
    11901: COPY("ZERO", "just_removed", 3202, "return_p"),
    11902: COPY("ZERO", "just_removed", 3202, "return_sp"),

    # other branch of ri3
    121: PUSH(1, 104, "fetch_o"),
    # 122: PUSH(1, 89),
    # call modify_active_axis

    # ri4
    126: PUSH(1, 127),
    127: PUSH(0, 101),

    # ri5
    129: RETURN(92, "o"),

    # rr4 is ri5???

}

old_to_new = {255: 255}

index = 0
for k in instructions:
    old_to_new[k] = index
    index += 1

new_instructions = {}

machine_code = """00000000 11011001111110000000000000001011 None
00000001 10010000111110000000001100110110 None
00000010 10010001101110000000001111100000 None
00000011 10010010010100000000000000011110 None
00000100 10010001110100000000000000100100 None
00000101 10011001110000000000000000100110 None
00000110 10011010010000000000000000101001 None
00000111 10100001101000000000000001111111 None
00001000 10101000011000000000000010000001 None
00001001 10101001101110000000000001001011 None
00001010 10100001110000000000000010001001 None
00001011 10110010001000000000000010011111 None
00001100 10110001001110000000001101101110 None
00001101 11000100111000000000000010100111 None
00001110 10111101101000000000000010101001 None
00001111 11001101001000000000000111111111 None
00010000 11100001111000000000001001010001 None
00010001 11000100101000000000001000000111 None
00010010 11001101011000000000001000001001 None
00010011 10111101101000000000001000011111 None
00010100 11100001101000000001001100100000 None
00010101 10110001110000000000001101100011 None
00010110 10101001110100000000001101111101 None
00010111 10010000001000000000001001111111 None
00011000 10011001011000000000001010000001 None
00011001 11011001101000000000001111000011 None
00011010 11011001111000000000001010001001 None
00011011 10011010101000000000001010011111 None
00011100 10010000101000000101011010100101 None
00011101 11010001101000000000001010100111 None
00011110 11000010000111000000100000000011 None
00011111 10001010011000000000011110101110 None
00100000 10001010011110000000100000001001 None
00100001 00110001101010110000100000000111 None
00100010 00110001101010110000100000001001 None
00100011 11001010000111000000100000011101 None
00100100 10001010001000000000100001100001 None
00100101 10001010000111000000100010001111 None
00100110 00110001101010110000100000101001 None
00100111 00110001101010110000100001111111 None
00101000 10111010000111000000100010001011 None
00101001 10001001111000000000100010010010 None
00101010 00110001101010110000100010001001 None
00101011 00110001101010110000100010011111 None
00101100 10001001101000000000100010100001 None
00101101 11010010000111000000100010100100 None
00101110 11010001101110000010001111011110 None
00101111 11010010001110000001010100100110 None
00110000 10001001101110000000101000001011 None
00110001 10000001111000000001111101000111 return_toggle
00110010 11010010111000000000101000011000 None
00110011 11010010101000000000101000011011 None
00110100 11010001111000000000101000100100 None
00110101 11010010001000000000101000100111 None
00110110 10001010011110000000101010000011 None
00110111 11000110100000000000101001111010 None
00111000 10001010001110000000101010001011 None
00111001 11001110100000000000101010000110 None
00111010 10111110100000000000101010001001 None
00111011 11010010111110000000101010010000 None
00111100 11010010001110000011010110011110 None
00111101 11010001111110000010000000101111 None
00111110 00110001101001000010110010000111 None
00111111 10001010011110000001111111111101 None
01000000 00110001101010110010000000000100 fetch_ysp
01000001 00110001101010110010000000000111 fetch_sp
01000010 00110001101010100010000000001001 None
01000011 00110001101010110010000000011111 None
01000100 11010001111000000011000101100100 None
01000101 10001001101110000010000000100101 None
01000110 10000001101000000010000001111000 fetch_toggle
01000111 00110001101010100010000001111111 None
01001000 00110001101010100010000010000001 None
01001001 00110001101010110011010111000110 None
01001010 10000001101110000010001000000001 None
01001011 00110001101001000010000010011100 None
01001100 00110001101001000010001000100110 None
01001101 00110001101001000010001101011001 None
01001110 00110001101001000010111010000001 None
01001111 00110001101001000010010101010000 None
01010000 00110001101001000010100001100000 None
01010001 00110001101001000010001000000100 None
01010010 00110001101001000010001000010110 None
01010011 00110001101001000010001000010001 None
01010100 00110001101001000010010101111100 None
01010101 00110001101001000010010110101000 None
01010110 00110001101001000010101001010100 None
01010111 10001001110000000010001101111011 None
01011000 11100001111110000011001011100001 None
01011001 00110001101010100010001010000111 None
01011010 00110001101010110010001010001001 None
01011011 00110001101010100010001010011111 None
01011100 11010010001000000011001010100100 None
01011101 10001001101110000010100000001101 None
01011110 00110001101001000010001010101001 pulse
01011111 00110001101001000010011111111111 None
01100000 10001001110000000011110101010001 None
01100001 00110001101010110010100000000111 fetch_o
01100010 00110001101010100010100000001001 None
01100011 00110001101010100011100100001010 None
01100100 00110001101010100011100100100000 None
01100101 10001010011110000010100000100101 None
01100110 00110001101010100010100001111100 return_ysp
01100111 00110001101010100010100001111111 return_sp
01101000 00110001101010100010100010000001 None
01101001 00110001101010110010100011010011 None
01101010 10000001111000000010100010001001 None
01101011 00110001101010110011100111011111 None
01101100 00110001101010110010100010100001 None
01101101 00110001101010110010100010100111 None
01101110 00110001101010100011110110101101 None
01101111 10001010011110000010100111111101 None
01110000 00110001101010100010101000000100 fetch_yp
01110001 00110001101010100010101000000111 fetch_sp
01110010 00110001101010110010101100001001 None
01110011 00110001101010110010101000011111 None
01110100 00110001101010100010101000100001 None
01110101 00110001101010110010101000100111 None
01110110 11010010011000000011111001101000 None
01110111 10001001101110000010011001001001 None
01111000 10001010011110000010101010001011 None
01111001 10000001101000000011101011010010 return_p
01111010 10000001101000000011101011011101 return_sp
01111011 00110001101010110010101011001011 fetch_o
01111100 00110001101010110010101010100001 None
01111101 00110001101010100010101110100111 None
01111110 00110001101010000010101111101100 return_o"""

machine_from_binary = {}

for l in machine_code.split("\n"):
    i = instruction_from_string(l)
    machine_from_binary[i.address] = i

for k, v in instructions.items():
    (stack_instruction,
     register_instruction,
     branch_instruction,
     first_register_address,
     second_register_address,
     true_branch,
     false_branch,
     output) = v.get_data()
    true_branch = old_to_new[true_branch]
    false_branch = old_to_new[false_branch]
    new_instructions[old_to_new[k]] = Instruction(*(stack_instruction,
                                                    register_instruction,
                                                    branch_instruction,
                                                    first_register_address,
                                                    second_register_address,
                                                    true_branch,
                                                    false_branch,
                                                    output,
                                                    old_to_new[k]))


def run_instructions(start=0):
    new_code = start

    print(len(variables), len(new_instructions))
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
            current_instruction = machine_from_binary[new_code]
            new_code = current_instruction()
            # time.sleep(0.1)
        sys.stdout = out
    print(len(variables), len(new_instructions), len(witnessed_variables))
    print(variables)

    print(var_addresses)
    for i in new_instructions:
        print(new_instructions[i])




run_instructions()
