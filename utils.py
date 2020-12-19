"""
    Utils used in MCMusic
"""
import colorama
colorama.init(autoreset=True)

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