import argparse
import re
import logging
import random
import string
import os
import sys
from pathlib import Path
import chardet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a default set of serial number patterns.  These can be overridden via CLI.
DEFAULT_SERIAL_PATTERNS = [
    r"[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}",  # UUID-like, any case
    r"SN:[A-Za-z0-9]{5,}",  # Labelled, example: SN:ABCDEFGHIJ or SN:abc12345
    r"SN-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+",  # Hyphenated, example: SN-12345-ABCDE
    r"(?:Serial|SN)[:\s][A-Za-z0-9]{5,}",  # Shorter labelled serial
    r"[A-Za-z0-9]{4,}(?:-[A-Za-z0-9]{4,})+",  # Hyphenated or segmented serial
    r"[A-Za-z0-9]{15,20}",  # Long serial, any case
    r"\b(?=[A-Za-z0-9]{10}\b)(?=[A-Za-z0-9]*[0-9])(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{10}\b",  # Plain 10 character serial
]

def generate_random_string(length):
    """
    Generates a random alphanumeric string of the specified length.

    Args:
        length (int): The length of the string to generate.

    Returns:
        str: A random alphanumeric string.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def mask_value_preserving_format(value):
    """Mask one value character by character, keeping separators in place."""
    out = []
    for ch in value:
        if ch.isdigit():
            out.append(random.choice(string.digits))
        elif ch.isupper():
            out.append(random.choice(string.ascii_uppercase))
        elif ch.islower():
            out.append(random.choice(string.ascii_lowercase))
        else:
            out.append(ch)
    return ''.join(out)


def mask_serial_number(match):
    """
    Masks a matched serial number with a random string of the same length and character types.

    Args:
        match (re.Match): The matched serial number.

    Returns:
        str: The masked serial number.
    """
    matched_string = match.group(0)
    masked_string = mask_value_preserving_format(matched_string)
    logging.debug(f"Masking a serial value of length {len(matched_string)}")
    return masked_string


def mask_serial_numbers_in_text(text, serial_patterns):
    """
    Masks serial numbers in a given text using the provided regular expression patterns.

    Args:
        text (str): The text to process.
        serial_patterns (list): A list of regular expression patterns to match serial numbers.

    Returns:
        str: The text with serial numbers masked.
    """
    compiled = []
    for pattern in serial_patterns:
        try:
            compiled.append(re.compile(pattern))
        except re.error as e:
            logging.error(f"Invalid regular expression: {pattern} - {e}")
            return None, 0
    # Single pass over the original text: collect non overlapping spans from
    # every pattern first, so a later pattern can never remask a replacement.
    spans = []
    claimed = []
    for regex in compiled:
        for m in regex.finditer(text):
            if m.start() == m.end():
                continue
            if any(m.start() < end and start < m.end() for start, end in claimed):
                continue
            claimed.append((m.start(), m.end()))
            spans.append((m.start(), m.end()))
    spans.sort()
    cache = {}
    parts = []
    pos = 0
    for start, end in spans:
        original = text[start:end]
        if original not in cache:
            cache[original] = mask_value_preserving_format(original)
        parts.append(text[pos:start])
        parts.append(cache[original])
        pos = end
    parts.append(text[pos:])
    logging.debug(f"Masked {len(spans)} serial value(s)")
    return ''.join(parts), len(spans)


def process_file(input_file, output_file, serial_patterns):
    """
    Processes a file, masking serial numbers and writing the output to another file.

    Args:
        input_file (str): The path to the input file.
        output_file (str): The path to the output file.
        serial_patterns (list): A list of regular expression patterns to match serial numbers.

    Returns:
        bool: True on success, False on failure
    """

    if Path(input_file).resolve() == Path(output_file).resolve():
        logging.error("Output file resolves to the input file; refusing in place output.")
        return False

    try:
        with open(input_file, 'rb') as f:
            raw_data = f.read()
            if not raw_data:
                logging.error(f"Input file is empty: {input_file}")
                return False
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            if encoding is None:
                logging.error(f"Failed to detect encoding for file: {input_file}.  Skipping.")
                return False # Indicate failure

            try:
                text = raw_data.decode(encoding)
            except UnicodeDecodeError as e:
                logging.error(f"Error decoding file {input_file} with encoding {encoding}: {e}.  Skipping.")
                return False  #Indicate failure

    except FileNotFoundError:
        logging.error(f"Input file not found: {input_file}")
        return False # Indicate failure
    except Exception as e:
        logging.error(f"Error reading input file: {input_file} - {e}")
        return False # Indicate failure

    masked_text, masked_count = mask_serial_numbers_in_text(text, serial_patterns)

    if masked_text is None: # Error occurred during masking
        return False

    if masked_count == 0:
        logging.error("No serial numbers were masked; no output written.")
        return False

    try:
        with open(output_file, 'w', encoding=encoding) as f:
            f.write(masked_text)
        logging.info(f"Successfully processed: {input_file} -> {output_file}")
        return True #Indicate success
    except Exception as e:
        logging.error(f"Error writing to output file: {output_file} - {e}")
        return False # Indicate failure


def setup_argparse():
    """
    Sets up the argument parser.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(description="Masks device serial numbers in files.")
    parser.add_argument("-i", "--input", dest="input_file", required=True, help="The input file to process.")
    parser.add_argument("-o", "--output", dest="output_file", required=True, help="The output file to write to.")
    parser.add_argument("-p", "--patterns", dest="patterns", nargs='+', default=DEFAULT_SERIAL_PATTERNS,
                        help="Regular expression patterns to match serial numbers. Defaults to common patterns.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")

    return parser

def main():
    """
    Main function.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Debug mode enabled.")

    input_file = args.input_file
    output_file = args.output_file
    serial_patterns = args.patterns

    # Input validation:  Basic file existence check
    if not os.path.exists(input_file):
        logging.error(f"Input file does not exist: {input_file}")
        sys.exit(1)

    if not process_file(input_file, output_file, serial_patterns):
        logging.error("Serial number masking failed. Check the logs for details.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()