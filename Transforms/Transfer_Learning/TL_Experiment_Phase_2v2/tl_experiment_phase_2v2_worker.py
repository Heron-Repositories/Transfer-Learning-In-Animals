
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import numpy as np
import queue
import time
from statemachine import StateMachine
from Heron.communication.socket_for_serialization import Socket
from Heron.gui.visualisation_dpg import VisualisationDPG
from Heron import general_utils as gu
from Heron import constants as ct
import config as cfg
import state_machine as sm
import man_targ_trap as mtt
from datetime import datetime

no_mtt: bool
reward_on_poke_delay: float
levers_state: int
levers_states_dict = {'Off-Silent': 0, 'Off-Vibrating': 1,
                      'On-Vibrating-Right': 2, 'On-Vibrating-Left': 3, 'On-Vibrating-Random': 4,
                      'On-Silent-Right': 5, 'On-Silent-Left': 6, 'On-Silent-Random': 7}
min_distance_to_target: int
max_distance_to_target: int
target_position_limits: []
trap_offsets: []
target_offsets: []
speed: float
must_lift_at_target: bool
number_of_pellets: int
availability_on = False
poke_on = False
prev_avail = True
prev_poke = True
lever_press_time = 0.0
start_trial_lever_press_time = 0.0
interupted_lever_press_time = 0.0
mean_dt = 0.1
dt_history = queue.Queue(10)
current_time: float
state_machine: StateMachine
man_targ_trap: mtt.MTT
time_steps_of_wait_after_failure = 100  # This needs to be double the grace period which is defined in the TL_Levers
counter_after_failure = 0
vis: VisualisationDPG
record = [[0, 0]]
vis_times = []
correct_last_1min = []
failed_last_1min = []
starting_time = datetime.now()
previous_record = np.array([0, 0])


def initialise(_worker_object):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global min_distance_to_target
    global max_distance_to_target
    global target_position_limits
    global trap_offsets
    global target_offsets
    global speed
    global must_lift_at_target
    global number_of_pellets
    global worker_object
    global availability_on
    global state_machine
    global current_time
    global vis

    try:
        parameters = _worker_object.parameters
        no_mtt = parameters[1]
        reward_on_poke_delay = generate_reward_poke_delay_from_parameter(parameters[2])
        levers_state = levers_states_dict[parameters[3]]
        min_distance_to_target, max_distance_to_target = [int(i) for i in parameters[4].split(',')]
        target_offsets = [int(i) for i in parameters[5].split(',')]
        trap_offsets = [int(i) for i in parameters[6].split(',')]
        speed = parameters[7]
        must_lift_at_target = parameters[8]
        number_of_pellets = parameters[9]

    except Exception as e:
        print(e)
        return False

    cfg.number_of_pellets = number_of_pellets

    state_machine = sm.StateMachine(no_mtt, mean_dt)

    initialise_man_target_trap_object()

    current_time = time.perf_counter()

    worker_object.num_of_iters_to_update_relics_substate = -1
    worker_object.relic_create_parameters_df(visualisation=parameters[0],
                                             no_mtt=no_mtt,
                                             reward_on_poke_delay=reward_on_poke_delay,
                                             levers_state=levers_state,
                                             min_max_distance_to_target='{}, {}'.format(min_distance_to_target, max_distance_to_target),
                                             target_offsets=str(target_offsets),
                                             trap_offsets=str(trap_offsets),
                                             speed=speed,
                                             must_lift_at_target=must_lift_at_target,
                                             number_of_pellets=number_of_pellets)

    vis = VisualisationDPG(worker_object.node_name, worker_object.node_index,
                           _visualisation_type='Single Pane Plot', _buffer=100)

    return True


def visualise_correct_failed_trials():
    global vis
    global state_machine
    global record
    global previous_record
    global vis_times
    global correct_last_1min
    global failed_last_1min

    if state_machine.record[0] != previous_record[0] or state_machine.record[1] != previous_record[1]:

        correct = state_machine.record[0]
        failed = state_machine.record[1]
        record.append([correct, failed])
        vis_times.append((datetime.now() - starting_time).total_seconds())

        start_index = (np.abs(np.array(vis_times) - (vis_times[-1] - (5 * 60)))).argmin()  # moving window of 5 minutes

        correct_last_1min.append(record[-1][0] - record[start_index][0])
        failed_last_1min.append(record[-1][1] - record[start_index][1])

        correct_fails = np.array([correct_last_1min, failed_last_1min])

        if len(correct_last_1min) < 100:
            vis.visualise(np.array(correct_fails))
        else:
            vis.visualise(np.array(correct_fails)[:, -100:])

    previous_record[0] = state_machine.record[0]
    previous_record[1] = state_machine.record[1]


def generate_reward_poke_delay_from_parameter(parameter):
    list_of_numbers = [float(i) for i in parameter.split(' ')]
    if len(list_of_numbers) > 1:
        a = list_of_numbers[0]
        b = list_of_numbers[1]
        reward_poke_delay = (np.random.random() * (b-a)) + a
    else:
        reward_poke_delay = float(list_of_numbers[0])

    return reward_poke_delay


def initialise_man_target_trap_object():
    global man_targ_trap

    if not no_mtt:
        up_or_down = generate_up_or_down()
        man_targ_trap = mtt.MTT(min_distance_to_target, max_distance_to_target,
                                target_offsets, trap_offsets,
                                mean_dt, speed, must_lift_at_target, up_or_down)


def create_average_speed_of_levers_updating():
    global mean_dt
    global dt_history
    global current_time

    if dt_history.full():
        dt_history.get()
    dt_history.put(time.perf_counter() - current_time)

    #mean_dt = np.mean(dt_history.queue)
    #mean_dt = 0.2
    current_time = time.perf_counter()


def generate_up_or_down():
    global levers_state
    result = -1
    if levers_state == 2 or levers_state == 5:
        result = 0
    if levers_state == 3 or levers_state == 6:
        result = 1
    if levers_state == 4 or levers_state == 7:
        result = np.random.binomial(n=1, p=0.5)

    return result


def recalibrate_lever_press_time():
    global lever_press_time
    global start_trial_lever_press_time

    lever_press_time_from_end_of_last_trial = lever_press_time - start_trial_lever_press_time

    return lever_press_time_from_end_of_last_trial


def lever_press_time_with_interruption(lever_press_time_temp):
    global lever_press_time
    global interupted_lever_press_time

    if poke_on != 0 and lever_press_time_temp != 0:
        if state_machine.current_state == state_machine.failed:
            interupted_lever_press_time = 0
        lever_press_time = lever_press_time_temp + interupted_lever_press_time
    if poke_on == 0 and state_machine.break_timer == 0 and lever_press_time_temp == 0:
        lever_press_time = lever_press_time_temp
        interupted_lever_press_time = 0
    if (poke_on != 0 and lever_press_time_temp == 0) or \
            (poke_on == 0 and state_machine.break_timer > 0):
        interupted_lever_press_time = lever_press_time


def experiment(data, parameters, savenodestate_update_substate_df):
    global no_mtt
    global reward_on_poke_delay
    global levers_state
    global min_distance_to_target
    global max_distance_to_target
    global target_position_limits
    global trap_offsets
    global speed
    global number_of_pellets
    global availability_on
    global poke_on
    global lever_press_time
    global start_trial_lever_press_time
    global state_machine
    global prev_avail
    global prev_poke
    global man_targ_trap
    global counter_after_failure
    global vis
    global previous_record

    try:
        vis.visualisation_on = worker_object.parameters[0]
        levers_state = levers_states_dict[parameters[3]]
        min_distance_to_target, max_distance_to_target = [int(i) for i in parameters[4].split(',')]
        target_offsets = [int(i) for i in parameters[5].split(',')]
        trap_offsets = [int(i) for i in parameters[6].split(',')]
        speed = parameters[7]
        cfg.number_of_pellets = parameters[9]
    except:
        pass

    # Calculate the (running average) time it takes for the levers to push new data to this Node and update it for the
    # state_machine and the man_targ_trap objects that need it
    create_average_speed_of_levers_updating()
    state_machine.dt = mean_dt
    if not no_mtt:
        man_targ_trap.dt = mean_dt

    topic = data[0].decode('utf-8')
    message = data[1:]
    message = Socket.reconstruct_array_from_bytes_message(message)

    if 'Levers_Box_In' in topic:
        # The first element of the array is whether the rat is in the poke. The second is the milliseconds it has been
        # pressing either the left or the right lever (one is positive the other negative). If it is 0 then the rat is
        # not pressing a lever

        poke_on = message[0]
        lever_press_time = message[1]
        #lever_press_time_temp = message[1]
        #lever_press_time_with_interruption(lever_press_time_temp)
        #print(lever_press_time_temp, lever_press_time)

    if 'Food_Poke_Update' in topic:
        availability_on = message[0]
        #print('GOT NEW AVAILABILITY = {}'.format(availability_on))
        result = [np.array([ct.IGNORE]), np.array([ct.IGNORE]), np.array([ct.IGNORE])]
        return result

    if availability_on != prev_avail:
        #print(' ================ Availability = {}'.format(availability_on))
        prev_avail = availability_on

    if poke_on != prev_poke:
        #print(' ================ Poke = {}'.format(poke_on))
        prev_poke = poke_on

    command_to_vibration_arduino_controller = np.array(['d'])  # That means turn vibration off

    if not poke_on and not availability_on:
        if state_machine.current_state == state_machine.no_poke_no_avail:
            if state_machine.break_timer >= 6:
                initialise_man_target_trap_object()
            state_machine.running_around_no_availability_0()

        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.leaving_poke_early_2()

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            if state_machine.poke_timer < reward_on_poke_delay:
                state_machine.got_it_11()
            else:
                state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.wait_on_fail_16()
            counter_after_failure += 1
            if counter_after_failure > time_steps_of_wait_after_failure:
                state_machine.initialise_after_fail_13()
                #initialise_man_target_trap_object()
                counter_after_failure = 0

        elif state_machine.current_state == state_machine.succeeded:
            state_machine.initialise_after_success_14()
            initialise_man_target_trap_object()

    elif poke_on and not availability_on:
        if state_machine.current_state == state_machine.no_poke_no_avail:
            if not no_mtt and state_machine.break_timer == 0:
                reward_on_poke_delay = generate_reward_poke_delay_from_parameter(parameters[2])
                man_targ_trap.back_to_initial_positions()
                start_trial_lever_press_time = lever_press_time  # This is important for the correct recalibration of
                # the lever_press_time
                state_machine.man_targ_trap = man_targ_trap.positions_of_visuals
                if not no_mtt and levers_state < 2:  # print delay only for Stage 3
                    print(reward_on_poke_delay)
            state_machine.just_poked_1()

        if state_machine.current_state == state_machine.succeeded:
            reward_on_poke_delay = generate_reward_poke_delay_from_parameter(parameters[2])
            initialise_man_target_trap_object()
            #man_targ_trap.back_to_initial_positions()
            start_trial_lever_press_time = lever_press_time  # This is important for the correct recalibration of
            # the lever_press_time
            state_machine.man_targ_trap = man_targ_trap.positions_of_visuals
            state_machine.restart_after_succeed_19()

        # The state "Poke No Availability" (P_NA) is where most of the logic happens. Here is where the animal has to
        # either wait long enough (either looking at the manipulandum moving by itself (Stage 3) or not (Stage 2))
        # or manipulate the levers to reach the target (Stages 4 and 5)
        elif state_machine.current_state == state_machine.poke_no_avail:
            state_machine.waiting_in_poke_before_availability_3()

            if no_mtt:  # If the man., target, trap are invisible (Stage 2) ...
                if state_machine.poke_timer > reward_on_poke_delay:  # ... and the poke waiting time is up ...
                    availability_on = True
                    state_machine.availability_started_4()  # ... reward the animal.

            else:  # (Stages 3 to 5)
                if levers_state == 0 or levers_state == 1:  # If the Levers are off (Stage 3) ...
                    #  ... update the position of the manipulandum.
                    state_machine.man_targ_trap = \
                        man_targ_trap.calculate_positions_for_auto_movement(state_machine.poke_timer,
                                                                            reward_on_poke_delay)

                    if levers_state == 1:  # If the levers state is Off-Vibrating turn vibration on.
                        # and at Stage 3 always keep the trial (up or down) random
                        man_targ_trap.up_or_down = np.random.binomial(n=1, p=0.5)
                        if man_targ_trap.up_or_down:
                            command_to_vibration_arduino_controller = np.array(['a'])
                        else:
                            command_to_vibration_arduino_controller = np.array(['s'])

                    if state_machine.poke_timer > reward_on_poke_delay:  # If the poke waiting time is up ...
                        availability_on = True
                        state_machine.availability_started_4()  # ... reward the animal.

                else:  # If the Levers are on (being either on vibrate or on silent) (Stages 4 and 5)
                    lever_press_time_from_end_of_last_trial = recalibrate_lever_press_time()

                    state_machine.man_targ_trap = \
                        man_targ_trap.calculate_positions_for_levers_movement(lever_press_time_from_end_of_last_trial)
                    if 2 <= levers_state <= 4:  # If the levers state is On-Vibrating ...
                        # ... turn vibration on.
                        if man_targ_trap.up_or_down:
                            command_to_vibration_arduino_controller = np.array(['a'])
                        else:
                            command_to_vibration_arduino_controller = np.array(['s'])

                    if man_targ_trap.has_man_reached_target():  # If the man. reached the target ...
                        availability_on = True
                        state_machine.availability_started_4()  # ... reward the animal.
                    elif man_targ_trap.has_man_reached_trap():  # If the man. reached the trap ...
                        availability_on = False
                        state_machine.fail_to_trap_15()  # ... start again.

        elif state_machine.current_state == state_machine.poke_avail:
            state_machine.too_long_in_poke_9()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.too_long_running_around_10()

        elif state_machine.current_state == state_machine.failed:
            state_machine.wait_on_fail_16()
            counter_after_failure += 1
            if counter_after_failure > time_steps_of_wait_after_failure:
                state_machine.poking_at_fail_12()
                start_trial_lever_press_time = lever_press_time
                initialise_man_target_trap_object()
                counter_after_failure = 0

        elif state_machine.current_state == state_machine.succeeded:
            state_machine.wait_on_succeeded_17()
            initialise_man_target_trap_object()

    elif not poke_on and availability_on:
        if state_machine.current_state == state_machine.poke_avail:
            state_machine.leaving_poke_while_availability_6()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.running_around_while_availability_8()

    elif poke_on and availability_on:
        if state_machine.current_state == state_machine.poke_avail:
            # TODO I must make a parameter to differentiate the always poking experiment to the poke sometimes
            #state_machine.waiting_in_poke_while_availability_5()
            state_machine.succeed_at_constant_poke_18()

        elif state_machine.current_state == state_machine.no_poke_avail:
            state_machine.poking_again_while_availability_7()

        elif state_machine.current_state == state_machine.succeeded:
            state_machine.wait_on_succeeded_17()

    command_to_vibration_arduino_controller = np.array([ct.IGNORE])

    current_state = [state_machine.current_state.name, state_machine.current_state.identifier,
                     state_machine.current_state.value, state_machine.current_state.initial]
    savenodestate_update_substate_df(state=current_state,
                                     command_to_screens=state_machine.command_to_screens,
                                     command_to_food_poke=state_machine.command_to_food_poke[0],
                                     command_to_vibration_arduino_controller=command_to_vibration_arduino_controller[0],
                                     reward_dealy=reward_on_poke_delay,
                                     reward_availability=availability_on)

    result = [state_machine.command_to_screens,
              state_machine.command_to_food_poke,
              command_to_vibration_arduino_controller]
    if vis.visualisation_on:
        visualise_correct_failed_trials()

    #print(' ooo Comm to Screen = {}'.format(state_machine.command_to_screens))
    #print(state_machine.current_state)

    if state_machine.record[0] != previous_record[0] or state_machine.record[1] != previous_record[1]:
        print(state_machine.record)

        previous_record[0] = state_machine.record[0]
        previous_record[1] = state_machine.record[1]

    return result


def on_end_of_life():
    pass


if __name__ == "__main__":
    worker_object = gu.start_the_transform_worker_process(work_function=experiment,
                                                          end_of_life_function=on_end_of_life,
                                                          initialisation_function=initialise)
    worker_object.start_ioloop()
