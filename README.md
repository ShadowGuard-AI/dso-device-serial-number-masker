# dso-device-serial-number-masker
Masks device serial numbers found in text or configuration files using regular expression matching and replacement with randomly generated alphanumeric strings of similar length and format. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

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
