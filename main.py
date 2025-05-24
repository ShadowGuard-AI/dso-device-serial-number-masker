import argparse
import re
import logging
import random
import string
import os
import chardet

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define a default set of serial number patterns.  These can be overridden via CLI.
DEFAULT_SERIAL_PATTERNS = [
    r"[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}",  # UUID-like
    r"SN:[A-Z0-9]{10}",  # Example: SN:ABCDEFGHIJ
    r"[A-Z0-9]{15,20}", # Example: a long alphanumeric serial
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


def mask_serial_number(match):
    """
    Masks a matched serial number with a random string of the same length and character types.

    Args:
        match (re.Match): The matched serial number.

    Returns:
        str: The masked serial number.
    """
    matched_string = match.group(0)
    masked_string = generate_random_string(len(matched_string))
    logging.debug(f"Masking '{matched_string}' with '{masked_string}'")
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
    masked_text = text
    for pattern in serial_patterns:
        try:
            masked_text = re.sub(pattern, mask_serial_number, masked_text)
        except re.error as e:
            logging.error(f"Invalid regular expression: {pattern} - {e}")
            return None # Indicate failure
    return masked_text


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

    try:
        with open(input_file, 'rb') as f:
            raw_data = f.read()
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

    masked_text = mask_serial_numbers_in_text(text, serial_patterns)

    if masked_text is None: # Error occurred during masking
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
        return

    if not process_file(input_file, output_file, serial_patterns):
        #process_file returns False on failure
        logging.error("Serial number masking failed. Check the logs for details.")


if __name__ == "__main__":
    main()