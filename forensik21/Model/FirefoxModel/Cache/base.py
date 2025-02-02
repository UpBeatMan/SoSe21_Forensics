import pickle
from datetime import datetime, timedelta, timezone
from os.path import exists, isfile, join

EPOCH = datetime(1970, 1, 1)
OTHER = "other"
DT_SEC = "datetime_second"
DT_SEC_DOT_MILLI = "datetime_second_dot_milli"
DT_MILLI = "datetime_milli"
DT_MICRO = "datetime_microseconds"
DT_MILLI_ZEROED_MICRO = "datetime_milliseconds_zeroed_microseconds"
DT_MILLI_OR_ZERO = "datetime_milliseconds_zero"
DT_ZERO = "datetime_always_zero"

MILLI_FACTOR = 1000
MICRO_FACTOR = 1000000

PERSISTENT = "Dauerhaft"


def microseconds_to_datetime(microseconds):
    """
    Creates datetime from microseconds.
    Workaround to datetime.replace does not handle microseconds well
    """
    datetime_obj = EPOCH + timedelta(microseconds=microseconds)
    return datetime_obj


class BaseAttribute:
    """
    Helper class to better handle Attributes
    Transforms timestamp into datetime because it makes handling date and time easier
    """

    def __init__(self, name: str, type_: str, value):
        self.name = name
        self.type = type_
        self.value = value
        self.timestamp = None

        if type_ == DT_SEC:
            self.timestamp = int(value)
            try:
                self.value = datetime.fromtimestamp(0) + timedelta(seconds=self.timestamp)
            except:
                self.value = datetime.fromtimestamp(0) + timedelta(seconds=self.timestamp/1000)
        elif type_ in (DT_MICRO, DT_MILLI_ZEROED_MICRO):
            self.timestamp = int(value)
            self.value = microseconds_to_datetime(self.timestamp)
        elif type_ == DT_MILLI:
            self.timestamp = int(value)
            self.value = microseconds_to_datetime(self.timestamp * MILLI_FACTOR)
        elif type_ == DT_MILLI_OR_ZERO:
            if self.value == 0:
                self.timestamp = 0
                self.value = PERSISTENT
                self.type = DT_ZERO
            else:
                self.timestamp = int(self.value)
                self.value = microseconds_to_datetime(self.timestamp * MILLI_FACTOR)
                self.type = DT_MILLI
        elif type_ == DT_SEC_DOT_MILLI:
            second = int(self.value)
            str_value = str(self.value)

            millisecond = int(str_value.split(".")[1])
            self.timestamp = (second * MILLI_FACTOR) + millisecond
            self.value = microseconds_to_datetime(self.timestamp * MILLI_FACTOR)

    def date_to_timestamp(self):
        """Transforms datetime to timestamps"""
        if self.type == OTHER or self.type == DT_ZERO:
            return

        microseconds = self.value.microsecond
        self.timestamp = int(datetime.timestamp(self.value.replace(tzinfo=timezone.utc)))

        if self.type == DT_MICRO:
            self.timestamp = (self.timestamp * MICRO_FACTOR) + microseconds
        elif self.type == DT_MILLI_ZEROED_MICRO:
            # Zeroing out the last three numbers
            microseconds = int(microseconds / MILLI_FACTOR) * MILLI_FACTOR
            self.timestamp = (self.timestamp * MICRO_FACTOR) + microseconds
        elif self.type == DT_MILLI:
            milliseconds = int(microseconds / MILLI_FACTOR)
            self.timestamp = (self.timestamp * MILLI_FACTOR) + milliseconds
        elif self.type == DT_SEC_DOT_MILLI:
            milliseconds = int(microseconds / MILLI_FACTOR)
            self.timestamp = float(str(self.timestamp) + "." + str(milliseconds))

    def change_date(self, delta):
        """Override value with datetime"""
        if self.type == OTHER:
            return

        if self.timestamp == 0:
            return    

        self.value = datetime.fromtimestamp(self.value.timestamp() - delta)

    def is_other(self):
        """Check if attribute is datetime or other type like string"""
        return self.type == OTHER or self.type == DT_ZERO

    def extended_timestamp(self):
        """Returns microseconds or milliseconds from timestamp"""
        if self.type == DT_MICRO:
            return self.timestamp % MICRO_FACTOR
        if self.type == DT_MILLI:
            return self.timestamp % MILLI_FACTOR

        return None


class BaseCacheClass:
    attr_list = []

    def get_value_list(self):
        list_ = []
        for attr in self.attr_list:
            list_.append(attr.value)

        return list_

    def get_state(self):
        return pickle.dumps(vars(self))

    def set_state(self, memento):
        previous_state = pickle.loads(memento)
        vars(self).clear()
        vars(self).update(previous_state)


class BaseCacheHandler:
    pre_path = ""
    post_path = ""

    caretakers = []

    def __init__(self, root_path: str, file_name: str):
        self.path = join(root_path, file_name)

        if root_path == "":
            raise FileNotFoundError("Kein Pfad angegeben")
        if not exists(self.path):
            raise FileNotFoundError("Datei nicht gefunden, Pfad %s" % self.path)

        self.path = self.pre_path + self.path + self.post_path

    def rollback(self):
        for caretaker in self.caretakers:
            caretaker.undo()

    def commit(self):
        for caretaker in self.caretakers:
            caretaker.save()

    def close_file(self):
        self.file_handle.close()

    def close(self):
        self.close_file()

    def open_file(self, write: bool = False):
        mode = "rb"
        if write:
            mode = "r+b"

        self.file_handle = open(self.path, mode)

    # Since cache files can get big, writing and reading the whole file is not recommended,
    # instead reading and writing the necessary parts is better. Do that on the handler layer
    def read_file(self):
        pass

    def write_file(self):
        pass


class Caretaker:
    originator: BaseCacheClass

    def __init__(self, obj: BaseCacheClass):
        self.originator = obj
        self.save()

    def save(self):
        self.memento = self.originator.get_state()

    def undo(self):
        self.originator.set_state(self.memento)
