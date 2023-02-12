
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import copy
import numpy as np
import serial
from Heron import general_utils as gu
import state_machine as sm


arduino_serial: serial.Serial
loop_on = False
buffer = ''
state_machine = sm.LeversStateMachine(_grace_threshold=5)
time_step = 12  # Milliseconds


def initialise(_worker_object):
    global arduino_serial
    global loop_on
    global state_machine

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
    except Exception as e:
        print(e)
        return False

    try:
        arduino_serial = serial.Serial(com_port)
    except Exception as e:
        print(e)

    loop_on = True

    return True


def get_string(string_in):
    global buffer

    if '\n' in string_in:
        result = copy.copy(buffer) + copy.copy(string_in.split('\n')[0])
        buffer = copy.copy(string_in.split('\n')[1])
    else:
        buffer = buffer + copy.copy(string_in)
        result = False

    return result


def lever_string_to_ints(string):
    [poke_string, left_time_string, right_time_string, left_press_string, right_press_string] = string.split('#')
    poke_on = int(not int(poke_string.split('=')[1]))
    left_time = -int(left_time_string.split('=')[1])
    right_time = int(right_time_string.split('=')[1])
    left_press = -int(left_press_string.split('=')[1])
    right_press = int(right_press_string.split('=')[1])

    return poke_on, left_time, right_time, left_press, right_press


def get_lever_pressing_time():
    global state_machine

    poke = state_machine.poke
    lever_time = state_machine.lever_press_time * time_step

    return [poke, lever_time]


def arduino_data_capture(_worker_object):
    global arduino_serial
    global loop_on
    global state_machine

    worker_object = _worker_object

    while not loop_on:
        gu.accurate_delay(1)

    _worker_object.savenodestate_create_parameters_df(com_port=_worker_object.parameters[0])
    _worker_object.num_of_iters_to_update_savenodestate_substate = -1

    while loop_on:
        try:
            bytes_in_buffer = arduino_serial.in_waiting
            if bytes_in_buffer > 0:
                string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')
                final_string = get_string(string_in)
                if final_string:
                    poke_on, left_time, right_time, left_press, right_press = lever_string_to_ints(final_string)

                    worker_object.savenodestate_update_substate_df(poke_on=poke_on, left_time=left_time, right_time=right_time,
                                                                   left_press=left_press, right_press=right_press)

                    state_machine.do_transition(poke_on, left_press, right_press)

                    poke_and_time = get_lever_pressing_time()

                    result = np.array(poke_and_time)
                    worker_object.send_data_to_com(result)
        except:
            pass


def on_end_of_life():
    global arduino_serial
    arduino_serial.reset_input_buffer()
    arduino_serial.close()


if __name__ == "__main__":
    gu.start_the_source_worker_process(work_function=arduino_data_capture, end_of_life_function=on_end_of_life,
                                       initialisation_function=initialise)