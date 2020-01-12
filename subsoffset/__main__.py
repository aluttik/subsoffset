#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import datetime as dt
import io
import operator as op
import re
import sys

if sys.version_info[0] == 3:
    from functools import reduce

from . import __summary__, __title__, __version__

TIMES_LINE_RE = re.compile(
    r"^(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)$"
)


def Offset(string):
    match = re.match(r"^(\d+)(h|m|s|ms)$", string)

    if match is None:
        raise ValueError

    value = int(match.group(1))
    suffix = match.group(2)

    if suffix == "h":
        return dt.timedelta(hours=value)
    if suffix == "m":
        return dt.timedelta(minutes=value)
    if suffix == "s":
        return dt.timedelta(seconds=value)
    if suffix == "ms":
        return dt.timedelta(milliseconds=value)


def _apply_offset(filename, offset, out):
    lines = []

    with io.open(filename, "r", encoding="utf-8") as fd:
        for line in fd:
            line = line.rstrip()
            match = TIMES_LINE_RE.match(line)
            if match is not None:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
                td1 = dt.timedelta(hours=h1, minutes=m1, seconds=s1, milliseconds=ms1)
                td2 = dt.timedelta(hours=h2, minutes=m2, seconds=s2, milliseconds=ms2)
                if td1 + offset < dt.timedelta(0):
                    raise Exception("Cannot have negative start time")
                td1 += offset
                td2 += offset
                time1 = str(td1).zfill(15)[:-3].replace('.', ',')
                time2 = str(td2).zfill(15)[:-3].replace('.', ',')
                line = "%s --> %s" % (time1, time2)
            lines.append(line)

    if out is None and sys.version_info[0] == 2:
        print("\n".join(lines).encode("utf-8"))
    elif out is None:
        print("\n".join(lines))
    else:
        with io.open(out, "w", encoding="utf-8-sig") as fd:
            fd.write("".join(line + "\n" for line in lines))


def add_offset(filename, offset, out):
    offset = reduce(op.add, offset)
    _apply_offset(filename, +offset, out)


def sub_offset(filename, offset, out):
    offset = reduce(op.add, offset)
    _apply_offset(filename, -offset, out)


class _SubparserHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        line = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == "A...":
            line = line.split("\n", 1)[-1]
        if line.startswith("    ") and line[4] != " ":
            line = "  " + " ".join(filter(len, line.lstrip().partition(" ")))
        return line


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        formatter_class=_SubparserHelpFormatter,
        prog=__title__,
        description=__summary__,
        usage="%(prog)s <command> [options]",
    )
    version = __title__ + " " + __version__
    parser.add_argument("-V", "--version", action="version", version=version)
    subparsers = parser.add_subparsers(title="commands")

    def create_subparser(name, function, help):
        prog = __title__ + " " + name
        p = subparsers.add_parser(name, prog=prog, help=help, description=help)
        p.set_defaults(_subcommand=function)
        return p

    p = create_subparser("add", add_offset, "Apply a positive offset to the file.")
    p.add_argument("filename", help="Subtitles file to apply offset to.")
    p.add_argument(
        "offset",
        nargs="+",
        type=Offset,
        help="Value proceeded by 'h', 'm', 's', or 'ms'.",
    )
    p.add_argument("-o", "--out", help="Subtitles file to apply offset to.")

    p = create_subparser("sub", sub_offset, "Apply a negative offset to the file.")
    p.add_argument("filename", help="Subtitles file to apply offset to.")
    p.add_argument(
        "offset",
        nargs="+",
        type=Offset,
        help="Value proceeded by 'h', 'm', 's', or 'ms'.",
    )
    p.add_argument("-o", "--out", default=None, help="File to write output to.")

    def help(command):
        if command not in parser._actions[-1].choices:
            parser.error("unknown command %r" % command)
        else:
            parser._actions[-1].choices[command].print_help()

    p = create_subparser("help", help, "show help for commands")
    p.add_argument("command", help="command to show help for")

    parsed = parser.parse_args(args=args)

    # this addresses a bug that was added to argparse in Python 3.3
    if not parsed.__dict__:
        parser.error("too few arguments")

    return parsed


def main():
    kwargs = parse_args().__dict__
    func = kwargs.pop("_subcommand")
    func(**kwargs)


if __name__ == "__main__":
    main()
