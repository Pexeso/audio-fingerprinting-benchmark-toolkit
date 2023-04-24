#!/usr/bin/env python3

# Copyright (c) 2023 Pexeso Inc.
#
# This code is licensed under the MIT license
# found in the LICENSE file in the root directory of this source tree.

"""
Script that compares the matches found by an audio matching solution
with the expected matches in the annotation file.
"""

import argparse
import collections
import csv
import math
import portion
import re
import sys

from abc import ABC, abstractmethod
from operator import itemgetter

from fields import *
from util import *


# constants
THRESHOLD_SMALL = (1 - 0.07)
THRESHOLD_MEDIUM = (1 - 0.07 * 3)
MIN_PITCH_SMALL = math.ceil(pitch_scale_to_cents(THRESHOLD_SMALL))
MAX_PITCH_SMALL = math.floor(pitch_scale_to_cents(1 / THRESHOLD_SMALL))
MIN_PITCH_MEDIUM = math.ceil(pitch_scale_to_cents(THRESHOLD_MEDIUM))
MAX_PITCH_MEDIUM = math.floor(pitch_scale_to_cents(1 / THRESHOLD_MEDIUM))
MIN_TEMPO_SMALL = math.ceil(tempo_scale_to_per_cent(THRESHOLD_SMALL))
MAX_TEMPO_SMALL = math.floor(tempo_scale_to_per_cent(1 / THRESHOLD_SMALL))
MIN_TEMPO_MEDIUM = math.ceil(tempo_scale_to_per_cent(THRESHOLD_MEDIUM))
MAX_TEMPO_MEDIUM = math.floor(tempo_scale_to_per_cent(1 / THRESHOLD_MEDIUM))


def get_parser():
    """
    Get command-line argument parser.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument('--annotation-file', '-a', default='annotations.csv',
                        help='File with annotations')
    parser.add_argument('--matches-file', '-m', default='matches.csv',
                        help='File with matches')
    parser.add_argument('--output-csv-file', '-o',
                        help='Output CSV file for results')

    parser.add_argument('--level', '-l', choices=['files', 'seconds', 'all'], default='all',
                        help='Level of evaluation: matching files, matching seconds, all levels')

    return parser


def load_annotations_or_matches(fn):
    """
    Load annotations or matches from the file.

    Returns:
        dict mapping (query_id, reference_id) to the list of segments
    """
    items = collections.defaultdict(list)

    with open(fn) as fr:
        reader = csv.DictReader(fr, delimiter=',')
        for row in reader:
            pair = (row[FIELD_ANNOTATION_QUERY_ID], row[FIELD_ANNOTATION_REFERENCE_ID])
            items[pair].append(row)

    return items


def convert_segment_ranges(items):
    """
    Convert segment range fields to integers.

    Parameters:
        items: dict mapping (query_id, reference_id) to the list of segments
    """

    if items and FIELD_INTERVAL_REFERENCE in next(iter(items)):
        # already converted
        return

    for key in items:
        for elem in items[key]:
            elem[FIELD_INTERVAL_REFERENCE] = portion.closedopen(int(elem[FIELD_ANNOTATION_REFERENCE_BEGIN]),
                                                                int(elem[FIELD_ANNOTATION_REFERENCE_END]))
            elem[FIELD_INTERVAL_QUERY] = portion.closedopen(int(elem[FIELD_ANNOTATION_QUERY_BEGIN]),
                                                            int(elem[FIELD_ANNOTATION_QUERY_END]))


def calculate_f_score(recall, precision):
    """
    Calculate F-Score from the recall and precision.
    """

    # let the precision have 9-times greater weight than the recall
    return 10 * recall * precision / (9 * recall + precision) if recall + precision > 0 else 0


def get_interval_length(interval):
    """
    Get the length of the interval.
    """
    return sum([x.upper - x.lower for x in interval if not x.empty])


def round_towards_target(value, target):
    """
    Round the value towards the target.
    """
    if target > value:
        return math.ceil(value)
    else:
        return math.floor(value)


def get_item_as_int(d, key, default):
    """
    Get an item from the dictionary and convert it to integer.
    If the item does not exist, return the default.
    """
    value = d.get(key, default)
    value = int(value) if isinstance(value, str) and re.match(r'^[+-]?\d+$', value) else default
    return value


def get_tags_from_annotation(annotation):
    """
    Get the list of tags for distinguishing the sub-results.
    """
    tags = []

    # tempo, pitch, and speed (= tempo & pitch at the same time)
    tempo = get_item_as_int(annotation, FIELD_ANNOTATION_TEMPO, 100)
    pitch = get_item_as_int(annotation, FIELD_ANNOTATION_PITCH, 0)

    if tempo == 100:
        if pitch == 0:
            tags.append('pitch:exact')
        elif MIN_PITCH_SMALL <= pitch <= MAX_PITCH_SMALL:
            tags.append('pitch:small')
        elif MIN_PITCH_MEDIUM <= pitch <= MAX_PITCH_MEDIUM:
            tags.append('pitch:medium')
        else:
            tags.append('pitch:large')
    if pitch == 0:
        if tempo == 100:
            tags.append('tempo:exact')
            tags.append('speed:exact')
        elif MIN_TEMPO_SMALL <= tempo <= MAX_TEMPO_SMALL:
            tags.append('tempo:small')
        elif MIN_TEMPO_MEDIUM <= tempo <= MAX_TEMPO_MEDIUM:
            tags.append('tempo:medium')
        else:
            tags.append('tempo:large')
    if tempo != 100 and pitch != 0:
        if MIN_TEMPO_SMALL <= tempo <= MAX_TEMPO_SMALL:
            tags.append('speed:small')
        elif MIN_TEMPO_MEDIUM <= tempo <= MAX_TEMPO_MEDIUM:
            tags.append('speed:medium')
        else:
            tags.append('speed:large')

    echo_delay = get_item_as_int(annotation, FIELD_ANNOTATION_ECHO_DELAY, 0)
    if echo_delay:
        tags.append('echo')

    high_pass = get_item_as_int(annotation, FIELD_ANNOTATION_HIGH_PASS, 0)
    if high_pass:
        tags.append('high-pass')

    low_pass = get_item_as_int(annotation, FIELD_ANNOTATION_LOW_PASS, 0)
    if low_pass:
        tags.append('low-pass')

    reverb = get_item_as_int(annotation, FIELD_ANNOTATION_REVERB, 0)
    if reverb:
        tags.append('reverb')

    noise_type = annotation.get(FIELD_ANNOTATION_NOISE_TYPE, '')
    noise_color = annotation.get(FIELD_ANNOTATION_NOISE_COLOR, '')
    noise_snr = annotation.get(FIELD_ANNOTATION_NOISE_SNR, '')
    if noise_type == NOISE_TYPE_SAMPLE:
        tags.append('noise:sample')
    elif noise_color:
        tags.append('noise:' + noise_color)
    else:
        tags.append('noise:none')
    if noise_snr != '':
        tags.append(f'noise:{noise_snr}dB')

    merge_prev = annotation.get(FIELD_ANNOTATION_MERGE_PREV, 'begin')
    if not merge_prev:
        merge_prev = 'begin'
    tags.append('merge_prev:' + merge_prev)

    merge_next = annotation.get(FIELD_ANNOTATION_MERGE_NEXT, 'end')
    if not merge_next:
        merge_next = 'end'
    tags.append('merge_next:' + merge_next)

    return tags


class BaseResults(ABC):
    """
    Abstract base class for keeping the results for the given result set.
    """

    @abstractmethod
    def print(self, name):
        """
        Print the results with the name.
        """
        pass


    @staticmethod
    def write_header(writer):
        """
        Write the header of a CSV table.
        """
        writer.writerow(['recall', 'precision', 'f_score', 'tp', 'up', 'fp', 'fn', 'query_id', 'reference_id', 'tags'])


    @abstractmethod
    def write_row(self, writer, query_id='', reference_id=''):
        """
        Write the results to a CSV row.
        """
        pass


class RecallPrecisionResults(BaseResults):
    """
    Class for keeping the recall/precision results for the given result set.
    """

    def __init__(self):
        """ Constructor. """
        super().__init__()

        self._recalls = []  # list of recalls
        self._precisions = []  # list of precisions

        self._tags = set()


    def add(self, recall, precision, tags=set()):
        """
        Add the result.
        """
        self._recalls.append(recall)
        self._precisions.append(precision)

        self._tags.update(tags)


    def get(self):
        """
        Get the overall results.
        """
        recall = sum(self._recalls) / len(self._recalls) if self._recalls else 0
        precision = sum(self._precisions) / len(self._precisions) if self._precisions else 1
        f_score = calculate_f_score(recall, precision)
        return recall, precision, f_score


    def _format_tags(self, name):
        if self._tags:
            if name == '':
                separator = ''
            elif name == 'TAG':
                separator = ' '
            else:
                separator = '  '
            return separator + ', '.join(sorted(self._tags))

        return ''


    def print(self, name):
        """
        Print the results with the name.
        """
        recall, precision, f_score = self.get()
        tags = self._format_tags(name)
        print(f'R {100 * recall:6.2f}  P {100 * precision:6.2f}  F {100 * f_score:6.2f}  {name}{tags}')


    def write_row(self, writer, query_id='', reference_id=''):
        recall, precision, f_score = self.get()
        tags = ','.join(sorted(self._tags))
        writer.writerow([f'{100 * recall:0.2f}', f'{100 * precision:0.2f}', f'{100 * f_score:0.2f}',
                         '', '', '', '', query_id, reference_id, tags])


class PositivesNegativesResults(RecallPrecisionResults):
    """
    Class for keeping the positives/negatives results for the given result set.
    """

    def __init__(self):
        """ Constructor. """
        super().__init__()

        self._tp = 0  # True Positives
        self._up = 0  # Unknown Positives
        self._fp = 0  # False Positives
        self._fn = 0  # False Negatives


    def add(self, tp, up, fp, fn, tags=set()):
        """
        Add the result.
        """
        recall = tp / (tp + fn) if tp + fn > 0 else 0
        precision = tp / (tp + fp) if tp + fp > 0 else 1
        super().add(recall, precision, tags)

        self._tp += tp
        self._up += up
        self._fp += fp
        self._fn += fn


    def get(self):
        """
        Get the overall results.
        """
        recall, precision, f_score = super().get()
        return recall, precision, f_score, self._tp, self._up, self._fp, self._fn


    def print(self, name):
        """
        Print the results with the name.
        """
        recall, precision, f_score, tp, up, fp, fn = self.get()
        tags = self._format_tags(name)
        print(
            f'R {100 * recall:6.2f}  P {100 * precision:6.2f}  F {100 * f_score:6.2f}  TP {tp:6}  UP {up:6}  FP {fp:6}  FN {fn:6}  {name}{tags}')


    def write_row(self, writer, query_id='', reference_id=''):
        recall, precision, f_score, tp, up, fp, fn = self.get()
        tags = ','.join(sorted(self._tags))
        writer.writerow([f'{100 * recall:0.2f}', f'{100 * precision:0.2f}', f'{100 * f_score:0.2f}',
                         tp, up, fp, fn, query_id, reference_id, tags])


class BaseEvaluator(ABC):
    """
    Abstract base results evaluator.
    """

    def evaluate(self, annotations, matches):
        """
        Evaluate the matches according to annotations.

        Parameters:
            annotations: dict mapping (query_id, reference_id) to the list of annotated segments
            matches: dict mapping (query_id, reference_id) to the list of matched segments
        """

        for pair in matches:
            if pair in annotations:
                self._evaluate_pair(pair, annotations[pair], matches[pair])
            else:
                self._evaluate_pair(pair, [], matches[pair])
        for pair in annotations:
            if pair not in matches:
                self._evaluate_pair(pair, annotations[pair], [])


    @abstractmethod
    def _evaluate_pair(self, pair, annotation, match):
        """
        Evaluate the match according to the annotation.

        Parameters:
            pair: (query_id, reference_id)
            annotation: list of annotated segments
            match: match list of matched segments
        """
        pass


    def output_results(self, title, fw=None):
        """
        Output the results with the title to stdout or CSV file.
        """
        if not fw:
            # output to stdout
            print(title)

            for pair in sorted(self._pair_results):
                self._pair_results[pair].print(f'{pair[0]}  {pair[1]}')

            for ref in sorted(self._ref_results):
                self._ref_results[ref].print(f'REF {ref}')

            for tag in sorted(self._tag_results):
                self._tag_results[tag].print(f'TAG')

            self._all_results.print('')
            print()

        else:
            print(title, file=fw)

            writer = csv.writer(fw, delimiter=',', lineterminator='\n')
            self._all_results.write_header(writer)

            for pair in sorted(self._pair_results):
                self._pair_results[pair].write_row(writer, query_id=pair[0], reference_id=pair[1])

            for ref in sorted(self._ref_results):
                self._ref_results[ref].write_row(writer, reference_id=ref)

            for tag in sorted(self._tag_results):
                self._tag_results[tag].write_row(writer)

            self._all_results.write_row(writer)
            print(file=fw)


class TrackEvaluator(BaseEvaluator):
    """
    Track-level results evaluator.
    """

    def __init__(self):
        """ Constructor. """
        super().__init__()

        self._pair_results = collections.defaultdict(PositivesNegativesResults)
        self._ref_results = collections.defaultdict(PositivesNegativesResults)
        self._tag_results = collections.defaultdict(PositivesNegativesResults)
        self._all_results = PositivesNegativesResults()


    def _evaluate_pair(self, pair, annotation, match):
        """
        Evaluate the match according to the annotation.

        Parameters:
            pair: (query_id, reference_id)
            annotation: list of annotated segments
            match: match list of matched segments
        """
        b_annotation = bool(annotation)
        b_match = bool(match)

        tp = int(b_annotation and b_match)
        fn = int(b_annotation and not b_match)
        fp = int(not b_annotation and b_match)
        up = 0

        # store the results

        self._pair_results[pair].add(tp, up, fp, fn, get_tags_from_annotation(annotation[0]) if annotation else [])
        self._ref_results[pair[1]].add(tp, up, fp, fn)
        for a in range(len(annotation)):
            for tag in get_tags_from_annotation(annotation[a]):
                self._tag_results[tag].add(tp, up, fp, fn, {tag})
        self._all_results.add(tp, up, fp, fn, {'TOTAL'})


class BoundingBoxSegmentEvaluator(BaseEvaluator):
    """
    Segment-level results evaluator using the Bounding Box method.
    """

    def __init__(self):
        """ Constructor. """
        super().__init__()

        self._pair_results = collections.defaultdict(RecallPrecisionResults)
        self._ref_results = collections.defaultdict(RecallPrecisionResults)
        self._tag_results = collections.defaultdict(RecallPrecisionResults)
        self._all_results = RecallPrecisionResults()


    def _evaluate_pair(self, pair, annotation, match):
        """
        Evaluate the match according to the annotation.

        Parameters:
            pair: (query_id, reference_id)
            annotation: list of annotated segments
            match: match list of matched segments
        """

        overlaps = [[(a[FIELD_INTERVAL_REFERENCE] & m[FIELD_INTERVAL_REFERENCE],
                      a[FIELD_INTERVAL_QUERY] & m[FIELD_INTERVAL_QUERY])
                     for a in annotation]
                    for m in match]

        # calculate recall

        overlap_reference_length = 0
        overlap_query_length = 0

        for a in range(len(annotation)):
            overlap_reference_union = portion.empty()
            overlap_query_union = portion.empty()

            for m in range(len(match)):
                if not overlaps[m][a][0].empty and not overlaps[m][a][1].empty:
                    overlap_reference_union |= overlaps[m][a][0]
                    overlap_query_union |= overlaps[m][a][1]

            overlap_reference_length += get_interval_length(overlap_reference_union)
            overlap_query_length += get_interval_length(overlap_query_union)

        annotation_reference_length = sum([get_interval_length(x[FIELD_INTERVAL_REFERENCE]) for x in annotation])
        annotation_query_length = sum([get_interval_length(x[FIELD_INTERVAL_QUERY]) for x in annotation])

        recall = 1
        recall *= overlap_reference_length / annotation_reference_length if annotation_reference_length else 0
        recall *= overlap_query_length / annotation_query_length if annotation_query_length else 0

        # calculate precision

        overlap_reference_length = 0
        overlap_query_length = 0

        for m in range(len(match)):
            overlap_reference_union = portion.empty()
            overlap_query_union = portion.empty()

            for a in range(len(annotation)):
                if not overlaps[m][a][0].empty and not overlaps[m][a][1].empty:
                    overlap_reference_union |= overlaps[m][a][0]
                    overlap_query_union |= overlaps[m][a][1]

            overlap_reference_length += get_interval_length(overlap_reference_union)
            overlap_query_length += get_interval_length(overlap_query_union)

        match_reference_length = sum([get_interval_length(x[FIELD_INTERVAL_REFERENCE]) for x in match])
        match_query_length = sum([get_interval_length(x[FIELD_INTERVAL_QUERY]) for x in match])

        precision = 1
        precision *= overlap_reference_length / match_reference_length if match_reference_length else 1
        precision *= overlap_query_length / match_query_length if match_query_length else 1

        # store the results

        self._pair_results[pair].add(recall, precision, get_tags_from_annotation(annotation[0]) if annotation else [])
        self._ref_results[pair[1]].add(recall, precision)
        for a in range(len(annotation)):
            for tag in get_tags_from_annotation(annotation[a]):
                self._tag_results[tag].add(recall, precision, {tag})
        self._all_results.add(recall, precision, {'TOTAL'})


class LengthSegmentEvaluator(BaseEvaluator):
    """
    Segment-level results evaluator using the segment lengths.
    """

    def __init__(self):
        """ Constructor. """
        super().__init__()

        self._pair_results = collections.defaultdict(PositivesNegativesResults)
        self._ref_results = collections.defaultdict(PositivesNegativesResults)
        self._tag_results = collections.defaultdict(PositivesNegativesResults)
        self._all_results = PositivesNegativesResults()


    def _evaluate_pair(self, pair, annotation, match):
        """
        Evaluate the match according to the annotation.

        Parameters:
            pair: (query_id, reference_id)
            annotation: list of annotated segments
            match: match list of matched segments
        """

        overlaps = [[(a[FIELD_INTERVAL_REFERENCE] & m[FIELD_INTERVAL_REFERENCE],
                      a[FIELD_INTERVAL_QUERY] & m[FIELD_INTERVAL_QUERY])
                     for a in annotation]
                    for m in match]

        # calculate True Positives and False Negatives

        tp = 0  # True Positives
        fn = 0  # False Negatives

        for a in range(len(annotation)):
            tempo = get_item_as_int(annotation[a], FIELD_ANNOTATION_TEMPO, 100) / 100

            overlap_reference_union = portion.empty()
            overlap_query_union = portion.empty()

            for m in range(len(match)):
                if not overlaps[m][a][0].empty and not overlaps[m][a][1].empty:
                    overlap_reference_union |= overlaps[m][a][0]
                    overlap_query_union |= overlaps[m][a][1]

            annotation_reference_length = get_interval_length(annotation[a][FIELD_INTERVAL_REFERENCE])
            overlap_reference_length = get_interval_length(overlap_reference_union)
            overlap_query_length = round_towards_target(get_interval_length(overlap_query_union) * tempo,
                                                        annotation_reference_length)
            overlap_length = min(overlap_reference_length, overlap_query_length)

            tp += overlap_length

            missing_reference_union = annotation[a][FIELD_INTERVAL_REFERENCE] - overlap_reference_union
            missing_query_union = annotation[a][FIELD_INTERVAL_QUERY] - overlap_query_union
            missing_reference_length = get_interval_length(missing_reference_union)
            missing_query_length = round_towards_target(get_interval_length(missing_query_union) * tempo, 0)
            missing_length = max(missing_reference_length, missing_query_length)

            fn += missing_length

        # calculate False Positives and Unknown Positives

        up = 0  # Unknown Positives
        fp = 0  # False Positives

        for m in range(len(match)):
            overlap_reference_union = portion.empty()
            overlap_query_only_union = portion.empty()

            match_reference_length = get_interval_length(match[m][FIELD_INTERVAL_REFERENCE])
            match_query_length = get_interval_length(match[m][FIELD_INTERVAL_QUERY])

            # take the tempo from the match segment, for the case there will not be any overlapping reference segments
            tempo = match_reference_length / match_query_length if match_query_length else 1

            for a in range(len(annotation)):
                if overlaps[m][a][1]:
                    # take the tempo from some (the last) annotation segment that overlaps the match segment
                    tempo = get_item_as_int(annotation[a], FIELD_ANNOTATION_TEMPO, 100) / 100
                if not overlaps[m][a][0].empty and not overlaps[m][a][1].empty:
                    overlap_reference_union |= overlaps[m][a][0]
                overlap_query_only_union |= overlaps[m][a][1]

            # True Positives + Unknown Positives = maximum of the full overlap in the reference and the partial overlap in the query only
            overlap_reference_length = get_interval_length(overlap_reference_union)
            overlap_query_only_length = round_towards_target(get_interval_length(overlap_query_only_union) * tempo,
                                                             match_reference_length)
            overlap_length = max(overlap_reference_length, overlap_query_only_length)

            # Unknown Positives = absolute difference of the full overlap in the reference and the partial overlap in the query only
            unknown_length = abs(overlap_reference_length - overlap_query_only_length)

            # False Positives = match - (True Positives + Unknown Positives)
            surplus_reference_length = max(0, match_reference_length - overlap_length)
            surplus_query_length = round_towards_target(match_query_length * tempo,
                                                        match_reference_length) - overlap_query_only_length
            surplus_length = max(surplus_reference_length, surplus_query_length)

            fp += surplus_length
            up += unknown_length

        # store the results

        self._pair_results[pair].add(tp, up, fp, fn, get_tags_from_annotation(annotation[0]) if annotation else [])
        self._ref_results[pair[1]].add(tp, up, fp, fn)
        for a in range(len(annotation)):
            for tag in get_tags_from_annotation(annotation[a]):
                self._tag_results[tag].add(tp, up, fp, fn, {tag})
        self._all_results.add(tp, up, fp, fn, {'TOTAL'})


def main():
    # parse command-line arguments
    parser = get_parser()
    args = parser.parse_args()

    # load the data
    annotations = load_annotations_or_matches(args.annotation_file)
    matches = load_annotations_or_matches(args.matches_file)

    if args.output_csv_file:
        fw = open(args.output_csv_file, 'wt')
    else:
        fw = None

    # run the file-level evaluator
    if args.level in ['files', 'all']:
        evaluator = TrackEvaluator()
        evaluator.evaluate(annotations, matches)
        evaluator.output_results('Track results', fw)

    # run the segment-level evaluators
    if args.level in ['seconds', 'all']:
        try:
            convert_segment_ranges(matches)
            convert_segment_ranges(annotations)
        except:
            print(
                'The matches or the annotations not contain segment ranges, matching seconds evaluation is not possible!',
                file=sys.stderr)
            return

        evaluator = BoundingBoxSegmentEvaluator()
        evaluator.evaluate(annotations, matches)
        evaluator.output_results('Bounding Box Segment results', fw)

        evaluator = LengthSegmentEvaluator()
        evaluator.evaluate(annotations, matches)
        evaluator.output_results('Length Segment results', fw)

    if fw:
        fw.close()


if __name__ == '__main__':
    main()
