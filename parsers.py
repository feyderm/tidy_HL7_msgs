'''
Parsers
'''

import re
import itertools
import numpy as np
from .helpers import concat

def parse_msgs(loc_txt, msgs):
    '''
    Parse messages for a given location

    Examples:
        >>> msg1 = '...AL1|3|DA|1545^MORPHINE^99HIC|||20080828|||\n...'
        >>> msg2 = '...AL1|1|DRUG|00000741^OXYCODONE||HYPOTENSION\n...'
        >>> parse_msgs("AL1.3.1", [msg1, msg2])
        >>> [['1545'], ['00000741']]

        >>> # multiple segments per message
        >>> seg_1 = '...AL1|1|DRUG|00000741^OXYCODONE||HYPOTENSION\n'
        >>> seg_2 = 'AL1|2|DRUG|00001433^TRAMADOL||SEIZURES~VOMITING\n...'
        >>> msg3 = seg_1 + seg_2
        >>> parse_msgs("AL1.3.1", [msg1, msg3])
        >>> [['1545'], ['00000741', '00001433']]

    Args:
        loc_txt: string of location to parse
        msgs: list(string)

    Returns:
        list(list(string))
    '''
    loc = parse_loc_txt(loc_txt)
    parser = get_parser(loc)
    return list(map(parser, msgs))

def parse_loc_txt(loc_txt):
    '''
    Parse HL7 message location

    Examples:
        >>> parse_loc_txt('PR1.3')
        {'seg': 'PR1', 'field': 3, 'depth': 2}

        >>> parse_loc_txt('DG1.3.1')
        {'seg': 'DG1', 'field': 3, 'comp': 0, 'depth': 3}

    Args:
        loc_txt: string of location

    Returns:
        Dictionary of location attributes and parsed elements

    Raises:
        ValueError if location syntax is incorrect
    '''
    loc = {}
    loc_split = loc_txt.split(".")
    loc['depth'] = len(loc_split)

    if loc['depth'] not in [2, 3]:
        raise ValueError(
            "Syntax of location must be either '<segment>.<field>' or "
            "'<segment>.<field>.<component>'"
        )

    loc['seg'] = loc_split[0]
    loc['field'] = int(loc_split[1])

    if loc['seg'] == "MSH":
        loc['field'] -= 1

    if loc['depth'] == 3:
        loc['comp'] = int(loc_split[2]) - 1

    return loc

def get_parser(loc):
    '''
    Higher-order function to parse a location from an HL7 message

    Example:
        >>> msg = '...AL1|3|DA|1545^MORPHINE^99HIC|||20080828|||\n...'
        >>> parse_allergy_type = get_parser("AL1.2")
        >>> parse_allergy_type(msg)
        >>> ['DA']

        >>> parse_allergy_code_text = get_parser("AL1.3.2")
        >>> parse_allergy_code_text(msg)
        >>> ['MORPHINE']

        >>> seg_1 = '...AL1|3|DA|1545^MORPHINE^99HIC|||20080828|||\n'
        >>> seg_2 = 'AL1|4|DA|1550^CODEINE^99HIC|||20101027|||\n...'
        >>> msg_2 = seg_1 + seg_2
        >>> parse_allergy_code_text(msg_2)
        >>> ['MORPHINE', 'CODEINE']

    Args:
        loc: dict of location attributes and values

    Returns:
        Function to parse an HL7 message at a given location
    '''
    def parser(msg):
        '''
        Parse an HL7 message

        Args:
            msg: string

        Returns:
            list(string)
        '''
        assert loc['depth'] in [2, 3]

        field_sep, comp_sep = list(msg)[3:5]

        seg_re = loc['seg'] + re.escape(field_sep) + '.*(?=\\n)'
        segs = re.findall(seg_re, msg)

        data = []
        for seg in segs:
            seg_split = seg.split(field_sep)
            if loc['depth'] == 2:
                try:
                    field_val = seg_split[loc['field']]
                    data.append(field_val)
                except IndexError:
                    data.append(np.nan)
            else:
                try:
                    field_val = seg_split[loc['field']]
                    comp_val = field_val.split(comp_sep)[loc['comp']]
                    data.append(comp_val)
                except IndexError:
                    data.append(np.nan)
        return data
    return parser

def parse_msg_id(id_locs_txt, msgs):
    '''
    Parse message IDs from raw HL7 messages

    The message identifier is a concatination of each ID location, which must
    be a single value for each message (i.e. the location must be for a
    segment found only once in a message). Returns a single string per
    message. Its value must be unique for each message because it is used to
    join data elements within a message.

    Example:
        >>> parse_msg_id(['MSH.7', 'PID.3.1', 'PID.3.4'], msgs)
        ['Facility1,68188,1719801063', Facility2,588229,1721309017', ... ]

    Args:
        id_locs_txt: list(string)
        msgs: list(string)

    Returns:
        list(string)

    Raises:
        RuntimeError if a location has multiple values
        RuntimeError if message IDs are not unique
    '''
    ids_per_loc = list(map(
        parse_msgs,
        id_locs_txt,
        itertools.repeat(msgs)
    ))

    are_loc_ids_single = (
        [all([len(id_val) == 1 for id_val in loc_ids]) for loc_ids in ids_per_loc]
    )

    if not all(are_loc_ids_single):
        raise RuntimeError(
            "One or more ID locations have multiple values per message: {id_locs}. ".format(
                id_locs=", ".join(itertools.compress(id_locs_txt, are_loc_ids_single))
            )
        )

    concatted = concat(ids_per_loc)

    if len(set(concatted)) != len(msgs):
        raise RuntimeError("Messages IDs are not unique")

    return concatted
