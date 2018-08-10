# motorpng.py

Retro png sprite sheet slicing utility

Divides an indexed palette png image into smaller tiles and converts them to pixels packed into bytes, writing the output to Motorola assembler FCB statements, or raw bytes, or individual png files.

Optionally slices the image first into 'big tiles', giving flexibility in converting images containing compound sprites.

Colour indices within the range covered by the output depth are copied unmodified to the output. i.e colour zero in the source image becomes colour zero in the output. The actual colours in the palette have no effect on the output.

Any colours outside of the range permitted by the output depth are converted to colour index zero.

Optionally generated masks convert out of range colours to the max allowed index and all other colours become index zero.

Output bit depth is one or two bits per pixel.

This was originally written to convert images for use in retro games, particularly for old Dragon and Tandy TRS80 CoCos.


## Requirements

Python 3

Also requires pypng available from here:

https://github.com/drj11/pypng

Download ```png.py``` and place in the same folder as ```motorpng.py```


## Examples

```motorpng.py input.png -x 12 -y 12 -m -f output.s```

Slices up ```input.png``` into 12x12 pixel tiles, also generating masks, writing the output as Motorola FCB statements to the file ```output.s```

```motorpng.py -h```

Get help on options
