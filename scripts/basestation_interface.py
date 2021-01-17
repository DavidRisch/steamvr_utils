import enum
import time

# sudo apt install pip3 libglib2.0-dev
# sudo pip3 install bluepy
import bluepy

import log


# based on: https://gist.github.com/waylonflinn/d525e08674ec3abb5c98cd41d1fd2f24


class BasestationPowerInterface:
    class Action(enum.Enum):
        ON = enum.auto()
        OFF = enum.auto()
        TOGGLE = enum.auto()

    def __init__(self, config):
        self.config = config

        self.devices = []

    def scan(self):
        class Delegate(bluepy.btle.DefaultDelegate):

            def __init__(self):
                self.devices = []
                bluepy.btle.DefaultDelegate.__init__(self)

            def handleDiscovery(self, dev, is_new_dev, is_new_data):
                if not is_new_dev:
                    return

                manufacturer = dev.getValue(bluepy.btle.ScanEntry.MANUFACTURER)

                if manufacturer is not None and manufacturer[0:4] == b'\x5d\x05\x00\x02':
                    log.i('Found Base Station {} at address {}'.format(
                        dev.getValue(bluepy.btle.ScanEntry.COMPLETE_LOCAL_NAME),
                        dev.addr))
                    self.devices.append(dev.addr)

        self.devices = []
        scanner = bluepy.btle.Scanner()
        delegate = Delegate()
        scanner.withDelegate(delegate)
        try:
            scanner.scan(2)
        except bluepy.btle.BTLEManagementError as e:
            log.e(e)
            if 'code: 20, error: Permission Denied' in str(e):
                raise RuntimeError('''
Missing Permissions for Bluetooth. Two options:
- Run this script as root (with sudo)
- Or give bluepy the necessary capabilities (afterwards this script can be run as a normal user):
    sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.?/dist-packages/bluepy/bluepy-helper
    or (depending on how you installed bluepy)
    sudo setcap 'cap_net_raw,cap_net_admin+eip' /home/$USER/.local/lib/python3.?/site-packages/bluepy/bluepy-helper
    see: https://github.com/IanHarvey/bluepy/issues/313#issuecomment-428324639
                    ''')
            else:
                raise e

        self.devices = delegate.devices
        if len(self.devices) == 0:
            raise RuntimeError('Bluetooth scan found no Base Stations. '
                               'If there are powered Base Stations near you, '
                               'this is probably a problem with your Bluetooth device.')

    def action(self, action):
        address = 0x12  # location of the byte which sets the power state

        for device in self.devices:
            basestation = bluepy.btle.Peripheral()
            log.i('Connecting to {}'.format(device))
            basestation.connect(device, addrType=bluepy.btle.ADDR_TYPE_RANDOM)

            if action == self.Action.TOGGLE:
                # only the state of the first base station is used to determine the target state
                current_state = basestation.readCharacteristic(address)
                if current_state == b'\x00':  # currently turned off
                    action = self.Action.ON
                    log.i('Currently turned off')
                else:
                    action = self.Action.OFF
                    log.i('Currently turned on')

            if action == self.Action.ON:
                if not self.config.dry_run():
                    basestation.writeCharacteristic(address, b'\x01')
                else:
                    log.w('Skipping because of dry run:')
                log.i('Turning on')
            elif action == self.Action.OFF:
                if not self.config.dry_run():
                    basestation.writeCharacteristic(address, b'\x00')
                else:
                    log.w('Skipping because of dry run:')
                log.i('Turning off')

            basestation.disconnect()

    def robust_action(self, action):
        def attempt_loop(function, max_attempts, try_all=False):
            attempt_count = 0
            success_count = 0
            last_error = None
            while attempt_count < max_attempts:
                try:
                    if try_all:
                        function()
                    else:
                        return function()
                    success_count += 1
                    log.i('Success of attempt {} of {}'.format(attempt_count + 1, max_attempts))
                except Exception as e:
                    last_error = e
                    log.e('Failure of attempt {} of {}: {}'.format(attempt_count + 1, max_attempts, e))
                attempt_count += 1

                time.sleep(0.5)  # to increase robustness

            if success_count == 0:
                log.e('No successful attempt in any of the {} attempts. Last error:'.format(max_attempts))
                raise last_error

        log.i("Scanning for Base Stations:")
        attempt_loop(lambda: self.scan(), self.config.basestation_attempt_count_scan())
        log.i("Changing power state of Base Stations:")
        attempt_loop(lambda: self.action(action), self.config.basestation_attempt_count_set(), try_all=True)
