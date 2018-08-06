#!/usr/bin/python3

# motorpng.py - png sprite sheet slicing utility
#
# Divides an indexed palette png image into smaller tiles and
# converts them to pixels packed into bytes, writing the output
# to Motorola assembler FCB statements, or raw bytes,
# or individual png files.
#
# Any colours outside of the range permitted by the output depth
# are converted to colour index zero for images.
#
# Optionally generated masks convert out of range colours to
# the max allowed index and all other colours become index zero.
#
#
# requires pypng
#   https://github.com/drj11/pypng

import png
import os
import sys
import argparse
import itertools
import datetime


# Divides an iterable into smaller iterable slices each
# consisting of size elements.
# Requires that the slices are consumed between calls
# otherwise the first element will be returned repeatedly.
def slicer(iterable, size):
    it = iter(iterable)
    for first in it:
        yield itertools.chain([first], itertools.islice(it, size-1))


def packed_pixels(row, packing):
    return (sum(a*b for a, b in zip(pixels, packing))
            for pixels in slicer(row, len(packing)))


def fcbstr(bytedata):
    return '\tFCB ' + ','.join(('${:02X}'.format(b) for b in bytedata))


def extract_image(pixmap, maxcolour):
    f = lambda x: x if (x <= maxcolour) else 0
    return ((f(x) for x in row) for row in pixmap)


def extract_mask(pixmap, maxcolour):
    f = lambda x: 0 if (x <= maxcolour) else maxcolour
    return ((f(x) for x in row) for row in pixmap)


def output_fcb(tile, f):
    if args.mask:
        mask = extract_mask(tile, maxcolour)
        for row in extract_mask(tile, maxcolour):
            f.write(fcbstr(packed_pixels(row, packing)))
            f.write('\n')
        f.write('\n')
    for row in extract_image(tile, maxcolour):
        f.write(fcbstr(packed_pixels(row, packing)))
        f.write('\n')
    f.write('\n')


def output_raw(tile, f):
    if args.mask:
        mask = extract_mask(tile, maxcolour)
        for row in extract_mask(tile, maxcolour):
            f.write(bytearray(packed_pixels(row, packing)))
    for row in extract_image(tile, maxcolour):
        f.write(bytearray(packed_pixels(row, packing)))


def output_png(tile, fname):
    try:
        output_png.tileno += 1
    except:
        output_png.tileno = 0
    with open('{}_{}.png'.format(
        fname, output_png.tileno), 'wb') as f:
            w = png.Writer(len(tile[0]), len(tile), **tilemetadata)
            w.write(f, tile)


def write_tiles(pixmap, output_fn, filespec):
    for bslice in slicer(pixmap, args.bigheight):
        btiles_t = ((trow for trow in slicer(row, args.bigwidth))
                    for row in bslice)
        btiles = zip(*btiles_t)

        for btile in btiles:
            for slice in slicer(btile, args.height):
                # using list() allows use of len()
                tiles_t = ((list(trow)
                    for trow in slicer(row, args.width)) for row in slice)
                tiles = zip(*tiles_t)
 
                for t in tiles:
                    correct_size = ((len(t) == args.height)
                            and (len(t[0]) == args.width)) 
                    if correct_size or args.keepfrags:
                        output_fn(t, filespec)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
            description='png tile sheet to packed pixel conversion utility')

    parser.add_argument('infile', help='input png file')
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument('-f', '--fcbfile',
            help='output tiles as Motorola fcb statements to FCBFILE')
    grp.add_argument('-r', '--rawfile',
            help='output tiles to binary RAWFILE')
    grp.add_argument('-p', '--pngfile',
            help='output tiles as separate png files')
    parser.add_argument('-b', '--bitdepth', type=int,
            help='bits per pixel in output', choices=(1,2), default=2)
    parser.add_argument('-m', '--mask',
            help='generate masks', action='store_true')
    parser.add_argument('-x', '--width', type=int,
            help='width of each tile', default=0)
    parser.add_argument('-y', '--height', type=int,
            help='height of each tile', default=0)
    parser.add_argument('-w', '--bigwidth', type=int,
            help='width of big tiles', default=0)
    parser.add_argument('-z', '--bigheight', type=int,
            help='height of big tiles', default=0)
    parser.add_argument('-k', '--keepfrags', action='store_true',
            help='include undersized fragments in output')
    args = parser.parse_args()


    pr = png.Reader(filename=args.infile)
    (width, height, pixmap, metadata) = pr.read()

    if not 'palette' in metadata:
        sys.exit('Sorry, I can only process png files with indexed palettes')

    if args.width == 0:
        args.width = width

    if args.height == 0:
        args.height = height

    if args.bigwidth == 0:
        args.bigwidth = args.width

    if args.bigheight == 0:
        args.bigheight = args.height

    if args.width > args.bigwidth:
        args.width = args.bigwidth

    if args.height > args.bigheight:
        args.height = args.bigheight
    
    # determing pixel packing weights
    packing = [1<<n for n in range(0, 8, args.bitdepth)]
    packing.reverse()

    # determine max colour allowed for bit depth
    maxcolour = (1 << args.bitdepth) - 1

    tilemetadata = {k: metadata[k] for k in metadata if k != 'size'}
    #print(metadata)
    #print(tilemetadata)

    now = datetime.datetime.now()
    info = [
        'Generated by {}'.format(__file__),
        '{}'.format(now.strftime('%Y/%m/%d %H:%M:%S')),
        'Source image {} ({}x{})'.format(
            args.infile, width, height)
    ]
    if (args.width != args.bigwidth) or (args.height != args.bigheight):
        info.append('Big tile size {}x{}'.format(
            args.bigwidth, args.bigheight))
    info.extend((
        'Output size {}x{}'.format(args.width, args.height),
        'Output bit depth {}'.format(args.bitdepth)
    ))

    for line in info:
        print(line)

    if args.fcbfile:
        print('Writing fcb output to {}'.format(args.fcbfile))
        with open(args.fcbfile, 'w') as f:
            for line in info:
                f.write('; {}\n'.format(line))
            f.write('\n')
            write_tiles(pixmap, output_fcb, f)
    elif args.rawfile:
        print('Writing raw output to {}'.format(args.rawfile))
        with open(args.rawfile, 'wb') as f:
            write_tiles(pixmap, output_raw, f)
    elif args.pngfile:
        outputname, __  = os.path.splitext(args.pngfile)
        print('Writing output to png files {}_n.png'.format(outputname))
        if args.mask:
            print('Ignoring mask option')
        write_tiles(pixmap, output_png, outputname)
    else:
        print('No output option selected')

    print()
