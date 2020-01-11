import os

import imageio
import rawpy
from PIL import Image
from nm_tools import exists
raw_extensions = ['dng', 'raw', 'cr2', 'crw',
                  'erf', 'raf', 'tif', 'kdc',
                  'dcr', 'mos', 'mef', 'nef',
                  'orf', 'rw2', 'pef', 'x3f',
                  'srw', 'srf', 'sr2',
                  'arw', 'mdc', 'mrw']


def convert_to_jpeg(file_path):
    assert exists(file_path)
    f, e = os.path.splitext(file_path)
    outfile = f + ".jpg"
    if file_path != outfile:
        if e[1:].lower() in raw_extensions:
            with rawpy.imread(file_path) as raw:
                rgb = raw.postprocess(
                    no_auto_bright=True,
                    gamma=(2.222, 20.5),
                    # gamma=(2.222, 4.5),
                    # exp_shift=3.5,
                    output_bps=8)
            imageio.imsave(outfile, rgb)
        else:
            try:
                im = Image.open(file_path).save(outfile)
            except BaseException as e:
                print("cannot convert", file_path)
                print(e)
        print("converted", outfile)


if __name__ == '__main__':
    convert_to_jpeg(
        "/Volumes/for-import-on-nas/little-family-ordered/unknown/IMG_1639.CR2")
