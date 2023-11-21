<!-- NOTE: two spaces at the end of line mean a line break, do not remove them! -->

Audio Fingerprinting Benchmark Toolkit
======================

## Introduction

The purpose of this Audio Fingerprinting Benchmark Toolkit is evaluation of the accuracy of different audio matching solutions.
The aim of audio matching is to identify which pieces of the reference audios are present in the query audios. 
This is usually achieved by first creating a unique audio fingerprints for both the reference and query audio files, 
and then using such fingerprints to compute audio similarity confidence. 

Audio fingerprints are typically created by using audio spectral analysis methods and are unique to particular audio samples. 
Fingerprint matching attempts to measure the similarity between fingerprints created from the reference 
and the query audio samples. 

The aim of the evaluation process implemented in this toolkit is to measure how good, or how accurate any given audio 
fingerprinting and matching algorithm is. Specific evaluation metrics are used to assess the accuracy, 
which have been described in the following sections of this document.

In this toolkit, the generated query audio files and the corresponding reference audio files are provided for 
evaluation.
You may also generate your own query files using your reference audio files.

Audio Fingerprinting Benchmark Toolkit supports both the file-level evaluation for matchers that report only which files match,
and the segment-level evaluation for matchers that report also the matching ranges of the audio files.


## Basic Evaluation

### Requirements

- Python 3.6+
- Python module [portion](https://pypi.org/project/portion/)


### Data Files

The following datasets of various sizes were generated from [FMA dataset](https://github.com/mdeff/fma) using the audios with permissive licenses.
The provided datasets contain reference and query audio files created using artificially applied audio modifications and distortions.

| Size   | Difficulty | File                                                                                                                                    | Size    | Query chunks | Query audios | Reference audios |
| ------ | ---------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------: | -----------: | -----------: | ---------------: |
| small  | easy       | [pexafb_easy_small.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_easy_small.zip)       | 657 MiB |          100 |           22 |               99 |
| small  | medium     | [pexafb_medium_small.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_medium_small.zip)   | 717 MiB |          100 |           27 |              100 |
| small  | hard       | [pexafb_hard_small.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_hard_small.zip)       | 630 MiB |          100 |           22 |               99 |
| medium | easy       | [pexafb_easy_medium.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_easy_medium.zip)     | 6.8 GiB |         1000 |          221 |              960 |
| medium | medium     | [pexafb_medium_medium.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_medium_medium.zip) | 7.0 GiB |         1000 |          220 |              950 |
| medium | hard       | [pexafb_hard_medium.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_hard_medium.zip)     | 7.2 GiB |         1000 |          219 |              953 |
| large  | easy       | [pexafb_easy_large.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_easy_large.zip)       |  69 GiB |        20000 |         4491 |             9004 |
| large  | medium     | [pexafb_medium_large.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_medium_large.zip)   |  69 GiB |        20000 |         4360 |             8998 |
| large  | hard       | [pexafb_hard_large.zip](https://pexafbtpublic.blob.core.windows.net/audio-fingerprinting-benchmark-toolkit/pexafb_hard_large.zip)       |  69 GiB |        20000 |         4400 |             9044 |

The contents of each of these archives:
- `fma_tracks.csv` - FMA tracks with suitable licenses, the reference audios were randomly chosen from them
- `queries` - generated query audio files
- `references` - used reference audio files
- `annotations.csv` - annotation file describing the contents of the queries, it is used for evaluation of the found matches

The **difficulty** level influences which audio distortions may be used in the queries:
- **easy**: high-pass, low-pass, changes in pitch and/or tempo mostly <= 6%, rarely > 10%, chunks are just concatenated, noise with Signal-to-Noise-Ratio (SNR) >= +10 dB
- **medium**: all of the above, echo, changes in pitch and/or tempo mostly <= 18%, rarely > 30%, chunks merged using overlap or fade in/fade out, noise with SNR >= +5 dB
- **hard**: all of the above, reverb, changes in pitch and/or tempo mostly <= 37%, rarely > 62%, noise with SNR >= +0 dB


### Usage

- install the requirements (`pip3 install -r requirements.txt`)
- download and unzip one or more provided data files (see the [previous subsection](#data-files))
- calculate the fingerprints of reference audios and query audios using your audio fingerprinter
- calculate the matches between the reference audios and the query audios using your audio matcher
- convert the found matches to the CSV format described in the section [Matches File](#matches-file)
- run `evaluate_matches.py --annotation-file annotations.csv --matches-file matches.csv`
- check the results


## File Formats

The Audio Fingerprinting Benchmark Toolkit uses CSV files. The delimiter is a comma `,` and quote char is a double-quote `"`.


### Matches File

The audio matching software should provide a CSV file with the found matches with the following fields:

| Field             | Type    | Mandatory       | Description                                                      |
| ----------------- | ------- | --------------- | ---------------------------------------------------------------- |
| `reference_id`    | String  | yes             | ID of the reference                                              |
| `query_id`        | String  | yes             | ID of the query                                                  |
| `reference_begin` | Integer | segment matches | Beginning of the segment in the reference, in seconds, inclusive |
| `reference_end`   | Integer | segment matches | End of the segment in the reference, in seconds, exclusive       |
| `query_begin`     | Integer | segment matches | Beginning of the segment in the query, in seconds, inclusive     |
| `query_end`       | Integer | segment matches | End of the segment in the query, in seconds, exclusive           |

Each line describes one matched segment (if segments are reported), or one matched file (if segments are not reported).
The segment ranges are in the whole seconds, the interval is `[begin, end)`, i.e. the `begin` belongs to the range but the `end` does not.
The segment-level evaluation will be calculated only if the segment begin/end are present.


### Annotation File

The annotation file describes what was put into the query files by the query generator script `generate_queries.py`.
Therefore, it describes the expected matches.

It contains the following fields:

| Field                 | Type    | Field Group  | Description                                                      |
| --------------------  | ------- | ------------ | ---------------------------------------------------------------- |
| `reference_id`        | String  | track        | ID of the reference                                              |
| `query_id`            | String  | track        | ID of the query                                                  |
| `reference_begin`     | Integer | segment      | Beginning of the segment in the reference, in seconds, inclusive |
| `reference_end`       | Integer | segment      | End of the segment in the reference, in seconds, exclusive       |
| `query_begin`         | Integer | segment      | Beginning of the segment in the query, in seconds, inclusive     |
| `query_end`           | Integer | segment      | End of the segment in the query, in seconds, exclusive           |
| `tempo`               | Integer | modification | Tempo in percent of the original                                 |
| `pitch`               | Integer | modification | Pitch change in cents                                            |
| `echo_delay`          | Integer | modification | Delay of the reflected sound in milliseconds                     |
| `echo_decay`          | Float   | modification | Decay (loudness) of the reflected sound                          |
| `high_pass`           | Integer | modification | Cutoff frequency for the high-pass filter                        |
| `low_pass`            | Integer | modification | Cutoff frequency for the low-pass filter                         |
| `reverb`              | Integer | modification | 1 if reverb was applied                                          |
| `noise_type`          | String  | noise        | Noise type ('continuous', 'pulsating', or 'sample')              |
| `noise_file`          | String  | noise        | File name with the noise sample (for noise_type = 'sample')      |
| `noise_color`         | String  | noise        | Noise color ('brown', 'pink' or 'white')                         |
| `noise_seed`          | Integer | noise        | Random seed for the FFmpeg noise generator                       |
| `noise_snr`           | Integer | noise        | Signal to Noise Ratio of the noise, in decibels                  |
| `merge_prev`          | String  | connection   | Type of the merging with the previous chunk                      |
| `merge_prev_duration` | Float   | connection   | Duration of the overlap with the previous chunk, in seconds      |
| `merge_next`          | String  | connection   | Type of the merging with the next chunk                          |
| `merge_next_duration` | Float   | connection   | Duration of the overlap with the next chunk, in seconds          |


## Evaluation

The matches are evaluated by the script `evaluate_matches.py`.
The found matches must be in the CSV format, see the chapter [Matches File](#matches-file) describing the format and fields.

Some audio matching solutions may report only which files matched, some report also the pairs of segments
in the reference audio and in the query audio that matched. The evaluation script supports both modes.
The segment-level evaluation is performed only if the detected matches contain the information about the segments.

The evaluator script calculates recall (R), precision (P), F-score (F) focusing on the precision,
number of true positives (TP), false positives (FP), false negatives (FN) and unknown positives (UP) - when it cannot be determined if the positive is true or false positive.
The explanation of these terms can be found on [Wikipedia](https://en.wikipedia.org/wiki/Precision_and_recall).

The evaluator script uses the following methods to evaluate the results:
- file-level evaluation - checking if the expected file pairs matched
- segment-level evaluation similar to evaluation of Bounding Boxes,
  see the article [A Large-scale Comprehensive Dataset and Copy-overlap Aware Evaluation Protocol for Segment-level Video Copy Detection](https://arxiv.org/abs/2203.02654), chapter 4.2.
- segment-level evaluation based on segment lengths

  **Example 1**: annotation and reported match on the same reference-query pair  
  ![TP FN FP](img/tp_fp_fn.svg)
  - the upper line is a timeline for the reference audio R
  - the lower line is a timeline for the query audio Q
  - the annotated (expected) segments are blue
  - the matched segments are red
  - if the query has different tempo, the ranges are normalized before the following calculations
  - True Positive seconds TP is the minimum of the overlapped ranges  
    TP = min(40 - 30, 45 - 33) = min(10, 12) = 10
  - False Negative seconds FN is the maximum of the ranges in the annotation but not in the match  
    FN = max(30 - 15, 33 - 20) = max(15, 13) = 15
  - False Positive seconds FP is the maximum of the ranges in the match but not in the annotation  
    FP = max(45 - 40, 51 - 45) = max(5, 6) = 6
  - Recall = TP / (TP + FN) = 10 / (10 + 15) = 10 / 25 = 0.40
  - Precision = TP / (TP + FP) = 10 / (10 + 6) = 10 / 16 = 0.625

  **Example 2**: the reported match is with a different reference audio R2  
  ![Different reference](img/different_reference.svg)
  - this is not an expected match, therefore the whole match segment is a False Positive  
    FP = max(45 - 30, 51 - 33) = max(15, 18) = 18
  - nothing matched with the reference audio R1, so everything is a False Negative  
    FN = max(40 - 15, 45 - 20) = max(25, 25) = 25

  **Example 3**: query matched also refrains in the reference audio  
  ![Refrain](img/refrain.svg)
  - the chunk used in the query may contain a refrain that occurs also somewhere else in the reference audio
  - however, it is not sure that it really is a refrain and thus correct match
  - therefore the corresponding segment is calculated as Unknown Positive instead of True Positive or False Positive
  - Unknown Positive seconds UP = max(62 - 50, 45 - 33) = max(12, 12) = 12
  - False Positive seconds FP = max(65 - 62, 51 - 45) = max(3, 6) = 6

### Evaluator output

The evaluator script calculates the results for each reference-query pair.
It also aggregates these individual results to larger groups:
- all queries using the same reference audio (denoted `REF`)
- groups according to the modification, noise, or merging type (denoted `TAG`)
- overall results (denoted `TOTAL`)

By default, the results are printed to standard output (see the example below).
The evaluator script also supports output to CSV file specified by the command-line option `--output-csv-file`.

**Example output** (shortened)
```
R  93.10  P 100.00  F  99.26  TP     27  UP     16  FP      0  FN      2  query3627  053963  echo, merge_next:end, merge_prev:concat, noise:-10dB, noise:sample, pitch:exact, speed:exact, tempo:exact
R  95.45  P  95.45  F  95.45  TP     21  UP      0  FP      1  FN      1  query2485  053963  merge_next:overlap, merge_prev:concat, noise:none, tempo:small
R  96.67  P 100.00  F  99.66  TP     29  UP      1  FP      0  FN      1  query3538  053963  merge_next:concat, merge_prev:concat, noise:none, pitch:exact, speed:exact, tempo:exact
R  95.07  P  98.48  F  98.13  TP     77  UP     17  FP      1  FN      4  REF 053963
R  93.10  P 100.00  F  99.26  TP     27  UP     16  FP      0  FN      2  TAG echo
R  95.45  P  95.45  F  95.45  TP     21  UP      0  FP      1  FN      1  TAG tempo:small
R  95.07  P  98.48  F  98.13  TP     77  UP     17  FP      1  FN      4  TOTAL
```

## Generating New Query Audio Files

This section describes the process of generating new query audio files.
The provided [data files](#data-files) were created using this process.

The Audio Fingerprinting Benchmark Toolkit allows for the generation of augmented (modified) queries. 
Several types of audio modifications can be applied to query audio samples to simulate real-world use-case scenarios 
and measure the robustness of audio matching technology to such modifications. Different audio modification severity 
and control settings (e.g. cut-off frequencies, or echo delay) are used for each processed audio file.

The applied audio modifications include:
- tempo modification,
- pitch change, 
- echo, 
- reverberation,
- high and low-pass filtering, and
- noise addition.


### Requirements

- [librubberband](https://github.com/breakfastquay/rubberband)
- [ladspa](https://www.ladspa.org/) with [tap plugins](https://tomscii.sig7.se/tap-plugins/)
- [FFmpeg](https://ffmpeg.org/) built with mp3/aac decoding/encoding and the following configure options: `--enable-indev=lavfi --enable-librubberband --enable-ladspa`


### List of Reference Audio Files

First, a CSV file with the list of reference audio files must be prepared.

When using [FMA dataset](https://github.com/mdeff/fma), use the script `generate_track_list_from_fma_dataset.py`.
- The option `--fma-path=PATH` specifies the location of the fMA dataset audio files. It is a path to the `fma_full` or `fma_large` directory.
- The first argument is the path to the `fma_metadata/raw_tracks.csv` file from the FMA metadata.
- The second argument is the output file name.

When using other files that FMA dataset, use the script `generate_track_list_from_media_files.py` to generate the list of reference audio files.
- The option `--output=FILE` specifies the output file name.
- The arguments are the file names of the media files that should be used for generating the queries.

The reference audio files should **not** match each other.
In order to ensure this, match all reference audios with each other
and then use the script `filter_non_matching_reference_audios.py`
to keep only the non-matching reference audios in the list.


### Generating the Query Audios

The script `generate_query_audios.py` generates the query audio files from the list of reference audio files:
- The maximum difficulty of the generated queries may be set by the `--difficulty` parameter.
- The total number of chosen chunks is 15% of the number of reference audios, or it may be set by the `--num-queries` parameter.
- Until all chunks have been generated:
  - Randomly choose the number of chunks to put into the next query file.
  - For each chunk:
    - Randomly choose the reference audio.
    - Randomly choose the duration of the chunk and the position in the reference audio.
    - Randomly choose the modifications (none, pitch, tempo, tempo & pitch, echo, noise, reverb, high-pass, low-pass, ...) and their parameters.
    - Get the chunk from the reference audio and apply the modifications.
    - Randomly choose how to connect the chunks (concatenation, fade in/out, overlap) and their parameters.
  - Connect the chunks into a query file.
- Generate `annotations.csv` file describing the expected matches, see section [Annotation File](#annotation-file).


### Creating the Audio Fingerprinting Benchmark Toolkit Data Files

In order to create the [Data Files](#data-files), the used reference audio files must be added to the package(s).

This is done by the script `symlink_reference_audios.py`.
- The option `--annotation-file` specifies the [annotation file](#annotation-file) describing the queries.
- The option `--reference-dir` specifies the path to the directory that will contain the symlinks to the reference audio files.
- The argument(s) specify the list(s) of reference audio file(s).

Finally, the contents of the data files is zipped into one archive.

All required steps starting with [Generating the Query Audios](#generating-the-query-audios) are performed by the script `generate_audio_benchmark_datasets.sh`.
It was used to create the provided [Data Files](#data-files).
