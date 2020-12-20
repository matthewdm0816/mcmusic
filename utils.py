"""
    Utils used in MCMusic
"""
import colorama
colorama.init(autoreset=True)

from collections import namedtuple

# hold duration only
Chunk = namedtuple('Chunk', ['chunk', 'duration', 'velocity'])

class bienumerate():
    """
    Bi-step enumerating iterables(like list)
    [1, 2, 3, 4] => (1, 2), (2, 3), (3, 4)
    """
    def __init__(self, l):
        self.iter = iter(l)
        self.iter2 = iter(l)
        next(self.iter2)
    
    def __iter__(self):
        return self

    def __next__(self):
        return next(self.iter), next(self.iter2)

def find(list, crit):
    """
    Find with criterion in a list
    """
    pos = []
    for i, item in enumerate(list):
        if crit(item):
            pos.append(i)
    return pos

def warn(msg):
    """
    Print in magenta, as a warning
    """
    print(colorama.Fore.MAGENTA + msg)

def print_track(notes):
    """
    print parsed notes
    """
    for note in notes:
        print(note)

class Note:
    def __init__(self, note=None, velocity=None, st=None, et=None):
        self.note, self.velocity = note, velocity
        self.start_time, self.end_time = st, et

    @property
    def duration(self):
        return self.end_time - self.start_time

    # @property
    # def note(self):
    #     return self._note

    # @note.setter
    # def note(self, value):
    #     self._note = int(round(value))

    # @property
    # def velocity(self):
    #     return self._velocity

    # @velocity.setter
    # def velocity(self, value):
    #     self._velocity = int(round(value))

    # @property
    # def start_time(self):
    #     return self._start_time

    # @start_time.setter
    # def start_time(self, value):
    #     self._start_time = int(round(value))

    # @property
    # def end_time(self):
    #     return self._end_time

    # @end_time.setter
    # def end_time(self, value):
    #     self._end_time = int(round(value))

    def __repr__(self):
        return "Note(note=%d, vel=%d, duration=%d @ %d)" % (
            self.note, self.velocity, self.duration, self.start_time
        )

    def copy(self):
        return Note(self.note, self.velocity, self.start_time, self.end_time)

    def __getitem__(self, key):
        # enables hash-like visiting
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

def note_to_chunk(note: Note):
    return Chunk(chunk=[note.note], duration=note.duration, velocity=note.velocity)