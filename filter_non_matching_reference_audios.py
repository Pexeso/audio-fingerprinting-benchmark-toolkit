#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Script to prepare the list of non-matching reference audio files by
filtering-out the matching pairs from the input set of audios.
"""

import argparse
import collections
import csv
import sys

from fields import *


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('input', help='File name of input list of tracks')
    parser.add_argument('output', help='File name for the output list of tracks')
    parser.add_argument('--matches', '-m', help='JSON file with track matches')

    return parser


def load_track_list(fn):
    """
    Load the track list from the file.

    Returns:
        dict mapping track ID to a CSV row
    """
    tracks = dict()

    with open(fn, 'r') as fr:
        reader = csv.DictReader(fr)
        for row in reader:
            tracks[row[FIELD_TRACK_ID]] = row

    return tracks


def load_matches(fn):
    """
    Load the matches form the file.

    Returns:
        (dict mapping reference ID to a set of matching query IDs, dict of counts of matching query IDs
        for each reference ID)
    """
    matches = collections.defaultdict(set)
    counts = collections.Counter()

    with open(fn, 'r') as fr:
        reader = csv.DictReader(fr)
        for row in reader:
            reference_id = row[FIELD_ANNOTATION_REFERENCE_ID]
            query_id = row[FIELD_ANNOTATION_QUERY_ID]
            matches[reference_id].add(query_id)
            matches[query_id].add(reference_id)

    for reference_id in matches:
        counts[reference_id] = len(matches[reference_id])

    return matches, counts


def remove_matches(tracks, matches, counts):
    """
    Remove the matching tracks from the track list.
    """
    while counts:
        # select the track with the most matches
        reference_id, count = counts.most_common(1)[0]

        # remove the selected track from its matches
        for query_id in matches[reference_id]:
            counts[query_id] -= 1
            matches[query_id].remove(reference_id)
            if not matches[query_id]:
                del matches[query_id]
                del counts[query_id]

        # remove the selected track
        del tracks[reference_id]
        del matches[reference_id]
        del counts[reference_id]


def main():
    # parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()

    # load the data
    tracks = load_track_list(args.input)
    matches, counts = load_matches(args.matches)

    remove_matches(tracks, matches, counts)

    # write the output file
    if tracks:
        with open(args.output, 'wt') as fw:
            fields = list(tracks[next(iter(tracks))].keys())
            writer = csv.DictWriter(fw, fields, delimiter=',', lineterminator='\n')
            writer.writeheader()
            for _, row in sorted(tracks.items()):
                writer.writerow(row)
    else:
        print('No suitable input tracks exist!', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
