#!/usr/bin/python3 -u
#
# Copyright 2021 Max Kellermann <max.kellermann@gmail.com>,
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import sys
import asyncio
import aionotify
import evdev
import errno
import RPi.GPIO as GPIO

sys.path.append("/etc/pidooria")
import config

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class Switch:
    def __init__(self, pin):
        self.__pin = pin
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

    async def press(self):
        GPIO.output(self.__pin, 1)
        await asyncio.sleep(0.2)
        GPIO.output(self.__pin, 0)

switches = {}

def make_switch(pin):
    global switches
    if pin not in switches:
        switches[pin] = Switch(pin)
    return switches[pin]

inputs = {
    name: make_switch(pin) for name, pin in config.inputs.items()
}

active_devices = set()

async def handle_input_device(device, switch):
    global active_devices
    try:
        async for event in device.async_read_loop():
            if event.type == evdev.ecodes.EV_KEY and event.value == evdev.KeyEvent.key_down:
                print(f"Got keypress from {device.uniq} ('{device.name}')")
                await switch.press()
    except OSError as e:
        if e.errno == errno.ENODEV:
            print(f"remove input device {device.path} '{device.name}'")
            return
        raise
    finally:
        active_devices.remove(device.path)

def scan_input_devices():
    global active_devices
    for path in evdev.list_devices():
        if path in active_devices: continue
        try:
            device = evdev.InputDevice(path)
        except OSError as e:
            print(f"Failed to open {path}: {e}")
            continue
        if device.name in inputs:
            print(f"add input device {device.path} '{device.name}'")
            active_devices.add(device.path)
            asyncio.ensure_future(handle_input_device(device, inputs[device.name]))

# inotify in /dev/input detects newly connected devices
watcher = aionotify.Watcher()
watcher.watch(alias='input', path='/dev/input', flags=aionotify.Flags.CREATE)

scan_input_devices()

loop = asyncio.get_event_loop()

async def watch_input(loop, watcher):
    await watcher.setup(loop)
    while True:
        event = await watcher.get_event()
        scan_input_devices()

asyncio.ensure_future(watch_input(loop, watcher))
loop.run_forever()
