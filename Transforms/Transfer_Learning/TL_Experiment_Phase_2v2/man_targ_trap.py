
import numpy as np
import copy


class MTT:

    def __init__(self, _variable_targets, _min_distance_to_target, _max_distance_to_target,
                 _dt, _man_speed, _must_lift_at_target, up_or_down):
        self.variable_targets = _variable_targets
        self.min_distance_to_target = _min_distance_to_target
        self.max_distance_to_target = _max_distance_to_target
        self.dt = _dt
        self.man_speed = _man_speed
        self.must_lift_at_target = _must_lift_at_target
        self.positions_of_visuals = np.empty(3)
        self.up_or_down = up_or_down

        if self.variable_targets:
            manipulandum, target, trap = self.initialise_trial_with_variable_target_trap()
        else:
            manipulandum, target, trap = self.initialise_trial_with_constant_target_trap()

        self.positions_of_visuals = np.array([manipulandum, target, trap])
        self.initial_positions_of_visuals = copy.copy(self.positions_of_visuals)

        self.angle_dif_between_man_and_target_trap = 5

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

    def initialise_trial_with_constant_target_trap(self):

        if self.up_or_down:
            target = 360
            trap = 360 - 90

            manipulandum = np.random.randint(np.max([target - self.max_distance_to_target, trap - 3]),
                                             target - np.max([self.min_distance_to_target, 3]))
        else:
            target = 360 - 90
            trap = 360

            manipulandum = np.random.randint(target + np.max([self.min_distance_to_target, 3]),
                                             np.min([target + self.max_distance_to_target, trap - 3]))

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
        #print(levers_pressed_time, self.positions_of_visuals[0])
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


