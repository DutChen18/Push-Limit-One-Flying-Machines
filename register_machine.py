import sys
from enum import Enum
# All arms should go x direction, then z, then y out from active machine.
Y_AXIS = 0b11
Z_AXIS = 0b10
X_AXIS = 0b01
NO_AXIS = 0b00

_name_map = {Y_AXIS: "y", X_AXIS: "x", Z_AXIS: "z", NO_AXIS: "base"}


class StackInstructions(Enum):
    STACK_FINISHED = 0b000
    AXIS_ADJUSTED = 0b111
    CONTEXT_1 = 0b001
    CONTEXT_2 = 0b010
    CONTEXT_3 = 0b011
    CONTEXT_4 = 0b100
    CONTEXT_5 = 0b101


def push_to_stack(code, bits):

    global stack
    stack <<= bits
    if isinstance(code, Enum):
        code = code.value
    assert code & ((1 << bits) - 1) == code
    assert bits != 4
    stack ^= code
    # print(bin(stack))


def pop_from_stack(bits):
    global stack
    code = stack & ((1 << bits) - 1)
    stack >>= bits
    # print(bin(stack))
    return code


def determine_active_axis():
    global dx
    global dy
    global dz
    global active_axis
    assert active_axis != NO_AXIS
    if dy > 1:
        if active_axis != Y_AXIS:
            assert False
            push_to_stack(active_axis, 2)
            push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
        active_axis = Y_AXIS
    elif dz > 1:
        if active_axis != Z_AXIS:
            push_to_stack(active_axis, 2)
            push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
        active_axis = Z_AXIS
    elif dx > 1:
        if active_axis != X_AXIS:
            push_to_stack(active_axis, 2)
            push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
        active_axis = X_AXIS
    else:
        if active_axis != NO_AXIS:
            push_to_stack(active_axis, 2)
            push_to_stack(StackInstructions.AXIS_ADJUSTED.value, 3)
        active_axis = NO_AXIS
    # print(f"Determined active axis {active_axis}")


def modify_active_axis(modification):
    global dx
    global dy
    global dz
    global active_axis
    if active_axis == Y_AXIS:
        dy += modification
    elif active_axis == Z_AXIS:
        dz += modification
    elif active_axis == X_AXIS:
        dx += modification
    else:
        print("Tried to modify no axis ")
        assert False


def fetch_from_store(cargo):
    global active_axis
    global negative_z
    if active_axis != Y_AXIS and cargo == "p":
        cargo = "sp"
    sign = ""
    if active_axis == Z_AXIS:
        sign = "-" if negative_z else "+"
    print(f"install {_name_map[active_axis]}{cargo}{sign}")


def return_to_store(cargo):
    global active_axis
    if active_axis != Y_AXIS and cargo == "p":
        cargo = "sp"
    sign = ""
    if active_axis == Z_AXIS:
        sign = "-" if negative_z else "+"
    print(f"remove {_name_map[active_axis]}{cargo}{sign}")


def recursively_install_1():
    global dx
    global dy
    global dz
    global negative_z
    global active_axis
    global just_installed

    determine_active_axis()
    if active_axis == NO_AXIS:
        if dy == 1:
            print("toggle y")
        if dz ^ negative_z == 0:
            print("toggle z")
        if dx == 1:
            print("toggle x")
        just_installed = 1
    else:
        modify_active_axis(-1)
        push_to_stack(StackInstructions.CONTEXT_1, 3)
        recursively_install_1()


def recursively_install_2():
    # Context 2 for install
    modify_active_axis(-1)
    fetch_from_store("p")
    push_to_stack(StackInstructions.CONTEXT_2, 3)
    recursively_install_1()


def recursively_install_3():
    # Context 3 for install
    push_to_stack(StackInstructions.CONTEXT_5, 3)
    determine_active_axis()
    global active_axis
    if active_axis == NO_AXIS:
        print(f"pulse {dx}")
        assert pop_from_stack(3) == StackInstructions.AXIS_ADJUSTED.value
        active_axis = pop_from_stack(2)
        assert active_axis != NO_AXIS
        recursively_remove_1()  # can maybe be a goto into ri5
    else:
        modify_active_axis(-1)
        fetch_from_store("o")
        push_to_stack(StackInstructions.CONTEXT_3, 3)
        recursively_install_1()


def recursively_install_4():
    # Context 4 for remove
    push_to_stack(StackInstructions.CONTEXT_4, 3)
    recursively_remove_1()


def recursively_install_5():
    # Context 5 for remove
    return_to_store("o")
    modify_active_axis(1)
    # push_to_stack(StackInstructions.CONTEXT_5, 4)
    recursively_remove_1()


def recursively_install_6():
    global just_installed
    return_to_store("p")
    modify_active_axis(2)
    just_installed = 1


def recursively_remove_1():
    global dx
    global dy
    global dz
    global negative_z
    global active_axis
    global just_installed
    determine_active_axis()
    if active_axis == NO_AXIS:
        if dx == 1:
            print("toggle x")
        if dz ^ negative_z == 0:
            print("toggle z")
        if dy == 1:
            print("toggle y")
        just_installed = 0
    else:
        modify_active_axis(-2)
        fetch_from_store("sp")
        push_to_stack(StackInstructions.CONTEXT_5, 3)
        recursively_install_1()


def recursively_remove_2():
    global just_installed
    global active_axis
    push_to_stack(StackInstructions.CONTEXT_2, 3)
    determine_active_axis()
    if active_axis == NO_AXIS:
        print(f"pulse {dx}")
        assert pop_from_stack(3) == StackInstructions.AXIS_ADJUSTED.value
        active_axis = pop_from_stack(2)
        assert active_axis != NO_AXIS
        recursively_remove_1()
    else:
        modify_active_axis(-1)
        fetch_from_store("o")
        push_to_stack(StackInstructions.CONTEXT_4, 3)
        recursively_install_1()


def recursively_remove_3():
    push_to_stack(StackInstructions.CONTEXT_3, 3)
    recursively_remove_1()


def recursively_remove_4():
    return_to_store("o")
    modify_active_axis(1)
    recursively_remove_1()


def recursively_remove_5():
    return_to_store("sp")
    modify_active_axis(1)
    push_to_stack(StackInstructions.CONTEXT_1, 3)
    recursively_remove_1()


def recursively_remove_6():
    global just_installed
    modify_active_axis(1)
    just_installed = 0


def process_stack_instruction():
    # print(bin(stack))
    global just_installed
    global active_axis
    global dx
    global dy
    global dz
    global negative_z

    instruction = pop_from_stack(3)
    if instruction == StackInstructions.AXIS_ADJUSTED.value:
        active_axis = pop_from_stack(2)
        # print(f"Set active axis to {_name_map[active_axis]}")
        return

    match instruction, just_installed:
        case StackInstructions.CONTEXT_1.value, 1:
            recursively_install_2()
        case StackInstructions.CONTEXT_2.value, 1:
            recursively_install_3()
        case StackInstructions.CONTEXT_3.value, 1:
            recursively_install_4()
        case StackInstructions.CONTEXT_4.value, 0:
            recursively_install_5()
        case StackInstructions.CONTEXT_5.value, 0:
            recursively_install_6()

        case StackInstructions.CONTEXT_5.value, 1:
            recursively_remove_2()
        case StackInstructions.CONTEXT_4.value, 1:
            recursively_remove_3()
        case StackInstructions.CONTEXT_3.value, 0:
            recursively_remove_4()
        case StackInstructions.CONTEXT_2.value, 0:
            recursively_remove_5()
        case StackInstructions.CONTEXT_1.value, 0:
            recursively_remove_6()
        case _:
            print(f"DEFAULT {instruction} {just_installed}")
    return


y_height = 2 # 32
y_buffer = 3
n = 4  # 256

stack = 0
just_installed = 0
active_axis = 1
with open("test42a.txt", "w", encoding="utf-8") as f:
    sys.stdout = f
    for y in range(y_height):
        for z in range(0, -n, -1):
            for x in range(2, n + 2):
                dx = x
                dy = y
                dz = 1-z
                negative_z = 1

                active_axis = Y_AXIS
                # determine_active_axis()
                stack = 0
                # print(bin(stack))
                recursively_remove_1()
                while stack & 0b111 != 0:
                    # print(bin(stack))
                    process_stack_instruction()

                dx = x
                dy = 3 * (y_height - y - 1) + y_height + y_buffer
                dz = z + n
                negative_z = 0

                # print("here")

                active_axis = Y_AXIS
                # determine_active_axis()
                stack = 0
                # print(bin(stack))
                recursively_install_1()
                while stack & 0b111 != 0:
                    process_stack_instruction()
                # exit()

    for y in range(y_height - 1, -1, -1):
        for z in range(0, -n, -1):
            for x in range(2, n + 2):
                dx = x
                dz = 1-z
                dy = 3 * (y_height - y - 1) + y_height + y_buffer
                negative_z = 1

                active_axis = Y_AXIS
                stack = 0
                recursively_remove_1()
                while stack & 0b111 != 0:
                    process_stack_instruction()

                dx = x
                dz = z + n
                dy = y
                negative_z = 0

                active_axis = Y_AXIS
                stack = 0
                recursively_install_1()
                while stack & 0b111 != 0:
                    process_stack_instruction()



