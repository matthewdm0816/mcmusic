#!/usr/bin/python
# This class handles the generation of a new song given a markov chain
# containing the note transitions and their frequencies.


from markov_chain import MarkovChain

import random
import hashlib
import mido
import argparse

temp_ticks = 0


class Generator:

    def __init__(self, markov_chain):
        self.markov_chain = markov_chain

    @staticmethod
    def load(markov_chain):
        assert isinstance(markov_chain, MarkovChain)
        return Generator(markov_chain)

    def _note_to_messages(self, Chunk):
        temp = []
        for idx, n in enumerate(Chunk.chunk):
            if (idx < len(Chunk.chunk) - 1):
                temp.append(mido.Message('note_on', note=n, velocity=Chunk.velocity, time=0))
            else:
                temp.append(mido.Message('note_on', note=n, velocity=Chunk.velocity, time=0))
        for idx, n in enumerate(Chunk.chunk):
            if (idx == 0):
                temp.append(mido.Message('note_off', note=n, velocity=0, time=Chunk.duration))
            else:
                temp.append(mido.Message('note_off', note=n, velocity=0, time=0))

        return temp

    def generate(self, filename):
        with mido.midifiles.MidiFile() as midi:
            print(midi.ticks_per_beat)
            track = mido.MidiTrack()
            # midi.ticks_per_beat=temp_ticks
            last_chunk = None
            # Generate a sequence of 100 notes
            for i in range(1000):
                new_chunk = self.markov_chain.get_next(last_chunk)
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
        self._parse(verbose=verbose)
        self.current_time = 0

    def _parse(self, verbose=False):
        """
        This function handles the reading of the midi and chunks the
        notes into sequenced "chords", which are inserted into the
        markov chain.
        """
        midi = mido.MidiFile(self.filename)
        self.ticks_per_beat = midi.ticks_per_beat
        print('ticks pre beat:', midi.ticks_per_beat)
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
        # 读取音乐，构造马尔可夫链
        for idx, track in enumerate(midi.tracks):
            self.current_time = 0
            last_time = -1000
            for message in track:
                if verbose:
                    print(message)
                if message.type == "set_tempo":
                    self.tempo = message.tempo
                elif message.type == "note_on" or message.type == "note_off":
                    # 要放在这，否则tempo可能未设定
                    if (idx != track_choose):
                        self.current_time += message.time
                        continue
                    if self._bucket_duration(self.current_time - last_time) > 100:
                        if (current_chunk != []):
                            self._sequence(previous_chunk,
                                           current_chunk,
                                           current_time,
                                           current_velocity)
                            print(previous_chunk, current_chunk, current_time)
                            previous_chunk = current_chunk
                            current_time = 0
                            current_chunk = []
                        if (message.velocity != 0 and message.type != "note_off"):
                            current_velocity = message.velocity
                            if (message.channel == channel_choose or channel_choose == -1):
                                print(last_time, ' ', self.current_time, ' ',
                                      self._bucket_duration(self.current_time - last_time))
                                last_time = self.current_time
                                current_chunk.append(message.note)
                    else:
                        if (message.velocity != 0 and message.type != "note_off"):
                            if (message.channel == channel_choose or channel_choose == -1):
                                print(last_time, ' ', self.current_time)
                                last_time = self.current_time
                                current_chunk.append(message.note)
                self.current_time += message.time
                current_time += message.time

    def _sequence(self, previous_chunk, current_chunk, duration, velocity):
        """
        Given the previous chunk and the current chunk of notes as well
        as an averaged duration of the current notes, this function
        permutes every combination of the previous notes to the current
        notes and sticks them into the markov chain.
        """
        """
        for n1 in previous_chunk:
            for n2 in current_chunk:
                self.markov_chain.add(
                    n1, n2, self._bucket_duration(duration))
                #print(n1," ",n2)
        """
        self.markov_chain.add(
            previous_chunk, current_chunk, self._bucket_duration(duration), velocity)

    def _bucket_duration(self, ticks):
        """
        This method takes a tick count and converts it to a time in
        milliseconds, bucketing it to the nearest 250 milliseconds.
        """
        try:
            ms = ((ticks / self.ticks_per_beat) * self.tempo) / 1000
            return int(ms)
            return int(ms - (ms % 250) + 250)
        except TypeError:
            raise TypeError(
                "Could not read a tempo and ticks_per_beat from midi")

    def get_chain(self):
        print(self.markov_chain)
        return self.markov_chain


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        # Example usage:
        # python generator.py <in.mid> <out.mid>
        chain = Parser(sys.argv[1], True).get_chain()
        Generator.load(chain).generate(sys.argv[2])
        print('Generated markov chain')
    else:
        print('Invalid number of arguments:')
        print('Example usage: python generator.py <in.mid> <out.mid>')
