# This is the code of the worker part of the Sink Operation. Here the user needs to write most of the code in order to
# define the Operation's functionality.

# <editor-fold desc="The following 6 lines of code are required to allow Heron to be able to see the Operation without
# package installation. Do not change.">
import sys
from os import path

current_dir = path.dirname(path.abspath(__file__))
node_dir = current_dir
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))
# </editor-fold>

# <editor-fold desc="Extra imports if required">
import subprocess
import zmq
from Heron.communication.socket_for_serialization import Socket
from Heron import general_utils as gu

# </editor-fold>

# <editor-fold desc="Global variables.
unity_socket_pub: zmq.Socket
unity_socket_rep: zmq.Socket
unity_process: subprocess.Popen
monitors: str
previous_monitors = None
sprites: dict
rotation: bool
opacity_target_trap: float
previous_opacity_target_trap = None
opacity_cue: float
previous_opacity_cue = None
screen_colour: int
main_screen_x_size = 2561 + 1280
sprite_screens_x_size = 1980
previous_message = 'Hi'



# </editor-fold>


def get_parameters(_worker_object):
    global monitors
    global previous_monitors
    global rotation
    global opacity_target_trap
    global previous_opacity_target_trap
    global opacity_cue
    global previous_opacity_cue

    try:
        parameters = _worker_object.parameters
        monitors = parameters[0]
        previous_monitors = monitors
        rotation = parameters[1]
        opacity_target_trap = parameters[2]
        previous_opacity_target_trap = opacity_target_trap
        opacity_cue = parameters[3]
        previous_opacity_cue = opacity_cue
    except Exception as e:
        print(e)
        return False

    _worker_object.savenodestate_create_parameters_df(monitors=monitors, rotation=rotation,
                                                     opacity_target_trap=opacity_target_trap,
                                                     opacity_cue=opacity_cue)
    _worker_object.num_of_iters_to_update_savenodestate_substate = 1000

    return True


def connect_sockets():
    global unity_socket_pub
    global unity_socket_rep

    try:
        unity_context = zmq.Context()
        unity_socket_pub = unity_context.socket(zmq.PUB)
        unity_socket_pub.bind("tcp://*:12346")
        unity_socket_rep = unity_context.socket(zmq.REP)
        unity_socket_rep.bind("tcp://*:12345")
    except Exception as e:
        print(e)
        return False

    return True


def start_unity_exe():
    global unity_process
    try:
        unity_exe = path.join(node_dir, '__Unity_TL_Task2_Screens_Project', 'Builds', 'TL_Task2_Screens_Unity.exe')
        unity_process = subprocess.Popen(unity_exe)
        print(unity_process)
    except Exception as e:
        print(e)
        return False

    return True


def first_communication_with_Unity():
    try:
        # That will lock until Unity has send a request but that means the process will be killed in 5 secs of inactivity
        unity_socket_rep.recv_string()
        unity_socket_rep.send_string('Python knows Unity is up.')
        gu.accurate_delay(100)

        # Once the req rep handshake has happened then we can send commands to the Unity exe
        screens_message_out = str('Screens:{}'.format(monitors))
        unity_socket_pub.send_string(screens_message_out)
        gu.accurate_delay(100)
        movement_type_message_out = str('MovementType:{}'.format(rotation))
        unity_socket_pub.send_string(movement_type_message_out)
        gu.accurate_delay(100)
        opacity_tt_message_out = str('OpacityTT:{}'.format(opacity_target_trap))
        unity_socket_pub.send_string(opacity_tt_message_out)
        gu.accurate_delay(100)
        opacity_cue_message_out = str('OpacityCue:{}'.format(opacity_cue))
        unity_socket_pub.send_string(opacity_cue_message_out)
    except Exception as e:
        print(e)
        return False

    return True


def initialise(_worker_object):
    if not get_parameters(_worker_object):
        return False

    if not connect_sockets():
        return False

    if not start_unity_exe():
        return False

    if not first_communication_with_Unity():
        return False

    return True


def work_function(data, parameters, savenodestate_update_substate_df):
    global unity_socket_pub
    global previous_message
    global previous_opacity_target_trap
    global previous_monitors
    global previous_opacity_cue

    topic = data[0]
    message_in = data[1:]
    message_in = Socket.reconstruct_data_from_bytes_message(message_in)[0]

    monitors = parameters[0]
    opacity_target_trap = parameters[2]
    opacity_cue = parameters[3]

    # Parameters updates
    if monitors != previous_monitors:
        screens_message_out = str('Screens:{}'.format(monitors))
        unity_socket_pub.send_string(screens_message_out)
        previous_monitors = monitors

    if previous_opacity_target_trap != opacity_target_trap:
        message_out = str('OpacityTT:{}'.format(opacity_target_trap))
        unity_socket_pub.send_string(message_out)
        previous_opacity_target_trap = opacity_target_trap

    if previous_opacity_cue != opacity_cue:
        message_out = str('OpacityCue:{}'.format(opacity_cue))
        unity_socket_pub.send_string(message_out)
        previous_opacity_cue = opacity_cue

    # Message in updates
    if 'OpacityTT' in message_in:
        opacity = float(message_in.split('=')[1])
        message_out = str('OpacityTT:{}'.format(opacity))
        unity_socket_pub.send_string(message_out)

    if 'OpacityCue' in message_in:
        opacity = float(message_in.split('=')[1])
        message_out = str('OpacityCue:{}'.format(opacity))
        unity_socket_pub.send_string(message_out)

    if 'Cue' in message_in or 'Manipulandum' in message_in or 'Target' in message_in or 'Trap' in message_in:
        message_out = 'Coordinates:{}'.format(message_in)
        # if message_out != previous_message:
        # print('------------ SCREENS = {}'.format(message_out))
        previous_message = message_out
        unity_socket_pub.send_string(message_out)

    savenodestate_update_substate_df(message_to_Unity=message_out)


def on_end_of_life():
    global unity_process
    global unity_socket_pub

    try:
        unity_process.kill()
        unity_socket_pub.close(linger=1)
    except:
        pass


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=work_function,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()
