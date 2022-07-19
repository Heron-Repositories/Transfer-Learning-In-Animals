
import numpy as np
import copy


class MTT:

    def __init__(self, _min_distance_to_target, _max_distance_to_target,
                 _target_offsets, _trap_offsets,
                 _dt, _man_speed, _must_lift_at_target, up_or_down):

        self.min_distance_to_target = _min_distance_to_target
        self.max_distance_to_target = _max_distance_to_target
        self.target_offsets = _target_offsets
        self.trap_offsets = _trap_offsets
        self.dt = _dt
        self.man_speed = _man_speed
        self.must_lift_at_target = _must_lift_at_target
        self.positions_of_visuals = np.empty(3)
        self.up_or_down = up_or_down

        manipulandum, target, trap = self.initialise_trial()

        self.positions_of_visuals = np.array([manipulandum, target, trap])
        self.initial_positions_of_visuals = copy.copy(self.positions_of_visuals)
        self.angle_dif_between_man_and_target_trap = 8

    '''
    def initialise_trial_with_variable_target_trap(self):

        manipulandum = np.random.randint(360 - 80, 360 - 9)

        if self.up_or_down:
            target = np.random.randint(manipulandum + self.min_distance_to_target + 11,
                                       np.min([manipulandum + self.max_distance_to_target + 12, 0]))
            trap = np.random.randint(360 - 90, manipulandum - 9)
        else:
            trap = np.random.randint(manipulandum + 11, 360)
            target = np.random.randint(np.max([manipulandum - self.max_distance_to_target - 10, 360 - 90]),
                                       manipulandum - self.min_distance_to_target - 9)

        return manipulandum, target, trap
    '''

    def offset_target_trap(self, target, trap):

        def create_random_offset(limits):
            try_again = True
            limits = np.array(limits)
            if limits.shape[0] > 2:
                limits = limits.reshape((2, int(len(limits) / 2)))
            else:
                limits = np.expand_dims(limits, axis=0)
            while try_again:
                random_theta = np.random.randint(-180, 180)
                for limit in limits:
                    if random_theta >= limit[0] and random_theta <= limit[1]:
                        try_again = False

            return random_theta

        target_offset = create_random_offset(self.target_offsets)
        target = target + target_offset
        # The following if locks the trap to the target if the offsets for the trap in the parameters are set to -181, 181
        if self.trap_offsets[0] == -181 and self.trap_offsets[1] == 181:
            trap_offset = target_offset
        else:
            trap_offset = create_random_offset(self.trap_offsets)
        trap = trap + trap_offset

        print('Offsets = {}, {}'.format(target_offset, trap_offset))

        return target, trap

    def initialise_trial(self):

        def adjust(pos):
            if pos < 0:
                return pos + 360
            if pos > 360:
                return pos - 360
            return pos

        if self.up_or_down:
            target, trap = self.offset_target_trap(360, 360-90)
            manipulandum = np.random.randint(np.max([target - self.max_distance_to_target, trap - 3]),
                                             target - np.max([self.min_distance_to_target, 3]))
        else:
            target, trap = self.offset_target_trap(360 - 90, 360)

            manipulandum = np.random.randint(target + np.max([self.min_distance_to_target, 3]),
                                             np.min([target + self.max_distance_to_target, trap - 3]))

        manipulandum = adjust(manipulandum)
        target = adjust(target)
        trap = adjust(trap)

        d_temp = {1: 'Left', 0: 'Right'}
        print('Trial type = {}'.format(d_temp[self.up_or_down]))
        return manipulandum, target, trap

    def calculate_positions_for_auto_movement(self, current_time, total_time):
        time_steps_required = (total_time - current_time) / self.dt
        position_change_required = self.initial_positions_of_visuals[1] - self.positions_of_visuals[0]

        if time_steps_required > 0:
            position_step = position_change_required / time_steps_required

            self.positions_of_visuals[0] = self.positions_of_visuals[0] + position_step

        return self.positions_of_visuals

    def calculate_positions_for_levers_movement(self, levers_pressed_time):
        if np.abs(levers_pressed_time) > 0:
            self.positions_of_visuals[0] = self.initial_positions_of_visuals[0] + \
                                           self.man_speed * levers_pressed_time/1000

        if levers_pressed_time == 0:
            self.positions_of_visuals[0] = self.initial_positions_of_visuals[0]

        if self.positions_of_visuals[0] > 360 or self.positions_of_visuals[0] < 0:
            self.positions_of_visuals[0] = self.positions_of_visuals[0] % 360

        if not self.must_lift_at_target:
            if self.has_man_reached_target():
                self.positions_of_visuals[0] = self.positions_of_visuals[1]
            elif self.has_man_reached_trap():
                self.positions_of_visuals[0] = self.positions_of_visuals[2]

        #print(levers_pressed_time, self.positions_of_visuals)
        return self.positions_of_visuals

    def has_man_reached_target(self):
        man_pos = self.positions_of_visuals[0]
        target_pos = self.positions_of_visuals[1]
        if np.abs(target_pos - man_pos) < self.angle_dif_between_man_and_target_trap \
                or np.abs(target_pos - man_pos) > 360 - self.angle_dif_between_man_and_target_trap:
            return True
        else:
            return False

    def has_man_reached_trap(self):
        man_pos = self.positions_of_visuals[0]
        trap_pos = self.positions_of_visuals[2]
        if np.abs(trap_pos - man_pos) < self.angle_dif_between_man_and_target_trap \
                or np.abs(trap_pos - man_pos) > 360 - self.angle_dif_between_man_and_target_trap:
            return True
        else:
            return False

    def back_to_initial_positions(self):
        self.positions_of_visuals = copy.copy(self.initial_positions_of_visuals)


