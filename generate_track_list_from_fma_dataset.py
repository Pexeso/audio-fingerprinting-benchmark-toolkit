#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Script preparing the reference track list for Audio Fingerprinting Benchmark Toolkit
from the FMA dataset.
"""

import argparse
import csv
import os.path
import sys

from util import get_track_duration


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('input', help='File name of input list (fma_metadata/raw_tracks.csv from FMA dataset)')
    parser.add_argument('output', help='File name for the output list')
    parser.add_argument('--fma-path', '-f', default='', help='Path to the FMA dataset track files')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    # set of allowed licenses
    licenses = {'by-sa', 'by', 'cc-zero', 'publicdomain',
                'http://artlibre.org/licence/lal/en',
                'http://creativecommons.org/licenses/sampling+/1.0/'}

    output_data = []

    # read the input file with the FMA track list
    with open(args.input, 'rt') as fr:
        reader = csv.DictReader(fr, delimiter=',')
        for row in reader:
            # check the license
            lic = os.path.splitext(os.path.basename(row['license_image_file_large']))[0]
            if not lic:
                lic = row['license_url']
            if lic not in licenses:
                continue

            # check that the track file exists
            track_id = int(row['track_id'])
            track_file = os.path.join(args.fma_path, f'{track_id//1000:03}', f'{track_id:06}.mp3')
            if not os.path.exists(track_file):
                continue
            row['track_file'] = track_file
            row['track_id'] = f'{track_id:06}'

            # find out the duration of the media file, because track_duration can't be trusted
            track_duration = get_track_duration(track_file)
            if not track_duration:
                continue
            if track_duration < 10:
                continue
            row['track_duration'] = track_duration

            output_data.append(row)

    # write the output file
    if output_data:
        with open(args.output, 'wt') as fw:
            writer = csv.DictWriter(fw, output_data[0].keys(), delimiter=',', lineterminator='\n')
            writer.writeheader()
            for row in output_data:
                writer.writerow(row)
    else:
        print('No suitable input tracks exist!', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
