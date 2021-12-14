# the GPIO pins of a RPi Relay Board:
RPI_RELAY_BOARD = (26, 20, 21)

DOOR = RPI_RELAY_BOARD[0]
GARAGE = RPI_RELAY_BOARD[1]

inputs = {
    'AB Shutter 3 Keyboard': DOOR,
    'AB Shutter 3 Consumer Control': GARAGE,
}

