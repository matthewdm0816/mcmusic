import random, hashlib, argparse, mido, json, colorama
import numpy as np
import sklearn.cluster as cluster
from tqdm import *
import os, sys

from utils import find, warn, print_track, bienumerate, Note, Chunk, note_to_chunk
from markov_chain import MarkovChain
from generator import Parser

temp_ticks = 0
colorama.init(autoreset=True)

filenames = [
            'sample/001.mid', 
            'sample/002.mid', 
            'sample/003.mid', 
            'sample/004.mid',
            'sample/005.mid',
            'sample/006.mid',
        ]

filenames = [
    os.path.join('..', 'POP909-Dataset', 'POP909', "%03d" % i, "%03d.mid" % i) for i in range(1, 100)
]

outnames = [
    os.path.join("sample", "%03d.json" % i) for i in range(1, 100)
]

if __name__ == "__main__":
    import sys
    for f, out in zip(filenames, outnames):
        print(colorama.Fore.MAGENTA + "Processing MIDI %s" % (f))
        parser = Parser(f, verbose=False)
        parser.dump_records(out)