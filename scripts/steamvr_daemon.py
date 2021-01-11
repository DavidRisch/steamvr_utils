import enum
import os
import subprocess
import sys
import threading
import time

import log


class SteamvrDaemon:
    class Stages(enum.Enum):
        STARTUP = enum.auto
        BEFORE_STEAMVR = enum.auto()
        DURING_STEAMVR = enum.auto()
        AFTER_STEAMVR = enum.auto()

    def __init__(self, steamvr_utils):
        self.steamvr_utils = steamvr_utils
        self.config = steamvr_utils.config

        self.current_stage = self.Stages.STARTUP
        self.start_of_current_stage = time.time()

    def update_stage(self, new_stage):
        log.i('SteamvrDaemon changed state to: {}'.format(new_stage.name))
        self.current_stage = new_stage
        self.start_of_current_stage = time.time()

    @classmethod
    def create_daemon(cls, steamvr_utils):
        # kill other instances of this deamon to make sure only one is running at any given time
        subprocess.run(['killall', 'steamvr_utils.py d'])

        # based on: https://code.activestate.com/recipes/278731-creating-a-daemon-the-python-way/
        pid = os.fork()
        if pid == 0:
            # First Child
            pid = os.fork()
            if pid == 0:
                # Second Child
                os.chdir('/')
                steamvr_daemon = cls(steamvr_utils)
                steamvr_daemon.loop()
                sys.exit()
            else:
                # First Child
                sys.exit()
        else:
            # Parent
            log.i('Logging to stdout will now stop. See log file at: {}'.format(steamvr_utils.config.log_path()))
            sys.exit()

    def loop(self):
        if self.current_stage == self.Stages.STARTUP:
            self.steamvr_utils.turn_on()

            self.current_stage = self.Stages.BEFORE_STEAMVR

        continue_running = self.check()

        if self.current_stage == self.Stages.DURING_STEAMVR:
            self.steamvr_utils.turn_on_iteration()

        if continue_running:
            interval = 1
            threading.Timer(interval, self.loop).start()

    def check(self):
        steamvr_running = self.is_steamvr_running()

        # log.d('Stage: {}   steamvr_running {}'.format(self.current_stage, steamvr_running))

        if self.current_stage == self.Stages.BEFORE_STEAMVR:
            if steamvr_running:
                self.update_stage(self.Stages.DURING_STEAMVR)
            elif self.start_of_current_stage + 60 <= time.time():
                log.e("SteamVR never started, exiting. Looking for a process with this name: {}".format(
                    self.config.daemon_watch_process_name()))
                self.steamvr_utils.turn_off()
                log.i("Exiting...")
                return False

        elif self.current_stage == self.Stages.DURING_STEAMVR:
            if not steamvr_running:
                self.update_stage(self.Stages.AFTER_STEAMVR)

        elif self.current_stage == self.Stages.AFTER_STEAMVR:
            if steamvr_running:
                self.update_stage(self.Stages.DURING_STEAMVR)
            elif self.start_of_current_stage + self.config.daemon_wait_after_quit() <= time.time():
                self.steamvr_utils.turn_off()
                log.i("Exiting...")
                return False

        return True

    def is_steamvr_running(self):
        process = subprocess.run(['ps', '-C', self.config.daemon_watch_process_name()], capture_output=True)
        state = process.returncode == 0
        return state
