import numpy as np
from statemachine import StateMachine, State
from Heron import constants as ct


class StateMachine(StateMachine):

    DEBUG = False

    command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
    command_to_food_poke = np.array([ct.IGNORE])

    constant_to_update_poke_without_starting_trial = -1

    # States
    initial = State("Init", initial=True)
    no_avail_touch = State("NA_T")
    no_avail_no_touch = State('NA_NT')
    success = State("S")
    failure = State("F")
    availability = State("A")

    # Transitions
    _1_wait_to_start = initial.to(initial)
    _2_button_first_pressed = initial.to(no_avail_touch)
    _3_button_kept_pressed = no_avail_touch.to(no_avail_touch)
    _4_button_stopped_pressed = no_avail_touch.to(no_avail_no_touch)
    _5_grace_period = no_avail_no_touch.to(no_avail_no_touch)
    _6_button_represssed_in_grace_period = no_avail_no_touch.to(no_avail_touch)
    _7_out_of_target = no_avail_no_touch.to(failure)
    _8_in_target = no_avail_no_touch.to(success)
    _9_punish_period = failure.to(failure)
    _10_availability_on = success.to(availability)
    _11_init_from_fail = failure.to(initial)
    _12_availability_period = availability.to(availability)
    _13_init_from_success = availability.to(initial)

    def __init__(self, _dt, _grace_to_succeed_period, _grace_to_fail_period, _punish_period, _man_target):
        super().__init__(StateMachine)
        self.dt = _dt
        self.grace_to_succeed_timer = 0
        self.grace_to_fail_timer = 0
        self.punish_counter = 0
        self.availability_wait_counter = 0
        self.grace_to_succeed_period = _grace_to_succeed_period
        self.grace_to_fail_period = _grace_to_fail_period
        self.punish_period = _punish_period
        self. availability_wait_period = 6
        self.man_target = _man_target
        self.record = np.array([0, 0])
        self.number_of_pellets = 1
        self.lever_press_time = 0
        self.start_trial_lever_press_time = 0

    def on__1_wait_to_start(self):
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])
        if self.DEBUG:
            print('1 waiting to start')

    def on__2_button_first_pressed(self):
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])
        if self.DEBUG:
            print('2 button 1st pressed')

    def on__3_button_kept_pressed(self):
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])

    def on__4_button_stopped_pressed(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([ct.IGNORE])
        if self.DEBUG:
            print('4 button stopped pressed')

    def on__5_grace_period(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([ct.IGNORE])

    def on__6_button_represssed_in_grace_period(self):
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])

        self.grace_to_succeed_timer = 0
        self.grace_to_fail_timer = 0
        if self.DEBUG:
            print('6 button repressed')

    def on__7_out_of_target(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([ct.IGNORE])
        self.record[1] = self.record[1] + 1
        self.grace_to_succeed_timer = 0
        self.grace_to_fail_timer = 0
        if self.DEBUG:
            print('7 out of target')

    def on__8_in_target(self):
        self.command_to_screens = np.array(['Cue=1, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([self.number_of_pellets])
        self.record[0] = self.record[0] + 1
        self.grace_to_succeed_timer = 0
        self.grace_to_fail_timer = 0
        if self.DEBUG:
            print('8 in target')

    def on__9_punish_period(self):
        self.command_to_screens = np.array(['Cue=0, Manipulandum=0, Target=0, Trap=0'])
        self.command_to_food_poke = np.array([ct.IGNORE])
        self.punish_counter += 1

    def on__10_availability_on(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])
        if self.DEBUG:
            print('10 availability on')

    def on__11_init_from_fail(self):
        self.man_target.lever_press_time_from_end_of_last_trial = self.lever_press_time
        self.man_target.initialise_trial()
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])
        self.punish_counter = 0
        if self.DEBUG:
            print('11 init from fail')

    def on__12_availability_period(self):
        self.command_to_screens = np.array([ct.IGNORE])
        self.command_to_food_poke = np.array([self.constant_to_update_poke_without_starting_trial])

    def on__13_init_from_success(self):
        self.man_target.lever_press_time_from_end_of_last_trial = self.lever_press_time
        self.man_target.initialise_trial()
        self.command_to_screens = np.array(
            ['Cue=0, Manipulandum={}, Target={}, Trap=0'.
                 format(self.man_target.positions_of_visuals[0], self.man_target.positions_of_visuals[1])])
        self.command_to_food_poke = np.array([ct.IGNORE])
        if self.DEBUG:
            print('13 init from success')

    def do_transition(self, _availability, _touching, _lever_press_time, _number_of_pellets,
                      _punishment_delay, _target_grace_period, _fail_grace_period):

        availability = _availability
        touching = _touching
        self.lever_press_time = _lever_press_time
        self.number_of_pellets = _number_of_pellets
        self.punish_period = _punishment_delay
        self.grace_to_succeed_period = _target_grace_period
        self.grace_to_fail_period = _fail_grace_period

        if not availability and not touching:
            self.start_trial_lever_press_time = self.lever_press_time

            if self.current_state == self.initial:
                self._1_wait_to_start()

            elif self.current_state == self.no_avail_touch:
                self._4_button_stopped_pressed()

            elif self.current_state == self.no_avail_no_touch:
                if self.man_target.has_man_reached_target():
                    self.grace_to_succeed_timer += 1
                    if self.grace_to_succeed_timer > self.grace_to_succeed_period:
                        self._8_in_target()
                    else:
                        self._5_grace_period()
                else:
                    self.grace_to_fail_timer += 1
                    if self.grace_to_fail_timer > self.grace_to_fail_period:
                        self._7_out_of_target()
                    else:
                        self._5_grace_period()

            elif self.current_state == self.success:
                self._10_availability_on()

            elif self.current_state == self.failure:
                if self.punish_counter > self.punish_period:
                    self._11_init_from_fail()
                else:
                    self._9_punish_period()

            elif self.current_state == self.availability:
                self.availability_wait_counter += 1
                if self.availability_wait_counter > self.availability_wait_period:
                    self.availability_wait_counter = 0
                    self._13_init_from_success()

        elif not availability and touching:
            self.man_target.calculate_positions_for_levers_movement(self.lever_press_time)

            if self.current_state == self.initial:
                self._2_button_first_pressed()

            elif self.current_state == self.no_avail_touch:
                self._3_button_kept_pressed()

            elif self.current_state == self.no_avail_no_touch:
                self._6_button_represssed_in_grace_period()

            elif self.current_state == self.success:
                self._10_availability_on()

            elif self.current_state == self.failure:
                if self.punish_counter > self.punish_period:
                    self._11_init_from_fail()
                else:
                    self._9_punish_period()

            elif self.current_state == self.availability:
                self.availability_wait_counter += 1
                if self.availability_wait_counter > self.availability_wait_period:
                    self.availability_wait_counter = 0
                    self._13_init_from_success()

        elif availability:
            if not touching:
                self.start_trial_lever_press_time = self.lever_press_time

            if self.current_state == self.success:
                self._10_availability_on()

            elif self.current_state == self.availability:
                self._12_availability_period()

            elif self.current_state == self.initial:
                self._1_wait_to_start()
