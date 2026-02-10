from enum import IntEnum, auto

class BookingState(IntEnum):
    START = auto()
    CLIENT_SELECT = auto()
    MASTER_SELECT = auto()
    DATE_SELECT = auto()
    TIME_SELECT = auto()
    CONFIRM = auto()

class ClientState(IntEnum):
    NAME = auto()
    PHONE = auto()
    NOTES = auto()
