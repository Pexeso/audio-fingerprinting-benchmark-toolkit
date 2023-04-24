# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Named constants for the Audio Fingerprinting Benchmark Toolkit.
"""

FIELD_ANNOTATION_REFERENCE_ID = 'reference_id'
FIELD_ANNOTATION_QUERY_ID = 'query_id'
FIELD_ANNOTATION_REFERENCE_BEGIN = 'reference_begin'
FIELD_ANNOTATION_REFERENCE_END = 'reference_end'
FIELD_ANNOTATION_QUERY_BEGIN = 'query_begin'
FIELD_ANNOTATION_QUERY_END = 'query_end'
FIELD_ANNOTATION_TEMPO = 'tempo'
FIELD_ANNOTATION_PITCH = 'pitch'
FIELD_ANNOTATION_ECHO_DELAY = 'echo_delay'
FIELD_ANNOTATION_ECHO_DECAY = 'echo_decay'
FIELD_ANNOTATION_HIGH_PASS = 'high_pass'
FIELD_ANNOTATION_LOW_PASS = 'low_pass'
FIELD_ANNOTATION_REVERB = 'reverb'
FIELD_ANNOTATION_NOISE_TYPE = 'noise_type'
FIELD_ANNOTATION_NOISE_FILE = 'noise_file'
FIELD_ANNOTATION_NOISE_COLOR = 'noise_color'
FEILD_ANNOTATION_NOISE_SEED = 'noise_seed'
FIELD_ANNOTATION_NOISE_SNR = 'noise_snr'
FIELD_ANNOTATION_MERGE_PREV = 'merge_prev'
FIELD_ANNOTATION_MERGE_PREV_DURATION = 'merge_prev_duration'
FIELD_ANNOTATION_MERGE_NEXT = 'merge_next'
FIELD_ANNOTATION_MERGE_NEXT_DURATION = 'merge_next_duration'

ANNOTATION_FIELDS = [
    FIELD_ANNOTATION_REFERENCE_ID,
    FIELD_ANNOTATION_QUERY_ID,
    FIELD_ANNOTATION_REFERENCE_BEGIN,
    FIELD_ANNOTATION_REFERENCE_END,
    FIELD_ANNOTATION_QUERY_BEGIN,
    FIELD_ANNOTATION_QUERY_END,
    FIELD_ANNOTATION_TEMPO,
    FIELD_ANNOTATION_PITCH,
    FIELD_ANNOTATION_ECHO_DELAY,
    FIELD_ANNOTATION_ECHO_DECAY,
    FIELD_ANNOTATION_HIGH_PASS,
    FIELD_ANNOTATION_LOW_PASS,
    FIELD_ANNOTATION_REVERB,
    FIELD_ANNOTATION_NOISE_TYPE,
    FIELD_ANNOTATION_NOISE_FILE,
    FIELD_ANNOTATION_NOISE_COLOR,
    FEILD_ANNOTATION_NOISE_SEED,
    FIELD_ANNOTATION_NOISE_SNR,
    FIELD_ANNOTATION_MERGE_PREV,
    FIELD_ANNOTATION_MERGE_PREV_DURATION,
    FIELD_ANNOTATION_MERGE_NEXT,
    FIELD_ANNOTATION_MERGE_NEXT_DURATION,
    ]
ANNOTATION_SORT_FIELDS = [
    FIELD_ANNOTATION_QUERY_ID,
    FIELD_ANNOTATION_QUERY_BEGIN,
    FIELD_ANNOTATION_QUERY_END,
    FIELD_ANNOTATION_REFERENCE_ID,
    FIELD_ANNOTATION_REFERENCE_BEGIN,
    FIELD_ANNOTATION_REFERENCE_END,
    ]

FIELD_CHUNK_DURATION = 'duration'
FIELD_CHUNK_FILE = 'file'
FIELD_CHUNK_INDEX = 'index'
FIELD_CHUNK_MERGE_NEXT = 'merge_next'
FIELD_CHUNK_MERGE_NEXT_DURATION = 'merge_next_duration'
FIELD_CHUNK_MERGE_PREV = 'merge_prev'
FIELD_CHUNK_MERGE_PREV_DURATION = 'merge_prev_duration'
FIELD_CHUNK_POSITION = 'position'
FIELD_CHUNK_QUERY_DURATION = 'query_duration'
FIELD_CHUNK_TEMPO = 'tempo'
FIELD_CHUNK_TRACK = 'track'
FIELD_CHUNK_MODIFICATION = 'modification'
FIELD_CHUNK_NOISE = 'noise'

FIELD_INTERVAL_REFERENCE = 'reference_interval'
FIELD_INTERVAL_QUERY = 'query_interval'

FIELD_TRACK_DURATION = 'track_duration'
FIELD_TRACK_FILE = 'track_file'
FIELD_TRACK_ID = 'track_id'

FIELD_MODIFICATION_NAME = 'name'
FIELD_MODIFICATION_ECHO_DELAY = 'echo_delay'
FIELD_MODIFICATION_ECHO_DECAY = 'echo_decay'
FIELD_MODIFICATION_HIGH_PASS = 'high_pass'
FIELD_MODIFICATION_LOW_PASS = 'low_pass'
FIELD_MODIFICATION_REVERB = 'reverb'
FIELD_MODIFICATION_PITCH = 'pitch'
FIELD_MODIFICATION_TEMPO = 'tempo'

FIELD_NOISE_COLOR = 'noise_color'
FIELD_NOISE_FILE = 'noise_file'
FIELD_NOISE_SEED = 'noise_seed'
FIELD_NOISE_SNR = 'noise_snr'
FIELD_NOISE_TYPE = 'noise_type'

MERGE_NAME_CONCAT = 'concat'
MERGE_NAME_FADE = 'fade'
MERGE_NAME_OVERLAP = 'overlap'

MODIFICATION_NAME_ECHO = 'echo'
MODIFICATION_NAME_HIGH_PASS = 'high-pass'
MODIFICATION_NAME_LOW_PASS = 'low-pass'
MODIFICATION_NAME_REVERB = 'reverb'
MODIFICATION_NAME_PITCH = 'pitch'
MODIFICATION_NAME_TEMPO = 'tempo'
MODIFICATION_NAME_TEMPO_PITCH = 'tempo+pitch'

NOISE_COLOR_BROWN = 'brown'
NOISE_COLOR_PINK = 'pink'
NOISE_COLOR_WHITE = 'white'

NOISE_TYPE_CONTINUOUS = 'continuous'
NOISE_TYPE_PULSATING = 'pulsating'
NOISE_TYPE_SAMPLE = 'sample'
