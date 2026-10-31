![Banner](banner.png)

# dso-device-serial-number-masker
Masks device serial numbers found in text or configuration files using regular expression matching and replacement with randomly generated alphanumeric strings of the same length and format. Masking is done character by character, so separators such as hyphens and colons stay in place, digits stay digits, and letter case is kept. Within one run, the same serial always gets the same replacement, and a masked value is never masked a second time. Default patterns cover UUID shaped values in any case, labelled serials such as SN:ABCDEFGHIJ and SN-12345-ABCDE, hyphenated and segmented serials, long serials of 15 to 20 characters in any case, and plain 10 character serials that mix letters and digits. Original serial values are never written to the log, including in debug mode. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Exit codes
- Exit 0: the run masked at least one serial and wrote the output file.
- Exit 1: any failure, including a missing or empty input file, an invalid pattern, an output path that resolves to the input file (in place output is refused and the input is left unchanged), or a run that masked zero serial values (no output is written and no success line is printed).

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-device-serial-number-masker`

## Usage
`./dso-device-serial-number-masker [params]`

## Parameters
- `-h`: Show help message and exit
- `-i`: The input file to process.
- `-o`: The output file to write to.
- `-p`: Regular expression patterns to match serial numbers. Defaults to common patterns.
- `-d`: Enable debug logging.

## License
Copyright (c) ShadowStrikeHQ
