#!/usr/bin/python
# This class handles the storage and manipulation of a markov chain of notes.

from collections import Counter, defaultdict, namedtuple
import random, json
import numpy as np

from utils import Note

Chunk = namedtuple('Chunk', ['chunk', 'duration', 'velocity'])

class MarkovChainOld:

    def __init__(self):
        self.chain = defaultdict(Counter)
        self.sums = defaultdict(int)

    @staticmethod
    def create_from_dict(dict):
        m = MarkovChain()
        # FIXME: bugged!
        for from_note, to_notes in dict.items():
            for k, v in to_notes.items():
                m.add(from_note, k, v)
        return m

    def _serialize(self, chunk, duration, velocity=127):
        return Chunk(chunk, duration, velocity)

    def __str__(self):
        return str(self.get_chain())

    def add(self, from_note, to_note, duration, velocity):
        from_note1=tuple(from_note)
        to_note1=tuple(to_note)
        self.chain[from_note1][self._serialize(to_note1, duration, velocity)] += 1
        self.sums[from_note1] += 1

    def get_next(self, seed_note):
        if seed_note is None or seed_note not in self.chain:
            random_chain = self.chain[random.choice(list(self.chain.keys()))]
            return random.choice(list(random_chain.keys()))
        next_note_counter = random.randint(0, self.sums[seed_note])
        for note, frequency in self.chain[seed_note].items():
            next_note_counter -= frequency
            if next_note_counter <= 0:
                return note

    def merge(self, other):
        assert isinstance(other, MarkovChain)
        self.sums = defaultdict(int)
        for from_note, to_notes in other.chain.items():
            self.chain[from_note].update(to_notes)
        for from_note, to_notes in self.chain.items():
            self.sums[from_note] = sum(self.chain[from_note].values())

    def get_chain(self):
        return {k: dict(v) for k, v in self.chain.items()}

    def print_as_matrix(self, limit=10):
        columns = []
        for from_note, to_notes in self.chain.items():
            for note in to_notes:
                if note not in columns:
                    columns.append(note)
        _col = lambda string: '{:<8}'.format(string)
        _note = lambda note: '{}:{}'.format(note.note, note.duration)
        out = _col('')
        out += ''.join([_col(_note(note)) for note in columns[:limit]]) + '\n'
        for from_note, to_notes in self.chain.items():
            out += _col(from_note)
            for note in columns[:limit]:
                out += _col(to_notes[note])
            out += '\n'
        print(out)

    def save(self, fp):
        # TODO!
        with open(fp, 'w') as f:
            json.dump(self.chain, f)

class MarkovChain:
    names = ['note', 'duration', 'velocity']
    def __init__(self):
        """
        Chains: 
            Note -> Note
            Vel -> Vel
            Duration -> Duration
        Probable Improvement:
            Note, Vel -> Duration
        """
        self.chains, self.sums = dict(), dict()
        for name in self.names:
            self.chains[name] = defaultdict(Counter)
            self.sums[name] = defaultdict(int)
            # self.sum[name] = 0
    
    def add(self, prev, now, melody=True):
        # for MELODY track, very likely to be no chords
        if melody:
            assert len(prev) == 1 and len(now) == 1, "Non-single note detected in MELODY mode"
            p, n = prev[0], now[0]
            for name in self.names:
                # record transitions
                self.chains[name][self._normalize(p[name], name)][self._normalize(n[name], name)] += 1
                self.sums[name][self._normalize(p[name], name)] += 1
                # self.sum[name] += 1
        else:
            raise NotImplementedError
        return 

    @staticmethod
    def _normalize(value, name):
        if name == 'duration':
            # normalize duration
            return MarkovChain._normalize_duration(value)
        else:
            return value

    @staticmethod
    def _normalize_duration(duration):
        """
        normalize to closet 10 ticks
        TODO: norm to 50ms
        """
        return int(round(duration / 10)) * 10

    def _sample_seed_note(self, verbose=False):
        # create a note starts at timepoint 0
        note = Note(st=0)
        for name, out_name in zip(self.names, ['note', 'end_time', 'velocity']):
            choices = np.array(self.chains[name].items)
            ps = np.array([self.sums[name][item] for item in self.chains[name].items])
            ps /= ps.sum() # generate weight
            if verbose:
                print(ps)
            note[out_name] = np.choice(choices, p=ps)
        return note

    def get_next(self, seed_note=None, greedy=True, verbose=True):
        if seed_note is None:
            seed_note = self._sample_seed_note(verbose=True)
        if greedy:
            note = Note(st=seed_note.end_time)
            for name, out_name in zip(self.names, ['note', 'end_time', 'velocity']):
                stats = self.chains[name][seed_note[name]]
                choices = np.array(stats.items)
                ps = np.array([stats[item] for item in stats.items])
                ps /= ps.sum() # generate weight
                note[out_name] = np.choice(choices, p=ps)
            note.end_time += note.start_time # fix end_time from duration
        if verbose:
            print(note)
        return note

if __name__ == '__main__':
    import sys
    # if len(sys.argv) == 2 and sys.argv[1] == 'test':
    #     m = MarkovChain()
    #     m.add(12, 14, 200)
    #     m.add(12, 15, 200)
    #     m.add(14, 25, 200)
    #     m.add(12, 14, 200)
    #     n = MarkovChain()
    #     n.add(10, 13, 100)
    #     n.add(12, 14, 200)
    #     m.merge(n)
    #     print(m)
    #     m.print_as_matrix()
