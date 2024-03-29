
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import serial
import threading
import pandas as pd
from datetime import datetime
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu, constants as ct

need_parameters = True
arduino_serial: serial.Serial
avail_time: float
avail_freq: int
succ_freq: int
fail_freq: int
sleep_dt = 0.18
abort_at_wrong_poke: bool
air_puff_at_wrong_poke: bool
trigger_string: str
pandas_file: str
pandas_trials_record: pd.DataFrame
availability_period_is_running = False
reward_amount = 1
reward_poke: bool  # False is the Old / Right poke, True is the New / Left one
air_puff_thread_is_running: bool
air_puff_timer = 0
succesful_trials = 0
success_failure_continue = None
was_last_trial_successful = False


def add_timestamp_to_filename(save_file):

    filename = save_file.split('.')
    date_time = '{}'.format(datetime.now()).replace(':', '-').replace(' ', '_').split('.')[0]
    save_file = '{}_{}.{}'.format(filename[0], date_time, filename[1])

    return save_file


def freq_to_signal(freq):
    freq = int(freq)
    if freq < 500:
        freq = 500
    if freq > 5000:
        freq = 5000
    return chr(int(freq/500 + 97)).encode('utf-8')


def initialise(_worker_object):
    global arduino_serial
    global avail_time
    global avail_freq
    global succ_freq
    global fail_freq
    global abort_at_wrong_poke
    global air_puff_at_wrong_poke
    global trigger_string
    global pandas_file
    global pandas_trials_record
    global reward_poke
    global air_puff_thread_is_running

    try:
        parameters = _worker_object.parameters
        com_port = parameters[0]
        avail_time = parameters[1]
        avail_freq = parameters[2]
        succ_freq = parameters[3]
        fail_freq = parameters[4]
        abort_at_wrong_poke = parameters[5]
        air_puff_at_wrong_poke = parameters[6]
        trigger_string = parameters[7]
        pandas_file = parameters[8]
    except Exception as e:
        print(e)
        return False

    try:
        arduino_serial = serial.Serial(com_port)
    except Exception as e:
        print(e)
        return False

    if pandas_file != '':
        pandas_trials_record = pd.DataFrame(columns=['TimeStamp', 'Start_OR_PelletsGiven'])

    air_puff_thread_is_running = False
    reward_poke = True
    set_poke_tray()

    worker_object.savenodestate_create_parameters_df(com_port=com_port, avail_time=avail_time, avail_freq=avail_freq,
                                                     succ_freq=succ_freq, fail_freq=fail_freq,
                                                     abort_at_wrong_poke=abort_at_wrong_poke,
                                                     air_puff_at_wrong_poke=air_puff_at_wrong_poke,
                                                     trigger_string=trigger_string, pandas_file=pandas_file)

    return True


def failure_sound():
    if int(fail_freq) != 0:
        arduino_serial.write(freq_to_signal(fail_freq))
        gu.accurate_delay(1200 * sleep_dt)
        arduino_serial.write(freq_to_signal(500))


def success_sound():
    if int(succ_freq) != 0:
        arduino_serial.write(freq_to_signal(succ_freq))
        gu.accurate_delay(1500 * sleep_dt)
        arduino_serial.write(freq_to_signal(succ_freq))
    gu.accurate_delay(1500 * sleep_dt)


def availability_sound():
    if int(avail_freq) != 0:
        arduino_serial.write(freq_to_signal(avail_freq))


def add_trial_state_to_trials_record(state):
    global pandas_trials_record
    global pandas_file

    if pandas_file != '':
        time = datetime.now()
        row = pd.DataFrame(data={pandas_trials_record.columns[0]: [time], pandas_trials_record.columns[1]: [state]})
        pandas_trials_record = pd.concat([pandas_trials_record, row])


def start_availability_thread():
    global arduino_serial
    global availability_period_is_running
    global avail_time
    global avail_freq
    global succ_freq
    global pandas_file
    global pandas_trials_record
    global reward_poke
    global abort_at_wrong_poke
    global succesful_trials
    global was_reward_collected
    global success_failure_continue
    global was_last_trial_successful

    total_steps = int(avail_time / sleep_dt)

    add_trial_state_to_trials_record('Start')

    bytes_in_buffer = arduino_serial.in_waiting
    while bytes_in_buffer:
        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')
        if '555\r\n' in string_in:
            gu.accurate_delay(500)
        arduino_serial.reset_input_buffer()
    step = 0

    while availability_period_is_running:

        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')

        success_failure_continue = 2  # 0=success, 1=failure, 2=continue
        # If the string is either 555 or 666 then if it is for the wrong poke and the abort_at_wrong_poke is on then
        # fail, otherwise succeed
        if bytes_in_buffer:
            if '555\r\n' in string_in:
                if not reward_poke:
                    success_failure_continue = 0
                else:
                    if abort_at_wrong_poke:
                        success_failure_continue = 1
                    else:
                        success_failure_continue = 0
            if '666\r\n' in string_in:
                if reward_poke:
                    success_failure_continue = 0
                else:
                    if abort_at_wrong_poke:
                        success_failure_continue = 1
                    else:
                        success_failure_continue = 0

        if success_failure_continue == 0:
            try:
                success_sound()
                for _ in np.arange(reward_amount):
                    arduino_serial.write('a'.encode('utf-8'))
                    gu.accurate_delay(700)
                was_last_trial_successful = True
                availability_period_is_running = False
                succesful_trials += 1
                print(succesful_trials)
            except Exception as e:
                print(e)
            add_trial_state_to_trials_record(reward_amount)
        elif step >= total_steps or success_failure_continue == 1:
            try:
                failure_sound()
                was_last_trial_successful = False
                availability_period_is_running = False
            except Exception as e:
                print(e)
            add_trial_state_to_trials_record(0)
        else:
            try:
                availability_sound()
                arduino_serial.read(arduino_serial.in_waiting)
                availability_period_is_running = True
            except Exception as e:
                print(e)
            gu.accurate_delay(1000 * sleep_dt)
        step += 1


def set_poke_tray():
    global arduino_serial
    global reward_poke

    if reward_poke:
        arduino_serial.write('m'.encode('utf-8'))
    else:
        arduino_serial.write('n'.encode('utf-8'))


def start_air_puff_thread():
    global availability_period_is_running
    global air_puff_thread_is_running
    global previous_availability_for_air_puff
    global air_puff_timer

    while air_puff_thread_is_running:
        if availability_period_is_running:
            air_puff_timer = 0
        if not availability_period_is_running:
            air_puff_timer += 1
            if air_puff_timer < 50:
                arduino_serial.reset_input_buffer()
            else:  # 5 seconds delay
                air_puff_if_poking_outside_availability()

        gu.accurate_delay(100)


def air_puff_if_poking_outside_availability():

    if not availability_period_is_running:
        bytes_in_buffer = arduino_serial.in_waiting
        string_in = arduino_serial.read(bytes_in_buffer).decode('utf-8')

        if bytes_in_buffer:
            if '555\r\n' in string_in or '666\r\n' in string_in:
                arduino_serial.write('y'.encode('utf-8'))
                gu.accurate_delay(100)
                arduino_serial.write('z'.encode('utf-8'))


def start_availability_or_switch_pokes(data, parameters):
    global availability_period_is_running
    global air_puff_thread_is_running
    global trigger_string
    global reward_amount
    global reward_poke
    global success_failure_continue
    global succesful_trials

    topic = data[0].decode('utf-8')
    message = Socket.reconstruct_data_from_bytes_message(data[1:])

    air_puff_at_wrong_poke = parameters[5]

    if air_puff_at_wrong_poke:
        if not air_puff_thread_is_running:
            air_puff_thread_is_running = True
            air_puff_thread = threading.Thread(group=None, target=start_air_puff_thread)
            air_puff_thread.start()
    else:
        air_puff_thread_is_running = False

    if 'Start' in topic:
        if not availability_period_is_running:
            if len(message.shape) > 1:  # If the message is sent as a double array
                message = message[0]
            if trigger_string == message[0] or trigger_string == 'number':
                if trigger_string == 'number':
                    if int(message[0]) != -1:
                        reward_amount = int(message[0])
                try:
                    if message[0] != -1 and message[0] != '-1':  # That allows the result to update without starting another thread
                        availability_period_is_running = True
                        avail_thread = threading.Thread(target=start_availability_thread)
                        avail_thread.start()
                except Exception as e:
                    print(e)
        result = [np.array([availability_period_is_running, was_last_trial_successful, succesful_trials])]

    elif 'Poke' in topic:
        reward_poke = message[0]
        if reward_poke == 'Left' or reward_poke == 'New':
            reward_poke = True
        if reward_poke == 'Right' or reward_poke == 'Old':
            reward_poke = False
        set_poke_tray()
        result = [np.array([availability_period_is_running, was_last_trial_successful, succesful_trials])]

    return result


def on_end_of_life():
    global air_puff_thread_is_running
    global pandas_file
    global pandas_trials_record

    if pandas_file != '':
        pandas_file = add_timestamp_to_filename(pandas_file)
        pandas_trials_record.to_pickle(pandas_file)

    air_puff_thread_is_running = False
    gu.accurate_delay(100)

    try:
        global arduino_serial
        arduino_serial.reset_input_buffer()
        arduino_serial.close()
    except:
        pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=start_availability_or_switch_pokes,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
