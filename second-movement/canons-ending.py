import clockblocks.clock
import itertools
import math
from pyalex.chord import Chord
from pyalex.pitch import Pitch
from pyalex.polyphony import QueuedVoiceManager, VoiceId
from pyalex.rand import RandomizerGroup
from pyalex.utilities import Utilities, LengthMultiplier, LengthMultiplierManager
import random
import scamp
import scamp_extensions.pitch.scale
import statistics
import sys	
from threading import Thread

melody_content = [
			[75, 7],
			[74, 4],
			[75, 3],
			[72, 4],
			[74, 3],
			[70, 2],
			[68, 3],
			[67, 7, 3]]
melody_extender = [[65, 7],
					[67, 2],
					[63, 2],

					[65, 3],
					[67, 2],
					[63, 2],

					[65, 7],
					[67, 2]
					]
melody_length = sum([i[1] for i in melody_content])


harmony_lookup = {	0: [0, 3, 7],
					2: [2, 5, 10],
					3: [0, 3, 7],
					5: [5, 8, 0],
					7: [7, 10, 2],
					8: [0, 3, 8],
					10: [2, 5, 7, 10]}

scl = scamp_extensions.pitch.scale.Scale.aeolian(60)

s = scamp.Session(tempo = 104)

pedal_voice = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")

melodic_voice_3 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_2 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_1 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_4 = s.new_part("Cello", clef_preference = "tenor")

def melody(scale_degree_alteration = 0, instrument = melodic_voice_1, play_extender = False, double = False):
	for note in melody_content:
		deg = scl.pitch_to_degree(note[0])
		new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)
		length = note[1]
		if len(note) == 3:
			if play_extender:
				length = note[2]
		pitches_to_play = [new_pitch]
		if double:
			pitches_to_play.extend([new_pitch + 12])
		instrument.play_chord(pitches_to_play, length = length, volume = 0.3)

	if play_extender:
		for note in melody_extender:
			deg = scl.pitch_to_degree(note[0])
			new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)
			length = note[1]
			pitches_to_play = [new_pitch]
			if double:
				pitches_to_play.extend([new_pitch + 12])
			instrument.play_chord(pitches_to_play, length = length, volume = 0.3, blocking = False)
			for _ in range(length):
				pedal_voice.play_chord([79, 91], length = 1, volume = 0.05, properties = {"articulations": ["tenuto"]})


def pedal(n, note_length = 1):
	for _ in range(0, n):
		pedal_voice.play_chord([79, 91], length = note_length, volume = 0.05)


def first_phrase():

	s.fork(pedal, args=[melody_length])
	s.fork(melody)
	s.wait_for_children_to_finish()


def second_phrase():

	delays = [6, 2]

	s.fork(pedal, args=[melody_length + sum(delays)])

	s.fork(melody)
	s.wait(delays[0])
	s.fork(melody, args=[5, melodic_voice_2])
	s.wait(delays[1])
	s.fork(melody, args=[9, melodic_voice_3, True])

	s.wait_for_children_to_finish()


s.start_transcribing()

first_phrase()

second_phrase()

s.fork(pedal, args=[1])
wt_pitches = [79, 77, 75, 73, 71, 69]
wt_lengths = [7, 3, 2, 2, 7, 3]
for p, l in zip(wt_pitches, wt_lengths):
	melodic_voice_3.play_note(p, length = l, volume = 0.3)


print("Beat:", s.beat(), "\t", "Time (min):", round(s.time()/60, 2))

s.stop_transcribing().to_score(time_signature = ["1/4", "4/4"]).show_xml()