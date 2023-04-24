#!/bin/bash

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

set -eu

# Generate Audio Benchmark
# @param name name of the Audio Benchmark
# @param size size of the Audio Benchmark (number of query chunks)
# @param seed random seed for the generator
generate_audio_benchmark () {
    name="$1"
    diff="$2"
    size="$3"
    seed="$4"

    # query audios
    ./generate_query_audios.py --annotation-file "$name/annotations.csv" --query-dir "$name/queries" --difficulty "$diff" --num-queries "$size" --seed "$seed" fma_tracks.csv

    # reference audios
    ./symlink_reference_audios.py --annotation-file "$name/annotations.csv" --reference-dir "$name/references" fma_tracks.csv

    # metadata
    ln -sfn ../fma_tracks.csv "$name"

    # archive
    7za a -l "$name.zip" "$name"
}

generate_audio_benchmark pexafb_easy_small    easy     100 120230412
generate_audio_benchmark pexafb_easy_medium   easy    1000 220230412
generate_audio_benchmark pexafb_easy_large    easy   20000 320230412
generate_audio_benchmark pexafb_medium_small  medium   100 420230412
generate_audio_benchmark pexafb_medium_medium medium  1000 520230412
generate_audio_benchmark pexafb_medium_large  medium 20000 620230412
generate_audio_benchmark pexafb_hard_small    hard     100 720230412
generate_audio_benchmark pexafb_hard_medium   hard    1000 820230412
generate_audio_benchmark pexafb_hard_large    hard   20000 920230412
