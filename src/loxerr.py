from collections import namedtuple

ScanError = namedtuple("error",
                   ["filename", "content", "pos", "msg"])

ScanErrorMessages = {
    10: "Unknown symbol.",
    11: "Error parsing string: Opening quote missing.",
    12: "Error parsing string: EOF reached while parsing escape sequence.",
    13: "Error parsing string: Unknown escape sequence.",
    14: "Error parsing string: Missing closing quote.",
    15: "Invalid start character for identifier.",
    16: "Error in parsing number: Expected digit or '.'.",
    17: "Error in parsing number: No digit.",
    
    30: "Error in parsing exponent: Invalid start character.",
    31: "Error in parsing exponent: No value.",

    40: "Error: EOF reached."
}

def report(err):
    # Get the line number and offset from `pos`:
    linenum = 0
    offset = 0
    for nchars in range(err.pos):
        if err.content[nchars] == '\n':
            linenum += 1
            offset = 0
        else:
            offset += 1

    print(f"Error in {err.filename}:{linenum}:{offset}:\n",
          err.msg)
