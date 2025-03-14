#!/usr/bin/env python

import argparse
import sys
from pathlib import Path

import txt2epub


def parse_cli():
    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     description='A small tool to convert TXTs to EPUB')
    parser.add_argument('inputs', nargs='+', help='input TXT files')
    parser.add_argument('-o', '--output', help='output EPUB files')
    parser.add_argument('-t', '--title',
                        help='title of generated book (use the first title of input TXT by default)')
    parser.add_argument('-a', '--authors', nargs='*',
                        help='authors of generated book (use all authors of input TXT by default)')
    args = parser.parse_args(sys.argv[1:])

    if not args.output:
        if len(args.inputs) > 1:
            print('error: requires to specify output when more than 1 input file given')
            sys.exit(1)
        args.output = str(Path(args.inputs[0]).with_suffix('.epub'))
    return args


if __name__ == '__main__':
    args = parse_cli()
    book = txt2epub.Book(args.inputs)
    if args.title:
        book.title = args.title
    if args.authors:
        book.authors = args.authors
    book.write(args.output)
