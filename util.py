#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Utility functions for the Audio Fingerprinting Benchmark Toolkit.
"""

import math
import os.path
import subprocess
import sys


def get_track_duration(fn):
    """
    Get the duration in seconds of the given media file.
    """

    # Simple "ffprobe -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $fn" does not work well
    # for media files with Variable Bit Rate.
    # So we are reading the timestamp and duration of the last packet.
    args = ['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'packet=pts_time:packet=duration_time', '-of', 'default=noprint_wrappers=1:nokey=1', fn]
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        print(f'{fn}: ffprobe failed!', file=sys.stderr)
        print('STDOUT:\n', p.stdout.decode(), file=sys.stderr)
        print('STDERR:\n', p.stderr.decode(), file=sys.stderr)
        return None

    # Decode the output, and calculate the stream duration
    try:
        lines = p.stdout.decode().splitlines()[-2:]  # PTS and duration of the last packet (in seconds)
        return round(float(lines[0]) + float(lines[1]), 3)
    except BaseException as e:
        print(f'{fn}: invalid output of ffprobe!', file=sys.stderr)
        print('STDOUT:\n', p.stdout.decode(), file=sys.stderr)
        return None


def get_track_id_from_file_name(fn):
    """
    Get the track ID (the base file name without known extensions) from the file name.
    """
    known_exts = set(['.aac', '.flac', '.m4a', '.mp3', '.ogg', '.opus', '.vorbis', '.wav', '.wma',
                      '.avi', '.flv', '.mkv', '.mov', '.mp4', '.mpg', '.wmv',
                      '.csv', '.json', '.msgpack', '.txt',
                     ])

    track_id = os.path.basename(fn)
    while True:
        root, ext = os.path.splitext(track_id)
        if ext in known_exts:
            track_id = root
        else:
            break

    return track_id


def pitch_scale_to_cents(scale):
    """
    Convert pitch scale to cents (100 cents = 1 semitone, 12 semitones = 1 octave).
    """
    return (1200 * math.log(scale) / math.log(2))


def tempo_scale_to_per_cent(scale):
    """
    Convert tempo scale to per cent.
    """
    return 100 * scale
