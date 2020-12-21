import random, hashlib, argparse, mido, json, colorama
import numpy as np
import sklearn.cluster as cluster
from tqdm import *

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

if __name__ == "__main__":
    import sys
    for f in filenames:
        parser = Parser(f, verbose=False)
        parser.dump_records("%s.json" % f)