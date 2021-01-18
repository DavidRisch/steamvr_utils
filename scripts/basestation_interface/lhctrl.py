# MIT License
#
# Copyright (c) 2019 risa2000
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# https://github.com/risa2000/lhctrl/tree/03a49e0687982efd488da561e47eaa90840e6102

"""
Valve v1 lighthouse power management over BT LE
"""

# external libs
from bluepy import btle

# standard imports
import signal
import sys
import time
from struct import pack
from functools import partial

#   globals
#-------------------------------------------------------------------------------
# wake-up command header
CMD_HDR1 = 0x12
CMD_HDR2 = 0x02
# wake-up command tail
CMD_TAIL = bytes.fromhex('000000000000000000000000')
# Characteristic handle
HCHAR = 0x35
# return error code
EXIT_OK = 0
EXIT_ERR = -1
# ping to LH timeout factor
TO_FACTOR = 0.75
# verbosity level INFO
INFO   = 1

#   defaults
#-------------------------------------------------------------------------------
LH_TIMEOUT      = 60
PING_SLEEP      = LH_TIMEOUT / 3
TRY_COUNT       = 5
TRY_PAUSE       = 2
GLOBAL_TIMEOUT  = 0

#   functions
#-------------------------------------------------------------------------------
def makeUpCmd(lh_id, off_timeout, cmd2=None):
    """create LH wake-up command."""
    # need to convert off timeout to big endian
    hdr1 = CMD_HDR1.to_bytes(1, 'little')
    if cmd2 is None:
        hdr2 = CMD_HDR2.to_bytes(1, 'little')
    else:
        hdr2 = cmd2.to_bytes(1, 'little')
    b_ot = off_timeout.to_bytes(2, 'big')
    b_id = lh_id.to_bytes(4, 'little')
    return pack('ss2s4s12s', hdr1, hdr2, b_ot, b_id, CMD_TAIL)

def argsCheck(args):
    """Sanity check for command line arguments."""
    if args.lh_b_id and not args.lh_b_mac:
        print('Scanning not implemented. MAC of "B" LH (option "--lh_b_mac") has to be specified.')
        sys.exit(EXIT_ERR)
    if args.lh_c_id and not args.lh_c_mac:
        print('Scanning not implemented. MAC of "C" LH (option "--lh_c_mac") has to be specified.')
        sys.exit(EXIT_ERR)
    if (args.ping_sleep and args.lh_timeout) and (args.ping_sleep >= TO_FACTOR * args.lh_timeout):
        print('Ping sleep should be at max {:2f} of LH timeout'.format(TO_FACTOR))
        sys.exit(EXIT_ERR)

def argsProcess(args):
    if args.lh_b_id:
        args.lh_b_id_int = int(args.lh_b_id, 16)
    if args.lh_c_id:
        args.lh_c_id_int = int(args.lh_c_id, 16)

def writeCmd(lh, hndl, cmd, verb=0):
    """Send write command and log to stdout if requested."""
    if (verb >= INFO):
        print('Writing char-cs to 0x{:x} : {:s} -> '.format(hndl, cmd.hex()), end='')
    res = lh.writeCharacteristic(hndl, cmd)
    if (verb >= INFO):
        print(res)
    return res

def readCmd(lh, hndl, verb=0):
    """Send read command and log to stdout if requested."""
    if (verb >= INFO):
        print('Reading char-cs from 0x{:x} -> '.format(hndl), end='')
    res = lh.readCharacteristic(hndl)
    if (verb >= INFO):
        print(res.hex())
    return res

def writeReadCmd(lh, hndl, cmd, verb=0):
    """Write data and read the same characterstic after."""
    res = writeCmd(lh, hndl, cmd, verb)
    return res, readCmd(lh, hndl, verb)

def connect(lh, mac, try_count, try_pause, verb=0, interface=0):
    """Connect to LH, try it `try_count` times."""
    while True:
        try:
            if (verb >= INFO):
                print('Connecting to {:s} at {:s} -> '.format(mac, time.asctime()), end='')
            lh.connect(mac, iface=interface)
            if (verb >= INFO):
                print(lh.getState())
            break
        except btle.BTLEDisconnectError as e:
            if try_count <= 1:
                raise e
            if (verb >= INFO):
                print(e)
            try_count -= 1
            time.sleep(try_pause)
            continue
        except:
            raise

def disconnect(lh, verb=0):
    if (verb >= INFO):
        print('Diconnecting at {:s}'.format(time.asctime()))
    lh.disconnect()

def wait(psleep, verb=0):
    if (verb >= INFO):
        print('Sleeping for {:.2f} sec ... '.format(psleep), end='', flush=True)
    time.sleep(psleep)
    if (verb >= INFO):
        print('Done!', flush=True)

def hndl_io(mac, hndl, cmd, try_count, try_pause, verb, interface):
    """Write `cmd` command to the `hndl` characteristics and read the reply to/from
    BTLE device with `mac` MAC address."""
    lh = btle.Peripheral()
    connect(lh, mac, try_count, try_pause, verb, interface)
    resw, resr = writeReadCmd(lh, hndl, cmd, verb)
    disconnect(lh, verb=args.verbose)
    return resw, resr

def loop(args):
    """Run the whole loop."""
    ping_b = makeUpCmd(args.lh_b_id_int, args.lh_timeout, args.cmd2)
    if args.lh_c_id:
        ping_c = makeUpCmd(args.lh_c_id_int, args.lh_timeout, args.cmd2)

    start = time.monotonic()

    if args.verbose >= INFO:
        print('Booting up "B" lighthouse')
        if args.lh_c_id:
            print('Booting up "C" lighthouse')
    try:
        while True:
            hndl_io(args.lh_b_mac, args.hndl, ping_b, args.try_count, args.try_pause, args.verbose, args.interface)
            if args.lh_c_id:
                hndl_io(args.lh_c_mac, args.hndl, ping_c, args.try_count, args.try_pause, args.verbose, args.interface)
            wait(args.ping_sleep, verb=args.verbose)
            now = time.monotonic()
            if args.global_timeout and (now - start > args.global_timeout):
                break
    except KeyboardInterrupt:
        print()
        print('Keyboard interrupt caught')
        pass

def shutdown(args):
    """Shut down the lighthouses."""
    if args.verbose >= INFO:
        print('Shutting down "B" lighthouse')
    upCmd = makeUpCmd(args.lh_b_id_int, 1, args.cmd2)
    hndl_io(args.lh_b_mac, args.hndl, upCmd, args.try_count, args.try_pause, args.verbose, args.interface)

    if args.lh_c_id:
        if args.verbose >= INFO:
            print('Shutting down "C" lighthouse')
        upCmd = makeUpCmd(args.lh_c_id_int, 1, args.cmd2)
        hndl_io(args.lh_c_mac, args.hndl, upCmd, args.try_count, args.try_pause, args.verbose, args.interface)

def sigterm_hndlr(args, sigterm_def, signum, frame):
    """Signal wrapper for the shutdown function."""
    if args.verbose >= INFO:
        print()
        print(f'Signal {repr(signum)} caught.')
    shutdown(args)
    if sigterm_def != signal.SIG_DFL:
        sigterm_def(signum, frame)
    else:
        sys.exit(EXIT_OK)

def main(args):
    """Main runner."""
    signal.signal(signal.SIGTERM, partial(sigterm_hndlr, args, signal.getsignal(signal.SIGTERM)))
    signal.signal(signal.SIGHUP, partial(sigterm_hndlr, args, signal.getsignal(signal.SIGHUP)))
    loop(args)
    shutdown(args)

#   main
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    from argparse import ArgumentParser

    ap = ArgumentParser(description='Wakes up and runs Vive lighthouse(s) using BT LE power management')
    ap.add_argument('-b', '--lh_b_id', type=str, required=True, help='BinHex ID of the "B" lighthouse (as in LHB-<8_char_id>)')
    ap.add_argument('-c', '--lh_c_id', type=str, help='Hex ID of the "C" lighthouse (as in LHB-<8char_id>)')
    ap.add_argument('--lh_b_mac', type=str, help='BT MAC of the "B" lighthouse (in format aa:bb:cc:dd:ee:ff)')
    ap.add_argument('--lh_c_mac', type=str, help='BT MAC of the "C" lighthouse (in format aa:bb:cc:dd:ee:ff)')
    ap.add_argument('--lh_timeout', type=int, default=LH_TIMEOUT, help='time (sec) in which LH powers off if not pinged [%(default)s]')
    ap.add_argument('--hndl', type=int, default=HCHAR, help='characteristic handle [%(default)s]')
    ap.add_argument('-g', '--global_timeout', type=int, default=GLOBAL_TIMEOUT, help='time (sec) how long to keep the lighthouse(s) alive (0=forever) [%(default)s]')
    ap.add_argument('-i', '--interface', type=int, default=0, help='The Bluetooth interface on which to make the connection to be set. On Linux, 0 means /dev/hci0, 1 means /dev/hci1 and so on.')
    ap.add_argument('-p', '--ping_sleep', type=float, default=PING_SLEEP, help='time (sec) between two consecutive pings [%(default)s]')
    ap.add_argument('--try_count', type=int, default=TRY_COUNT, help='number of tries to set up a connection [%(default)s]')
    ap.add_argument('--try_pause', type=int, default=TRY_PAUSE, help='sleep time when reconnecting [%(default)s]')
    ap.add_argument('--cmd2', type=int, default=CMD_HDR2, help='second byte in the data written to the LH [%(default)s]')
    ap.add_argument('-v', '--verbose', action='count', default=0, help='increase verbosity of the log to stdout')

    args = ap.parse_args()
    argsCheck(args)
    argsProcess(args)
    main(args)
