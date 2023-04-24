#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Script preparing the reference track list from the given set of media files.
"""

import argparse
import csv
import sys

from util import get_track_duration, get_track_id_from_file_name


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('track', nargs='*', help='Track file name(s)')
    parser.add_argument('--input', '-i', help='File name with the input list of media files')
    parser.add_argument('--output', '-o', required=True, help='File name for the output CSV')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    if not args.input and not args.track:
        print('Track file name(s) or --input LIST must be specified', file=sys.stderr)
        print(file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)

    tracks = dict()

    # read the input list of media files
    if args.input:
        with open(args.input, 'rt') as fr:
            for line in fr:
                track_file = line.rstrip()
                args.track.append(track_file)

    # prepare the track list, including durations
    for track_file in args.track:
        duration = get_track_duration(track_file)
        if not duration:
            continue

        track_id = get_track_id_from_file_name(track_file)
        tracks[track_id] = {
            'track_id': track_id,
            'track_file': track_file,
            'track_duration': duration,
            }

    # write the track list
    with open(args.output, 'w') as fw:
        output_fields = ['track_id', 'track_file', 'track_duration']
        writer = csv.DictWriter(fw, output_fields, lineterminator='\n')
        writer.writeheader()
        for track_id in sorted(tracks):
            row = tracks[track_id]
            writer.writerow(row)


if __name__ == '__main__':
    main()
