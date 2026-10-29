"""Explicit origin of a logical channel; never infer a missing body location."""


def parse_provenance(header):
    channel = header['channel_id']
    if 'data_origin' not in header and 'source_channel_id' not in header:
        return 'measured', channel  # unchanged legacy firmware
    origin, source = header.get('data_origin'), header.get('source_channel_id')
    if (origin not in ('measured', 'simulated') or type(source) is not int
            or not 1 <= source <= 4
            or (origin == 'measured') != (source == channel)):
        raise ValueError('audio provenance')
    return origin, source
