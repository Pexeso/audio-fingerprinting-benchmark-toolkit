#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Generator of the query audio files from the reference audio files.
"""

import argparse
import csv
import functools
import glob
import math
import multiprocessing
import os
import queue
import random
import subprocess
import sys
import threading

from operator import itemgetter

from fields import *
from util import *


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('track_list', nargs='+', help='CSV file with track list')
    parser.add_argument('--annotation-file', '-a', default='annotations.csv',
                        help='Output file with annotations for generated queries')
    parser.add_argument('--query-dir', '-q', default='queries',
                        help='Directory for generated queries')
    parser.add_argument('--tmp-dir', '-t', default='tmp',
                        help='Directory for temporary files')
    parser.add_argument('--threads', '-T', type=int, default=multiprocessing.cpu_count(),
                        help='Number of threads')

    parser.add_argument('--codec', '-c', choices=['mp3', 'aac'], default='mp3',
                        help='Audio codec used for the generated queries')
    parser.add_argument('--sample-rate', '-r', type=int, default=44100,
                        help='Audio sample rate used for the generated queries')

    parser.add_argument('--difficulty', '-d', choices=['easy', 'medium', 'hard'], default='hard',
                        help='Maximum difficulty of the generated query chunks')
    parser.add_argument('--dry-run', '-D', action='store_true',
                        help='Dry run - do not generate query audios, just annotations')
    parser.add_argument('--num-queries', '-n', type=int, help='Number of query chunks')
    parser.add_argument('--seed', '-s', type=int, help='Random seed')

    return parser


def initialize(args):
    """
    Initialize for generating the queries.
    """
    os.makedirs(args.query_dir, exist_ok=True)
    os.makedirs(args.tmp_dir, exist_ok=True)


def cleanup(args):
    """
    Cleanup after generating the queries.
    """
    for fn in glob.glob(os.path.join(args.tmp_dir, 'chunk_*_*.*')):
        os.remove(fn)

    try:
        os.rmdir(args.tmp_dir)
    except:
        pass


class QueryGenerator:
    """
    Generator of query files.
    """

    def __init__(self, query_dir, tmp_dir, num_threads):
        """
        Constructor.

        Parameters:
            query_dir: Directory for generated queries
            tmp_dir: Directory for temporary files
            num_threads: Number of threads
        """
        self._query_dir = query_dir
        self._tmp_dir = tmp_dir
        self._num_threads = num_threads

        self._tracks = dict()
        self._annotations = []

        self._error_in_thread = None
        self._queue = None
        self._threads = []

        self._noise_samples = glob.glob('noise/*.wav')


    def create_threads(self):
        """
        Create worker threads.
        """
        self._queue = queue.Queue()
        self._threads = [threading.Thread(target=self.__worker) for i in range(self._num_threads)]
        for thread in self._threads:
            thread.start()


    def join_threads(self):
        """
        Join the worker threads.
        """
        if self._threads:
            for thread in self._threads:
                self._queue.put(None)
            for thread in self._threads:
                thread.join()

            self._queue = None
            self._threads = []


    def __worker(self):
        """
        Thread worker method processing the tasks.
        """
        for task in iter(self._queue.get, None):
            try:
                task()
            except BaseException as e:
                self._error_in_thread = e
            self._queue.task_done()


    def _init_difficulty(self, difficulty):
        self._merge_choices = []
        self._modification_choices = []
        self._tempo_pitch_sigma = 0.01
        self._noise_volume_start = 0

        level = {'easy': 1,
                 'medium': 2,
                 'hard': 3,
                 }[difficulty]

        if level >= 1:
            self._merge_choices += [
                MERGE_NAME_CONCAT,
            ]
            self._modification_choices += [
                MODIFICATION_NAME_HIGH_PASS,
                MODIFICATION_NAME_LOW_PASS,
                MODIFICATION_NAME_PITCH,
                MODIFICATION_NAME_TEMPO,
                MODIFICATION_NAME_TEMPO_PITCH,
            ]
            self._tempo_pitch_sigma = 0.04
            self._noise_volume_start = 2

        if level >= 2:
            self._merge_choices += [
                MERGE_NAME_FADE,
                MERGE_NAME_OVERLAP,
            ]
            self._modification_choices += [
                MODIFICATION_NAME_ECHO,
            ]
            self._tempo_pitch_sigma = 0.12
            self._noise_volume_start = 1

        if level >= 3:
            self._modification_choices += [
                MODIFICATION_NAME_REVERB,
            ]
            self._tempo_pitch_sigma = 0.25
            self._noise_volume_start = 0

        self._modification_choices += [None] * (15 - len(self._modification_choices))


    def _get_random_tempo_or_pitch(self):
        """
        Get random tempo or pitch for rubberband FFmpeg filter.
        """
        value = random.normalvariate(0, self._tempo_pitch_sigma)
        if value >= 0:
            value += 1
        else:
            value = 1 / (1 - value)

        return value


    def _get_random_modification(self):
        """
        Get a random modification together with its parameters, or None.
        """
        name = random.choice(self._modification_choices)
        if not name:
            return None

        modification = {FIELD_MODIFICATION_NAME: name}

        if name == MODIFICATION_NAME_ECHO:
            modification[FIELD_MODIFICATION_ECHO_DELAY] = 10 * random.randint(1, 50)
            modification[FIELD_MODIFICATION_ECHO_DECAY] = round(random.uniform(0.3, 0.6), 1)

        elif name == MODIFICATION_NAME_HIGH_PASS:
            modification[FIELD_MODIFICATION_HIGH_PASS] = 100 * random.randint(1, 4)

        elif name == MODIFICATION_NAME_LOW_PASS:
            modification[FIELD_MODIFICATION_LOW_PASS] = 1000 * random.randint(3, 10)

        elif name == MODIFICATION_NAME_REVERB:
            modification[FIELD_MODIFICATION_REVERB] = 1

        elif name == MODIFICATION_NAME_PITCH:
            value = self._get_random_tempo_or_pitch()
            modification[FIELD_MODIFICATION_PITCH] = value

        elif name == MODIFICATION_NAME_TEMPO:
            value = self._get_random_tempo_or_pitch()
            modification[FIELD_MODIFICATION_TEMPO] = value

        elif name == MODIFICATION_NAME_TEMPO_PITCH:
            value = self._get_random_tempo_or_pitch()
            modification[FIELD_MODIFICATION_PITCH] = value
            modification[FIELD_MODIFICATION_TEMPO] = value

        return modification


    def _get_random_noise(self):
        """
        Get a random noise together with its parameters, or None.
        """
        noise_choices = [NOISE_TYPE_CONTINUOUS, NOISE_TYPE_PULSATING] + \
                        [NOISE_TYPE_SAMPLE] * len(self._noise_samples)
        noise_choices += [None] * len(noise_choices)

        typ = random.choice(noise_choices)
        if not typ:
            return None

        snr = 5 * random.randint(self._noise_volume_start, 3)

        if typ == NOISE_TYPE_SAMPLE:
            file_name = random.choice(self._noise_samples)

            noise = {FIELD_NOISE_FILE: file_name,
                     FIELD_NOISE_SNR: snr,
                     FIELD_NOISE_TYPE: typ,
                     }
        else:
            color = random.choice([NOISE_COLOR_BROWN,
                                   NOISE_COLOR_PINK,
                                   NOISE_COLOR_WHITE])
            seed = random.randint(0, 0xffffffff)

            noise = {FIELD_NOISE_COLOR: color,
                     FIELD_NOISE_SEED: seed,
                     FIELD_NOISE_SNR: snr,
                     FIELD_NOISE_TYPE: typ,
                     }

        return noise


    def _create_chunk(self, chunk, codec, sample_rate, query_index):
        """
        Create a (modified) chunk from the track.
        """
        # basic arguments with cutting out the chunk
        args = ['ffmpeg', '-vn',
                '-ss', '%0.1f' % (chunk[FIELD_CHUNK_POSITION]),
                '-t', '%0.1f' % (chunk[FIELD_CHUNK_DURATION]),
                '-i', chunk[FIELD_CHUNK_TRACK][FIELD_TRACK_FILE],
                ]

        audio_filter = 'loudnorm'

        # add modifications
        if chunk[FIELD_CHUNK_MODIFICATION]:
            modification = chunk[FIELD_CHUNK_MODIFICATION]

            # echo
            if modification[FIELD_MODIFICATION_NAME] == MODIFICATION_NAME_ECHO:
                delay = modification[FIELD_MODIFICATION_ECHO_DELAY]
                decay = modification[FIELD_MODIFICATION_ECHO_DECAY]
                out_gain = round(1.0 / (0.8 + decay), 2)
                audio_filter += f',aecho=0.8:{out_gain:0.2f}:{delay}:{decay:0.1f}'

            # high-pass
            elif modification[FIELD_MODIFICATION_NAME] == MODIFICATION_NAME_HIGH_PASS:
                freq = modification[FIELD_MODIFICATION_HIGH_PASS]
                audio_filter += f',highpass=f={freq}'

            # low-pass
            elif modification[FIELD_MODIFICATION_NAME] == MODIFICATION_NAME_LOW_PASS:
                freq = modification[FIELD_MODIFICATION_LOW_PASS]
                audio_filter += f',lowpass=f={freq}'

            # pitch and/or tempo
            elif FIELD_MODIFICATION_PITCH in modification or FIELD_MODIFICATION_TEMPO in modification:
                audio_filter += ',rubberband=channels=together'
                if FIELD_MODIFICATION_PITCH in modification:
                    audio_filter += f':pitch={modification[FIELD_MODIFICATION_PITCH]}'
                if FIELD_MODIFICATION_TEMPO in modification:
                    audio_filter += f':tempo={modification[FIELD_MODIFICATION_TEMPO]}'

            # reverb
            elif modification[FIELD_MODIFICATION_NAME] == MODIFICATION_NAME_REVERB:
                audio_filter += ',ladspa=file=tap_reverb:tap_reverb'

        # add noise
        if chunk[FIELD_CHUNK_NOISE]:
            noise = chunk[FIELD_CHUNK_NOISE]
            typ = noise[FIELD_NOISE_TYPE]
            volume = -noise[FIELD_NOISE_SNR]

            if typ == NOISE_TYPE_SAMPLE:
                args += ['-i', noise[FIELD_NOISE_FILE]]
                audio_filter += f'[a];loudnorm'
                if volume != 0:
                    audio_filter += f',volume=volume={volume}dB'
                audio_filter += '[n];[a][n]amix=duration=first'

            else:
                color = noise[FIELD_NOISE_COLOR]
                seed = noise[FIELD_NOISE_SEED]
                duration = chunk[FIELD_CHUNK_DURATION] / chunk[FIELD_CHUNK_TEMPO]

                audio_filter += f'[a];anoisesrc=r={sample_rate}:d={duration:0.2f}:c={color}:s={seed},loudnorm'
                if volume != 0:
                    audio_filter += f',volume=volume={volume}dB'
                if noise[FIELD_NOISE_TYPE] == NOISE_TYPE_PULSATING:
                    audio_filter += f',apulsator=mode=square:offset_l=0.5:offset_r=0.5:hz=0.5:amount=1'
                audio_filter += f'[n];[a][n]amix'

        args += ['-filter_complex', audio_filter]
        args += ['-ar', str(sample_rate)]
        args += ['-ac', '2']

        if codec == 'mp3':
            # do not write ID3 and Xing tags
            args += ['-write_xing', '0', '-id3v2_version', '0']

        # add output file
        chunk_file = os.path.join(self._tmp_dir, 'chunk_%04d_%04d.%s' % (query_index, chunk[FIELD_CHUNK_INDEX], codec))
        chunk[FIELD_CHUNK_FILE] = chunk_file
        args.extend(['-y', chunk_file])

        # run ffmpeg to create the chunk
        p = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise RuntimeError('ffmpeg failed!\nCOMMAND: "%s"\nSTDOUT:\n%s\nSTDERR:\n%s\n' % (
                '" "'.join(args), p.stdout.decode(), p.stderr.decode()))

        # update the chunk duration according to the real duration of the chunk file
        duration = get_track_duration(chunk[FIELD_CHUNK_FILE])
        if duration:
            chunk[FIELD_CHUNK_QUERY_DURATION] = duration


    def _create_query(self, query_id, chunks, codec, sample_rate):
        """
        Create the query from the chunks.
        """
        filter_complex = ''

        # prepare the complex filter to merge different chunks using different merge types
        for chunk_index in range(len(chunks) - 1):
            chunk = chunks[chunk_index]
            if chunk[FIELD_CHUNK_MERGE_NEXT] == MERGE_NAME_CONCAT:
                merge_type = 'nofade'
                duration = 0
                overlap = 0
            elif chunk[FIELD_CHUNK_MERGE_NEXT] == MERGE_NAME_FADE:
                merge_type = 'tri'
                duration = chunk[FIELD_CHUNK_MERGE_NEXT_DURATION]
                overlap = 1
            elif chunk[FIELD_CHUNK_MERGE_NEXT] == MERGE_NAME_OVERLAP:
                merge_type = 'nofade'
                duration = chunk[FIELD_CHUNK_MERGE_NEXT_DURATION]
                overlap = 1
            else:
                raise RuntimeError(f'Invalid merge: {chunk[FIELD_CHUNK_MERGE_NEXT]}')

            if chunk_index == 0:
                filter_complex += '[0]'
            else:
                filter_complex += f'[{chunk_index}m];[{chunk_index}m]'
            filter_complex += f'[{chunk_index + 1}]acrossfade=d={duration}:o={overlap}:c1={merge_type}:c2={merge_type}'

        # prepare the command-line arguments
        args = ['ffmpeg', '-vn']
        for chunk in chunks:
            args += ['-i', chunk[FIELD_CHUNK_FILE]]

        args += ['-filter_complex', filter_complex]
        args += ['-ar', str(sample_rate)]
        args += ['-ac', '2']

        if codec == 'mp3':
            # do not write ID3 and Xing tags
            args += ['-write_xing', '0', '-id3v2_version', '0']

        query_file = os.path.join(self._query_dir, f'{query_id}.{codec}')
        args += ['-y', query_file]

        # run ffmpeg to create the chunk
        p = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode != 0:
            raise RuntimeError('ffmpeg failed!\nCOMMAND: "%s"\nSTDOUT:\n%s\nSTDERR:\n%s\n' % (
                '" "'.join(args), p.stdout.decode(), p.stderr.decode()))

        for chunk in chunks:
            os.remove(chunk[FIELD_CHUNK_FILE])


    def _add_query_annotations(self, query_id, chunks):
        """
        Add the annotations for the chunks of the query.
        """
        query_begin = 0
        for chunk in chunks:
            reference_begin = chunk[FIELD_CHUNK_POSITION]
            reference_end = reference_begin + chunk[FIELD_CHUNK_DURATION]
            query_end = query_begin + chunk[FIELD_CHUNK_QUERY_DURATION]

            annotation = {
                FIELD_ANNOTATION_REFERENCE_ID: chunk[FIELD_CHUNK_TRACK][FIELD_TRACK_ID],
                FIELD_ANNOTATION_QUERY_ID: query_id,
                FIELD_ANNOTATION_REFERENCE_BEGIN: int(math.floor(reference_begin)),
                FIELD_ANNOTATION_REFERENCE_END: int(math.ceil(reference_end)),
                FIELD_ANNOTATION_QUERY_BEGIN: int(math.floor(query_begin)),
                FIELD_ANNOTATION_QUERY_END: int(math.ceil(query_end)),
            }
            modification = chunk.get(FIELD_CHUNK_MODIFICATION)
            noise = chunk.get(FIELD_CHUNK_NOISE)
            for field in ANNOTATION_FIELDS:
                if field not in annotation:
                    if field in chunk:
                        if field == FIELD_ANNOTATION_TEMPO:
                            annotation[field] = round(tempo_scale_to_per_cent(chunk[field]))
                        else:
                            annotation[field] = chunk[field]
                    elif modification and field in modification:
                        if field == FIELD_ANNOTATION_PITCH:
                            annotation[field] = round(pitch_scale_to_cents(modification[field]))
                        else:
                            annotation[field] = modification[field]
                    elif noise and field in noise:
                        if field == FIELD_ANNOTATION_NOISE_FILE:
                            annotation[field] = os.path.basename(noise[field])
                        else:
                            annotation[field] = noise[field]

            self._annotations.append(annotation)

            merge_duration = chunk.get(FIELD_CHUNK_MERGE_NEXT_DURATION, 0)
            query_begin = query_end - merge_duration


    def load_track_list(self, fn):
        """
        Load the track list from the file.
        """
        with open(fn, 'r') as fr:
            reader = csv.DictReader(fr)
            for row in reader:
                row[FIELD_TRACK_DURATION] = float(row[FIELD_TRACK_DURATION])
                if row[FIELD_TRACK_DURATION] >= 10:
                    self._tracks[row[FIELD_TRACK_ID]] = row


    def have_tracks(self):
        """
        Return true if any tracks were loaded.
        """
        return len(self._tracks) > 0


    def generate_queries(self, difficulty, num_queries, seed, codec, sample_rate, dry_run):
        """
        Generate queries.

        Parameters:
            difficulty: maximum difficulty of the query chunks ('easy', 'medium', 'hard')
            num_queries: number of query chunks
            seed: random seed
            codec: audio codec of the files
            sample_rate: audio sample rate
            dry_run: do not generate query audios, just annotations
        """

        self._init_difficulty(difficulty)
        random.seed(seed)

        all_track_ids = sorted(self._tracks)

        if not num_queries:
            num_queries = 1 + int(0.15 * len(all_track_ids))

        self._error_in_thread = None

        query_index = 0
        while num_queries > 0:
            # random number of query chunks in the query file
            num_chunks = min(3 + int(random.expovariate(0.5)), max(3, num_queries))
            num_queries -= num_chunks

            # start choosing from all track IDs
            track_ids = all_track_ids.copy()

            # generate chunks
            chunks = []
            for chunk_index in range(num_chunks):
                # choose the track and remove it from the list to avoid using it for this query again
                track_index = random.randrange(len(track_ids))
                track_id = track_ids.pop(track_index)
                track = self._tracks[track_id]

                # get the random modification and noise (if any)
                modification = self._get_random_modification()
                noise = self._get_random_noise()
                tempo = modification.get(FIELD_CHUNK_TEMPO, 1) if modification else 1

                # get the duration and position of the chunk in the source track
                track_duration = track[FIELD_TRACK_DURATION]
                if track_duration < 30:
                    # For short tracks, avoid using 2 seconds from the very beginning and end of the track.
                    # Prefer longer durations by using sqrt(uniform(sqr(min), sqr(max))).
                    max_duration = track_duration - 4 + 0.5
                    chunk_duration = round(
                        math.sqrt(random.uniform(math.ceil(4.5 * 4.5), math.floor(max_duration * max_duration))), 1)
                    chunk_position = round(random.uniform(2, track_duration - chunk_duration - 2), 1)
                else:
                    # For longer tracks, avoid using 6 seconds from the very beginning and end of the track.
                    # Prefer longer durations by using sqrt(uniform(sqr(min), sqr(max))).
                    max_duration = min(30, track_duration - 12) + 0.5
                    chunk_duration = round(
                        math.sqrt(random.uniform(math.ceil(4.5 * 4.5), math.floor(max_duration * max_duration))), 1)
                    chunk_position = round(random.uniform(6, track_duration - chunk_duration - 6), 1)

                # add the chunk description to the list of chunks
                chunk = {FIELD_CHUNK_INDEX: chunk_index,
                         FIELD_CHUNK_TRACK: track,
                         FIELD_CHUNK_TEMPO: tempo,
                         FIELD_CHUNK_MODIFICATION: modification,
                         FIELD_CHUNK_NOISE: noise,
                         FIELD_CHUNK_DURATION: chunk_duration,
                         FIELD_CHUNK_POSITION: chunk_position,
                         FIELD_CHUNK_QUERY_DURATION: chunk_duration / tempo,
                         }
                chunks.append(chunk)

                # create the chunk
                if not dry_run:
                    if self._queue:
                        self._queue.put(functools.partial(self._create_chunk, chunk, codec, sample_rate, query_index))
                    else:
                        self._create_chunk(chunk, codec, sample_rate, query_index)

            # wait until the background threads creating chunks finish
            if self._queue:
                self._queue.join()

            # throw the Exception originating from the thread
            if self._error_in_thread:
                raise self._error_in_thread

            # concatenate parts
            for chunk_index in range(num_chunks - 1):
                this_chunk = chunks[chunk_index]
                next_chunk = chunks[chunk_index + 1]

                merge_type = random.choice(self._merge_choices)
                this_chunk[FIELD_CHUNK_MERGE_NEXT] = merge_type
                next_chunk[FIELD_CHUNK_MERGE_PREV] = merge_type

                if merge_type != MERGE_NAME_CONCAT:
                    merge_duration = min(round(random.uniform(2, 5), 1),
                                         this_chunk[FIELD_CHUNK_DURATION] - 0.5,
                                         this_chunk[FIELD_CHUNK_QUERY_DURATION] - 0.5,
                                         next_chunk[FIELD_CHUNK_DURATION] - 0.5,
                                         next_chunk[FIELD_CHUNK_QUERY_DURATION] - 0.5)
                    this_chunk[FIELD_CHUNK_MERGE_NEXT_DURATION] = merge_duration
                    next_chunk[FIELD_CHUNK_MERGE_PREV_DURATION] = merge_duration

            query_id = f'query{query_index:04d}'
            if not dry_run:
                self._create_query(query_id, chunks, codec, sample_rate)
            self._add_query_annotations(query_id, chunks)
            query_index += 1


    def write_annotations(self, annotation_file):
        """
        Write annotations to the annotation file.
        """
        with open(annotation_file, 'w') as fw:
            writer = csv.DictWriter(fw, ANNOTATION_FIELDS, delimiter=',', lineterminator='\n')
            writer.writeheader()
            for row in sorted(self._annotations, key=itemgetter(*ANNOTATION_SORT_FIELDS)):
                writer.writerow(row)


def main():
    # parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()

    initialize(args)

    g = QueryGenerator(args.query_dir, args.tmp_dir, args.threads)

    # load the tracks from the track lists
    for fn in args.track_list:
        g.load_track_list(fn)
    if not g.have_tracks():
        print('No tracks were loaded', file=sys.stderr)
        sys.exit(1)

    # generate queries
    try:
        g.create_threads()
        g.generate_queries(args.difficulty, args.num_queries, args.seed, args.codec, args.sample_rate, args.dry_run)
        g.write_annotations(args.annotation_file)
    finally:
        g.join_threads()

    cleanup(args)


if __name__ == '__main__':
    main()
