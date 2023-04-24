#!/usr/bin/python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Script that creates symlinks to the reference audio files used by the query
audio files, for creating a package with all needed files.
"""

import argparse
import csv
import os

from fields import *


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('track_list', nargs='+', help='CSV file with track list')
    parser.add_argument('--annotation-file', '-a', default='annotations.csv',
                        help='Output file with annotations for generated queries')
    parser.add_argument('--reference-dir', '-r', default='references',
                        help='Directory for symlinked reference audios')

    return parser


def load_track_list(track_lists):
    """
    Load track list from the file(s).

    Returns:
        dict of tracks mapping track ID to track file
    """
    tracks = dict()

    for fn in track_lists:
        with open(fn, 'r') as fr:
            reader = csv.DictReader(fr)
            for row in reader:
                tracks[row[FIELD_TRACK_ID]] = row[FIELD_TRACK_FILE]

    return tracks


def load_references_from_annotations(fn):
    """
    Load references from annotations file.
    """
    references = set()

    with open(fn) as fr:
        reader = csv.DictReader(fr, delimiter=',')
        for row in reader:
            references.add(row[FIELD_ANNOTATION_REFERENCE_ID])

    return references


def symlink_reference_audios(references, tracks, reference_dir):
    """
    Symlink track files of the references to the reference dir.
    """
    for reference in references:
        track_file = tracks[reference]
        file_name = os.path.basename(track_file)
        dir_name = os.path.dirname(track_file)
        subdir_name = os.path.basename(dir_name)

        use_subdir = subdir_name.isnumeric()

        if use_subdir:
            target_dir = os.path.join(reference_dir, subdir_name)
        else:
            target_dir = reference_dir

        if os.path.isabs(track_file):
            source_fn = track_file
        else:
            source_fn = os.path.relpath(track_file, target_dir)

        os.makedirs(target_dir, exist_ok=True)
        os.symlink(source_fn, os.path.join(target_dir, file_name))


def main():
    # parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()

    tracks = load_track_list(args.track_list)
    references = load_references_from_annotations(args.annotation_file)
    symlink_reference_audios(references, tracks, args.reference_dir)


if __name__ == '__main__':
    main()
