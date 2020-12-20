#!/usr/bin/python
# This class handles the generation of a new song given a markov chain
# containing the note transitions and their frequencies.


from markov_chain import MarkovChain

import random, hashlib, argparse, mido, json, colorama
import numpy as np
import sklearn.cluster as cluster
from utils import find, warn, print_track, bienumerate, Note, Chunk, note_to_chunk

temp_ticks = 0
colorama.init(autoreset=True)

"""
TODO: 
    1. Separate Chunk Note/Duration/Velocity
    2. Enhance Duration Processing
"""

class Generator:
    def __init__(self, markov_chain):
        self.markov_chain = markov_chain

    @staticmethod
    def load(markov_chain):
        assert isinstance(markov_chain, MarkovChain)
        return Generator(markov_chain)

    def _note_to_messages(self, chunk):
        temp = []
        if isinstance(chunk, Note):
            # add Note compatibility
            chunk = note_to_chunk(chunk)
        for idx, n in enumerate(chunk.chunk):
            if (idx < len(chunk.chunk) - 1):
                temp.append(mido.Message('note_on', note=n, velocity=Chunk.velocity, time=0))
            else:
                temp.append(mido.Message('note_on', note=n, velocity=Chunk.velocity, time=0))
        for idx, n in enumerate(chunk.chunk):
            if (idx == 0):
                temp.append(mido.Message('note_off', note=n, velocity=0, time=Chunk.duration))
            else:
                temp.append(mido.Message('note_off', note=n, velocity=0, time=0))

        return temp

    def generate(self, filename, n_notes=1000):
        with mido.midifiles.MidiFile() as midi:
            print(colorama.Fore.MAGENTA + "Generated MIDI ticks/beat: %d" % midi.ticks_per_beat)
            track = mido.MidiTrack()
            # midi.ticks_per_beat=temp_ticks
            last_chunk = None
            # Generate a sequence of some notes
            for i in range(n_notes):
                new_chunk = self.markov_chain.get_next(seed_note=last_chunk)
                if isinstance(new_chunk, Note):
                    new_chunk = note_to_chunk(new_chunk)
                track.extend(self._note_to_messages(new_chunk))
                last_chunk = []
                for n in new_chunk.chunk:
                    last_chunk.append(n)
                last_chunk = tuple(last_chunk)
            midi.tracks.append(track)
            midi.save(filename)
            print("test")
            for message in track:
                print(message)


class Parser:

    def __init__(self, filename, verbose=False):
        """
        This is the constructor for a Serializer, which will serialize
        a midi given the filename and generate a markov chain of the
        notes in the midi.
        """
        self.filename = filename
        # The tempo is number representing the number of microseconds
        # per beat.
        self.tempo = None
        # The delta time between each midi message is a number that
        # is a number of ticks, which we can convert to beats using
        # ticks_per_beat.
        self.ticks_per_beat = None
        self.markov_chain = MarkovChain()
        self.track_records = []

        self._parse(verbose=verbose)
        

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
        temp_ticks = midi.ticks_per_beat
        previous_chunk = []
        current_chunk = []
        current_velocity = 0
        current_time = 0
        # 选取track
        if (len(midi.tracks) > 1):
            print('choose tracks')
            for idx, track in enumerate(midi.tracks):
                print('track ', idx, ':', track)
            track_choose = int(input("choose the track\n"))
        else:
            track_choose = 0
            print('only 1 track')
        # 选取channel
        channels = set()
        for idx, track in enumerate(midi.tracks):
            if (idx != track_choose):
                continue
            for message in track:
                if message.type == "note_on" or message.type == "note_off":
                    channels.add(message.channel)
        if (len(channels) > 1):
            for channel in channels:
                print('channel:', channel)
            channel_choose = int(input('choose the channel\ninput -1 to choose all\n'))
        else:
            channels = list(channels)
            channel_choose = channels[0]
            print('only 1 track')

        # set music tempo previously
        for idx, track in enumerate(midi.tracks):
            for message in track:
                if message.type == "set_tempo":
                    self.tempo = message.tempo
                    print("Track tempo is set to %d" % self.tempo)

        # 读取音乐，构造马尔可夫链
        for idx, track in enumerate(midi.tracks):
            # # current_time ~ current recorded chunk total time
            # current_time = 0
            # # last_time ~ last chunk ending time
            # last_time = -1000
            # last_total_time, current_total_time = 0, 0
            # last_velocity, current_velocity = 0, 0

            # skip unchosen tracks
            if idx != track_choose and track_choose != -1:
                continue

            on_notes = []
            recorded_notes = []
            current_time = 0
            
            # enumerate messages
            for message in track:
                if verbose:
                    print(message)
                # any ON/OFF notes
                if self.is_note(message):
                    current_time += message.time
                    # TODO: use a state machine to record each note time!!!
                    pos = find(on_notes, lambda x: x.note == message.note)
                    # Note ON
                    if self.is_on(message):
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
                    # update current time
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
            print(cores, labels)
            
            chunks, chunk = [], []
            last_label = None
            for idx, label in enumerate(labels):
                if label == last_label:
                    # append into chunk
                    chunk.append(recorded_notes[idx])
                elif label == -1:
                    # single note
                    chunks.append(chunk)
                    chunks.append([recorded_notes[idx]])
                    last_label = None
                else:
                    # new chunk
                    chunks.append(chunk)
                    chunk = [recorded_notes[idx]]
                    last_label = label
            
            # save clustered chunks into state & MC chain
            self.track_records.append(chunks)
            for prev, now in bienumerate(chunks):
                self.markov_chain.add(prev, now)
            


    def dump_records(self, filename):
        with open(filename, 'w') as fp:
            json.dump(self.track_records, fp)


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

    def get_chain(self):
        print(self.markov_chain)
        return self.markov_chain


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        # Parse only | for debugging
        parser = Parser(sys.argv[1], verbose=True)
    elif len(sys.argv) == 3:
        # Example usage:
        # python generator.py <in.mid> <out.mid>
        chain = Parser(sys.argv[1], True).get_chain()
        Generator.load(chain).generate(sys.argv[2])
        print('Generated markov chain')
    else:
        print('Invalid number of arguments:')
        print('Example usage: python generator.py <in.mid> <out.mid>')
