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
melody_extender = [[65, 5],
					[63, 7]]
melody_length = sum([i[1] for i in melody_content])


harmony_lookup = {	0: [0, 3, 7],
					2: [2, 5, 8],
					3: [0, 3, 7],
					5: [2, 5, 8],
					7: [0, 3, 7],
					8: [2, 5, 8],
					10: [2, 5, 10]}


# chordal_melody_content = [
# 				[[67, 72, 75], 7],
# 				[[65, 70, 74], 4],
# 				[[67, 72, 75], 3],
# 				[[63, 67, 72], 4],
# 				[[65, 68, 74], 3],
# 				[[62, 65, 70], 2],
# 				[[60, 63, 68], 3],
# 				[[58, 62, 67], 7]]

# chordal_melody_length = sum([i[1] for i in chordal_melody_content])

scl = scamp_extensions.pitch.scale.Scale.aeolian(60)

s = scamp.Session(tempo = 112)

pedal_voice = s.new_part("piano")
melodic_voice_1 = s.new_part("piano")
melodic_voice_2 = s.new_part("piano")
melodic_voice_3 = s.new_part("piano")

def melody(scale_degree_alteration = 0, instrument = melodic_voice_1, play_extender = False):
	for note in melody_content:
		deg = scl.pitch_to_degree(note[0])
		new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)
		length = note[1]
		if len(note) == 3:
			if play_extender:
				length = note[2]
		instrument.play_note(new_pitch, length = length, volume = 0.3)

	if play_extender:
		for note in melody_extender:
			deg = scl.pitch_to_degree(note[0])
			new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)
			length = note[1]
			instrument.play_note(new_pitch, length = length, volume = 0.3, blocking = False)
			for _ in range(length):
				pedal_voice.play_chord([79, 91], length = 1, volume = 0.05, properties = {"articulations": ["tenuto"]})


def chordal_melody(scale_degree_alteration = 0, instrument = melodic_voice_1):
	for note in melody_content:
		deg = scl.pitch_to_degree(note[0])
		new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)	
		pitches_to_play = [new_pitch]
		length = note[1]
		i = 1
		while len(pitches_to_play) < 3:
			candidate_pitch = new_pitch - i
			# print(int(candidate_pitch%12))
			# print(harmony_lookup[new_pitch%12])
			if int(candidate_pitch%12) in harmony_lookup[new_pitch%12]:
				pitches_to_play.append(candidate_pitch)
			i += 1
		instrument.play_chord(pitches_to_play, length = length, volume = 0.3)


def pedal(n):
	for _ in range(0, n):
		pedal_voice.play_chord([79, 91], length = 1, volume = 0.05, properties = {"articulations": ["tenuto"]})


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


def third_phrase():

	s.fork(pedal, args=[chordal_melody_length])
	s.fork(chordal_melody)
	s.wait_for_children_to_finish()


def fourth_phrase():

	delays = [6, 2]

	s.fork(pedal, args=[chordal_melody_length + sum(delays)])

	s.fork(chordal_melody)
	s.wait(delays[0])
	s.fork(melody, args=[5, melodic_voice_2])
	s.wait(delays[1])
	s.fork(melody, args=[9, melodic_voice_3, True])

	s.wait_for_children_to_finish()


s.start_transcribing()

# s.fork(pedal, args=[7])
# s.wait_for_children_to_finish()

# # first_phrase()
# # second_phrase()
third_phrase()
fourth_phrase()

print(s.time())

s.stop_transcribing().to_score().show()