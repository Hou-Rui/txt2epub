#!/usr/bin/env python

import argparse
import dataclasses
import sys
from pathlib import Path

import txt2epub


@dataclasses.dataclass
class Args:
    input_files: list[str]
    output_file: str
    title: str
    authors: list[str]


def parse_cli() -> Args:
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='A small tool to convert TXTs to EPUB')
    parser.add_argument('input_files', nargs='+', help='input TXT files')
    parser.add_argument('-o', '--output', help='output EPUB files')
    parser.add_argument('-t', '--title',
                        help='title of generated book (use the first title of input TXT by default)')
    parser.add_argument('-a', '--authors', nargs='*',
                        help='authors of generated book (use all authors of input TXT by default)')
    args = parser.parse_args(sys.argv[1:])

    if not args.output:
        if len(args.input_files) > 1:
            print('error: requires to specify output when more than 1 input file given')
            sys.exit(1)
        args.output = str(Path(args.input_files[0]).with_suffix('.epub'))
    return Args(args.input_files, args.output, args.title, args.authors)


if __name__ == '__main__':
    args = parse_cli()
    book = txt2epub.Book(args.input_files)
    if args.title:
        book.title = args.title
    if args.authors:
        book.authors = args.authors
    book.write(args.output_file)
