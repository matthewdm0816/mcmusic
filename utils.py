"""
    Utils used in MCMusic
"""

def find(list, crit):
    pos = []
    for i, item in enumerate(list):
        if crit(item):
            pos.append(i)
    return pos