
import numpy as np
from statemachine import StateMachine, State


class LeversStateMachine(StateMachine):

    # States
    no_poke_no_levers = State("NP_NL", initial=True)
    no_poke_levers = State("NP_L")
    poke_no_levers = State("P_NL")
    no_poke_no_levers_grace = State("NP_NL_G")
    no_poke_levers_grace = State("NP_L_G")
    poke_levers = State("P_L")

    # Transitions
    _0 = no_poke_no_levers.to(no_poke_no_levers)
    _1 = no_poke_no_levers.to(no_poke_levers)
    _2 = no_poke_levers.to(no_poke_no_levers)
    _3 = no_poke_no_levers.to(poke_no_levers)
    _4 = no_poke_no_levers.to(poke_levers)
    _5 = no_poke_levers.to(poke_levers)
    _6 = no_poke_levers.to(no_poke_levers)
    _7 = poke_no_levers.to(poke_no_levers)
    _8 = poke_levers.to(poke_levers)
    _9 = poke_no_levers.to(poke_levers)
    _10 = poke_levers.to(poke_no_levers)
    _11 = poke_no_levers.to(no_poke_levers_grace)
    _12 = no_poke_levers_grace.to(poke_no_levers)
    _13 = poke_no_levers.to(no_poke_no_levers_grace)
    _14 = no_poke_no_levers_grace.to(poke_no_levers)
    _15 = poke_levers.to(no_poke_levers_grace)
    _16 = no_poke_levers_grace.to(poke_levers)
    _17 = no_poke_levers_grace.to(no_poke_levers_grace)
    _18 = no_poke_levers_grace.to(no_poke_no_levers_grace)
    _19 = no_poke_no_levers_grace.to(no_poke_levers_grace)
    _20 = poke_levers.to(no_poke_levers_grace)
    _21 = no_poke_no_levers_grace.to(poke_levers)
    _22 = no_poke_no_levers_grace.to(no_poke_no_levers_grace)
    _23 = no_poke_no_levers_grace.to(no_poke_no_levers)
    _24 = no_poke_levers.to(poke_no_levers)

    def __init__(self, _grace_threshold=60):
        super().__init__(StateMachine)
        self.lever_press_time = 0
        self.poke = 0
        self.grace_time = 0
        self.grace_threshold = _grace_threshold

        self.lever_pressed = 0  # Set to -1 for left +1 for right

    def do_transition(self, poke, pressed_left, pressed_right):

        def set_pressed():
            if pressed_right == 0:
                self.lever_pressed = pressed_left
            else:
                self.lever_pressed = pressed_right

        pressed = pressed_left + pressed_right
        if self.current_state == self.no_poke_no_levers:
            if poke and pressed == 0:
                self._3()
            elif not poke and pressed == 0:
                self._0()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._4()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._1()

        elif self.current_state == self.no_poke_levers:
            if poke and pressed == 0:
                self._24()
            elif not poke and pressed == 0:
                self._2()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._5()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._6()

        elif self.current_state == self.poke_no_levers:
            if poke and pressed == 0:
                self._7()
            elif not poke and pressed == 0:
                self._13()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._9()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._11()

        elif self.current_state == self.poke_levers:
            if poke and pressed == 0:
                self._10()
            elif not poke and pressed == 0:
                self._20()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._8()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._15()

        elif self.current_state == self.no_poke_levers_grace:
            if poke and pressed == 0:
                self._12()
            elif not poke and pressed == 0:
                self._18()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._16()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._17()

        elif self.current_state == self.no_poke_no_levers_grace:
            if poke and pressed == 0:
                self._14()
            elif not poke and pressed == 0:
                self._22()
                if self.grace_time >= self.grace_threshold:
                    self._23()
            elif poke and np.abs(pressed) > 0:
                set_pressed()
                self._21()
            elif not poke and np.abs(pressed) > 0:
                set_pressed()
                self._19()

    def on__0(self):
        self.poke = 0

    def on__1(self):
        self.poke = 0

    def on__2(self):
        self.poke = 0

    def on__3(self):
        self.lever_press_time = 0
        self.poke = 1

    def on__4(self):
        self.lever_press_time = 0
        self.poke = 1

    def on__5(self):
        self.lever_press_time += self.lever_pressed
        self.grace_time = 0
        self.poke = 1

    def on__6(self):
        self.poke = 0

    def on__7(self):
        self.grace_time = 0
        self.poke = 1

    def on__8(self):
        self.lever_press_time += self.lever_pressed
        self.grace_time = 0
        self.poke = 1

    def on__9(self):
        self.lever_press_time += self.lever_pressed
        self.poke = 1

    def on__10(self):
        self.poke = 1

    def on__11(self):
        self.lever_press_time += self.lever_pressed
        self.poke = 1

    def on__12(self):
        self.grace_time = 0
        self.poke = 1

    def on__13(self):
        self.poke = 1

    def on__14(self):
        self.grace_time = 0
        self.poke = 1

    def on__15(self):
        self.poke = 1

    def on__16(self):
        self.grace_time = 0
        self.lever_press_time += self.lever_pressed
        self.poke = 1

    # In the next 3 transitions making the grace_time bigger than the grace_threshold does not terminate the trial
    def on__17(self):
        self.grace_time += 1
        self.poke = 1

    def on__18(self):
        self.grace_time += 1
        self.poke = 1

    def on__19(self):
        self.grace_time += 1
        self.poke = 1

    def on__20(self):
        self.grace_time = 0
        self.poke = 1

    def on__21(self):
        self.grace_time += 1
        self.poke = 1

    def on__22(self):
        self.grace_time += 1
        self.poke = 1

    def on__23(self):
        self.grace_time = 0
        self.poke = 0
        self.lever_press_time = 0

    def on__24(self):
        self.poke = 1
        self.lever_press_time = 0

