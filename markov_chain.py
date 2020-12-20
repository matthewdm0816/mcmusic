#!/usr/bin/python
# This class handles the storage and manipulation of a markov chain of notes.

from collections import Counter, defaultdict, namedtuple
import random, json
import numpy as np

from utils import Note, Chunk

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
        """
        Add to transition matrix
        """
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
        """
        Create a note from priori P(N)
        """
        # create a note starts at timepoint 0
        note = Note(st=0)
        log_prob = 0 # 0 == ln 1
        for name, out_name in zip(self.names, ['note', 'end_time', 'velocity']):
            choices = np.array(list(self.chains[name].keys()))
            ps = np.array([self.sums[name][key] for key in self.chains[name].keys()])
            # print(choices, ps)
            ps = ps / ps.sum() # generate weight
            if verbose:
                print(ps)
            
            # take a choice
            zipped = np.stack([choices, ps], axis=1)
            indices = np.arange(zipped.shape[0])
            prop, prob = list(zipped[np.random.choice(indices, p=ps)])
            note[out_name] = int(prop)
            log_prob += np.log(prob)
        return note, log_prob

    def get_next(self, seed_note=None, greedy=True, verbose=True):
        """
        Get next note depending on last note(seed note)
        According to P(N_{i+1}|N_i)
        """
        log_prob = 0 # log-likelihood
        if seed_note is None:
            seed_note, lld = self._sample_seed_note(verbose=True)
            log_prob += lld
        if greedy:
            # greedily take
            note = Note(st=seed_note.end_time)
            for name, out_name in zip(self.names, ['note', 'end_time', 'velocity']):
                stats = self.chains[name][seed_note[name]]
                choices = np.array(list(stats.keys()))
                ps = np.array([stats[key] for key in stats.keys()])
                ps = ps / ps.sum() # generate weight

                # take a choice
                zipped = np.stack([choices, ps], axis=1)
                indices = np.arange(zipped.shape[0])
                prop, prob = list(zipped[np.random.choice(indices, p=ps)])
                note[out_name] = int(prop)
                log_prob += np.log(prob)
            note.end_time += note.start_time # fix end_time from duration
        if verbose:
            print(note, log_prob)
        return note, log_prob

    def dump(self, f):
        """
        Save chains from JSON
        """
        with open(f, 'w') as fp:
            state_dict = {
                "chains": self.chains,
                "sums": self.sums
            }
            json.dump(state_dict, fp)

    def load(self, f):
        """
        Load chains from JSON
        """
        with open(f, 'r') as fp:
            state_dict = json.load(fp)
            for name, chain in state_dict["chains"]:
                for k, counter in chain:
                    for key, val in counter:
                        self.chains[name][k][key] = val
            for name, sums in state_dict["sums"]:
                for k, val in sums:
                    self.sums[name][k] = val

    def generate_dp(self, seed_note=None):
        # TODO: Use DP to generate melody
        pass


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
