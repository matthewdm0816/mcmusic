#!/usr/bin/python
# This class handles the generation of a new song given a markov chain
# containing the note transitions and their frequencies.



import random, hashlib, argparse, mido, json, colorama
import numpy as np
import sklearn.cluster as cluster
from tqdm import *

from utils import find, warn, print_track, bienumerate, Note, Chunk, note_to_chunk
from markov_chain import MarkovChain

temp_ticks = 0
colorama.init(autoreset=True)

"""
TODO: 
    1. Separate Chunk Note/Duration/Velocity
    2. Enhance Duration Processing
"""

class Generator:
    def __init__(self, markov_chain, tpb = None, tempo=None):
        self.markov_chain = markov_chain
        self.tempo, self.ticks_per_beat = tempo, tpb

    @staticmethod
    def load(state):
        markov_chain, tpb, tempo = state
        assert isinstance(markov_chain, MarkovChain)
        return Generator(markov_chain, tpb, tempo)

    def _note_to_messages(self, chunk):
        # TODO: add 休止符 support
        messages = []
        # add Note compatibility
        if isinstance(chunk, Note):
            chunk = note_to_chunk(chunk)

        # a rest
        rest_note = 64
        if 0 in chunk.chunk:
            messages.append(mido.Message('note_on', 
                note=rest_note, 
                velocity=0, 
                time=0
                )
            )
            messages.append(mido.Message('note_off', 
                note=rest_note, 
                velocity=0, 
                time=chunk.duration
                )
            )
        else:
            # add note_on msg
            for idx, n in enumerate(chunk.chunk):
                assert n != 0
                # print(n, chunk.velocity, chunk.duration)
                messages.append(mido.Message('note_on', 
                    note=n, 
                    velocity=chunk.velocity, 
                    time=0
                    )
                )

            # add note_off msg
            for idx, n in enumerate(chunk.chunk):
                assert n != 0
                messages.append(mido.Message('note_off', 
                    note=n, 
                    velocity=0,
                    time=chunk.duration if idx == 0 else 0 # elapse time at first note_off
                    )
                )

        return messages

    def generate(self, filename, n_notes=300, verbose=True):
        with mido.midifiles.MidiFile() as midi:
            if self.ticks_per_beat is not None:
                midi.ticks_per_beat = self.ticks_per_beat
            print(colorama.Fore.MAGENTA + "Generated MIDI ticks/beat: %d" % midi.ticks_per_beat)
            track = mido.MidiTrack()
            # midi.ticks_per_beat=temp_ticks
            last_chunk = None
            log_prob = 0
            if self.tempo is not None:
                track.extend([mido.MetaMessage('set_tempo', tempo=self.tempo)])
            # Generate a sequence of some notes
            for _ in trange(n_notes):
                # get note and its log-prob
                new_chunk, lld = self.markov_chain.get_next(seed_note=last_chunk, verbose=verbose)
                log_prob += lld

                # expend to track
                track.extend(self._note_to_messages(new_chunk))

                # if rest, don't update N_i
                if new_chunk.note == 0:
                    # translate last note, set new duration
                    duration = new_chunk.duration
                    last_chunk.end_time = new_chunk.end_time
                    last_chunk.start_time = new_chunk.end_time - duration
                else:
                    last_chunk = new_chunk
            midi.tracks.append(track)
            midi.save(filename)
            print(colorama.Fore.MAGENTA + 
                "Finished generating MIDI of length: %d, log-likelihood: %d, saved to %s" 
                % (n_notes, log_prob, filename)
            )
            if verbose:
                for message in track:
                    print(message)


class Parser:

    def __init__(self, filename=None, verbose=False):
        """
        This is the constructor for a Serializer, which will serialize
        a midi given the filename and generate a markov chain of the
        notes in the midi.
        """
        # The tempo is number representing the number of microseconds
        # per beat.
        self.tempo = None
        # The delta time between each midi message is a number that
        # is a number of ticks, which we can convert to beats using
        # ticks_per_beat.
        self.ticks_per_beat = None
        self.markov_chain = MarkovChain()
        self.track_records = []
        if filename is not None:
            self.parse_file(filename, verbose=verbose)
        
    def parse_file(self, filename, verbose=False):
        self.filename = filename
        self._parse(verbose=verbose)

    @property
    def beat_ticks(self):
        return self.tempo / 1000 * self.ticks_per_beat

    @staticmethod
    def is_on(message):
        # check if a message is real note_on
        return message.type == 'note_on' and message.velocity != 0

    @staticmethod
    def is_note(message):
        return message.type in ('note_on', 'note_off')

    def _parse(self, verbose=False):
        """
        This function handles the reading of the midi and chunks the
        notes into sequenced "chords", which are inserted into the
        markov chain.
        """
        midi = mido.MidiFile(self.filename)
        self.ticks_per_beat = midi.ticks_per_beat
        print('ticks per beat:', midi.ticks_per_beat)
        current_time = 0

        # set music tempo previously
        for idx, track in enumerate(midi.tracks):
            for message in track:
                if message.type == "set_tempo":
                    self.tempo = message.tempo
                    print("Track tempo is set to %d" % self.tempo)

        # 读取音乐，构造马尔可夫链
        for idx, track in enumerate(midi.tracks):

            # skip unchosen tracks
            if track.name != 'MELODY':
                continue

            on_notes = []
            recorded_notes = []
            current_time = 0
            
            # enumerate messages
            # TODO: find 休止符, add as note 0
            for message in track:
                if verbose:
                    print(message)
                # any ON/OFF notes
                if self.is_note(message):
                    # update current time
                    current_time += message.time
                    # use a state machine to record each note time!!!
                    pos = find(on_notes, lambda x: x.note == message.note)
                    # Note ON
                    if self.is_on(message):
                        # check 休止符 before add some note
                        if on_notes == [] and message.time > self.ticks_per_beat / 8 and message.time != current_time:
                            # skip trimming(at start) rest
                            recorded_notes.append(Note(
                                note=0,
                                velocity=0,
                                st=current_time - message.time, 
                                et=current_time
                            ))

                        on_notes.append(Note(
                            note=message.note, 
                            velocity=message.velocity,
                            st=current_time
                        ))
                    # Note END
                    else: 
                        if pos == []: # not find some note to end before start
                            warn("Warning: Note not found to end")
                            # raise ValueError("Note not found to end")
                            continue
                        else:
                            # NOTE: choose first note to end
                            note = on_notes[pos[0]].copy() # use a new copy
                            note.end_time = current_time # set end_time
                            del on_notes[pos[0]] # delete existed note
                            recorded_notes.append(note) # append to notes lib
                        
            # end up all remaining notes
            for note in on_notes:
                note.end_time = current_time
                recorded_notes.append(note.copy())
            # empty/meta track
            if recorded_notes == []:
                warn("Skipping meta/empty track")
                continue

            # sort with start_time
            recorded_notes.sort(key=lambda note: note.start_time)
            # self.track_records.append(recorded_notes)
            if verbose:
                print_track(recorded_notes)
            print("In total %d notes in this track" % len(recorded_notes))
            self.track_records.append(recorded_notes)
            # --- MC parsing ---
            start_times = np.array([note.start_time for note in recorded_notes])
            # start_times = start_times / self.ticks_per_beat * self.tempo / 1000
            # print(start_times)
            # print(start_times.shape)

            # cluster notes
            # NOTE: DBSCAN seems clusters these notes very well, -1 notates single note
            cores, labels = cluster.dbscan(
                start_times.reshape(-1, 1), eps=0.3, min_samples=2, n_jobs=4, p=2
            )
            if verbose:
                print(cores, labels)
            
            chunks, chunk = [], []
            last_label = None
            for idx, label in enumerate(labels):
                if label == last_label:
                    # append into chunk
                    chunk.append(recorded_notes[idx])
                elif label == -1:
                    # single note
                    if chunk != []:
                        chunks.append(chunk)
                    chunks.append([recorded_notes[idx]])
                    last_label = None
                else:
                    # new chunk
                    if chunk != []:
                        chunks.append(chunk)
                    chunk = [recorded_notes[idx]]
                    last_label = label
            
            # save clustered chunks into state & MC chain
            # self.track_records.append(chunks)
            last_note = None
            for note in chunks:
                if last_note is None:
                    last_note = note
                    continue
                
                self.markov_chain.add(last_note, note, melody=True)
                if note[0].note != 0:
                    # skip rest | monkey patch
                    # TODO: more robust
                    last_note = note
            

    def dump_records(self, filename):
        class MyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Note): 
                    return obj.get_state_dict()
                return json.JSONEncoder.default(self, obj)

        with open(filename, 'w') as fp:
            json.dump(self.track_records, fp, cls=MyEncoder)
            


    def _bucket_duration(self, ticks):
        """
        This method takes a tick count and converts it to a time in
        milliseconds, bucketing it to the nearest 250 milliseconds.
        Changed: return real duration.
        """
        try:
            ms = ((ticks / self.ticks_per_beat) * self.tempo) / 1000
            return int(ms)
            # return int(ms - (ms % 250) + 250)
        except TypeError:
            raise TypeError(
                "Could not read a tempo and ticks_per_beat from midi")

    def get_state_dict(self):
        # print(self.markov_chain)
        return self.markov_chain, self.ticks_per_beat, self.tempo


def generate(in_list, out_list, mapping='serial'):
    """
    generate multiple music from multiple input
    mapping: way how input maps to output
    """
    assert mapping in ('serial', 'total') or isinstance(mapping, list)
    if mapping == 'serial':
        assert len(in_list) == len(out_list), 'In/out list of songs mismatch'
        mapping = [(i, i) for i in range(len(in_list))]
    elif mapping == 'total':
        mapping = [(i, 1) for i in range(len(out_list))]

    for files in in_list:
        for fn in files:
            parser = Parser(fn, verbose=False)
            
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        # Parse only | for debugging
        parser = Parser(sys.argv[1], verbose=False)
    elif len(sys.argv) == 3:
        # Example usage:
        # python generator.py <in.mid> <out.mid>
        parser = Parser(sys.argv[1], verbose=False)
        parser.dump_records('dump.json')
        state = parser.get_state_dict()
        Generator.load(state).generate(sys.argv[2], n_notes=100, verbose=False)
    else:
        print('Invalid number of arguments:')
        print('Example usage: python generator.py <in.mid> <out.mid>')
