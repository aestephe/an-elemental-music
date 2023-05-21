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
					[63, 7]]
melody_length = sum([i[1] for i in melody_content])


harmony_lookup = {	0: [0, 3, 7],
					2: [2, 5, 10],
					3: [0, 3, 7],
					5: [5, 8, 0],
					7: [7, 10, 2],
					8: [0, 3, 8],
					10: [2, 5, 7, 10]}


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

s = scamp.Session(tempo = 104)

pedal_voice = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")

melodic_voice_3 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_2 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_1 = s.new_midi_part(midi_output_device = "IAC Driver Bus 1")
melodic_voice_4 = s.new_part("Cello", clef_preference = "tenor")

flute = s.new_part("Flute")
oboe = s.new_part("Oboe")

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
				pedal_voice.play_chord([79, 91], length = 1, volume = 0.05)


def chordal_melody(scale_degree_alteration = 0, instrument = melodic_voice_1, play_extender = False):
	for note in melody_content:
		deg = scl.pitch_to_degree(note[0])
		new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)	
		pitches_to_play = [new_pitch]
		length = note[1]
		i = 1
		while len(pitches_to_play) < len(harmony_lookup[new_pitch%12]):
			candidate_pitch = new_pitch - i
			# print(int(candidate_pitch%12))
			# print(harmony_lookup[new_pitch%12])
			if int(candidate_pitch%12) in harmony_lookup[new_pitch%12]:
				pitches_to_play.append(candidate_pitch)
			i += 1
		instrument.play_chord(pitches_to_play, length = length, volume = 0.2)

	if play_extender:
		for note in melody_extender:
			deg = scl.pitch_to_degree(note[0])
			new_pitch = scl.degree_to_pitch(deg + scale_degree_alteration)	
			pitches_to_play = [new_pitch]
			length = note[1]
			i = 1
			while len(pitches_to_play) < len(harmony_lookup[new_pitch%12]):
				candidate_pitch = new_pitch - i
				# print(int(candidate_pitch%12))
				# print(harmony_lookup[new_pitch%12])
				if int(candidate_pitch%12) in harmony_lookup[new_pitch%12]:
					pitches_to_play.append(candidate_pitch)
				i += 1
			instrument.play_chord(pitches_to_play, length = length, volume = 0.2, blocking = False)
			for _ in range(length):
				pedal_voice.play_chord([79, 91], length = 1, volume = 0.05)


def inverted_chordal_melody(axis_scale_degree = 3, 
							instrument = melodic_voice_1, 
							augmentation = 1, 
							chromatic_transposition = 0, 
							varied = False):
	sum_of_inversion = (2*axis_scale_degree)%7

	q = 0
	for note in melody_content:
		deg = scl.pitch_to_degree(note[0])
		inverted_deg = (sum_of_inversion - deg)%12

		if varied:
			if inverted_deg == 0:
				inverted_deg = 12
			elif inverted_deg == 1:
				inverted_deg = 13
			elif inverted_deg == 2:
				inverted_deg = 14	

			# OVERRIDE
			if q == 2:
				inverted_deg = 7

		else:	
			if inverted_deg == 0:
				inverted_deg = 7
			elif inverted_deg == 1:
				inverted_deg = 8
			elif inverted_deg == 2:
				inverted_deg = 9

			# OVERRIDE
			if q == 2:
				inverted_deg = 7

		new_pitch = scl.degree_to_pitch(inverted_deg)	
		pitches_to_play = [new_pitch - chromatic_transposition]
		length = Utilities.quantize(note[1]*augmentation, 1)
		i = 1
		while len(pitches_to_play) < len(harmony_lookup[new_pitch%12]):
			candidate_pitch = new_pitch - i
			# print(int(candidate_pitch%12))
			# print(harmony_lookup[new_pitch%12])
			if int(candidate_pitch%12) in harmony_lookup[new_pitch%12]:
				pitches_to_play.append(candidate_pitch - chromatic_transposition)
			i += 1
		instrument.play_chord(pitches_to_play, length = length, volume = 0.2)
		q += 1

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


def third_phrase():

	s.fork(pedal, args=[melody_length])
	s.fork(chordal_melody)
	s.wait_for_children_to_finish()


def fourth_phrase():

	delays = [6, 2]

	s.fork(pedal, args=[melody_length + sum(delays)])

	s.fork(chordal_melody)
	s.wait(delays[0])
	s.fork(chordal_melody, args=[5, melodic_voice_2])
	s.wait(delays[1])
	s.fork(melody, args=[9, melodic_voice_3, True, True])

	s.wait_for_children_to_finish()

def fifth_phrase():

	augmentation = 1

	s.fork(pedal, args=[int(Utilities.quantize(melody_length*augmentation, 1))])
	s.fork(inverted_chordal_melody, args=[3, melodic_voice_4, augmentation, 12, False])
	s.wait_for_children_to_finish()


def sixth_phrase():

	augmentation = 1

	s.fork(pedal, args=[int(Utilities.quantize(melody_length*augmentation, 1))])
	s.fork(inverted_chordal_melody, args=[3, melodic_voice_4, augmentation, 12, True])
	s.wait_for_children_to_finish()


s.start_transcribing()

s.fast_forward_in_beats(600)

s.fork(pedal, args=[11])
s.wait_for_children_to_finish()

first_phrase()
second_phrase()

fifth_phrase()

fourth_phrase()

sixth_phrase()

third_phrase()

second_phrase()

# s.fork(pedal, args=[4])
# s.wait_for_children_to_finish()

s.fork(pedal, args=[3, 1.5])
s.fork(pedal, args=[7, 0.75])
s.wait_for_children_to_finish()


# s.tempo = 138
# for _ in range(7):
# 	oboe.play_chord([63, 67, 72, 75, 79, 84], length = 1, volume = 0.5, properties = {"articulations": ["staccato"]}, blocking = False)
# 	flute.play_chord([63, 67, 72, 75, 79, 84], length = 1, volume = 0.5, properties = {"articulations": ["staccato"]})


print("Beat:", s.beat(), "\t", "Time (min):", round(s.time()/60, 2))

s.stop_transcribing().to_score().show_xml()