from core.Constants import TEXTURE_PACK as PACK
from utils.files import get_full_path

from os import listdir
from os.path import splitext

from PIL.Image import open as img_open
import numpy as np


EMPTY_PIXEL = [255, 255, 255, 0]
IMAGE_FORMATS = ('.png', )


def cook_all():
    print(f'-- cooking Animation Pack: {PACK}')

    path = get_full_path(PACK, file_type='anm')
    directories = listdir(path)

    for dr in directories:
        directory_path = f'{path}/{dr}'
        textures = listdir(directory_path)

        for tex in textures:
            if splitext(tex)[1] in IMAGE_FORMATS:
                rect = cook_one(f'{path}/{dr}/{tex}')
                file = open(f'{directory_path}/{splitext(tex)[0]}_dat.txt', mode='w')
                file.write(str(rect))
                file.close()

    print(f'-- Animation Pack: {PACK} cooked')


def cook_one(file):
    print(file)

    im = img_open(file)
    data = np.array(im.getdata(), dtype=np.int16)
    h, w = im.height, im.width
    data = data.reshape([h, w, 4])

    #  vertical borders
    mn = data.max(axis=0)
    empty = EMPTY_PIXEL
    bordersV = []

    find = False
    if not np.array_equal(mn[0], empty):
        bordersV.append(0)
        find = True

    for i, pixel in enumerate(mn):
        if not np.array_equal(empty, pixel):
            # left border
            if not find:
                find = True
                bordersV.append(i)

        else:
            # right border
            if find:
                find = False
                bordersV.append(i)

    #
    complete_data = []

    for x in range(0, len(bordersV), 2):
        mn = data[0:h, bordersV[x]:bordersV[x+1]].max(axis=1)

        bordersH = []

        find = False
        if not np.array_equal(mn[0], empty):
            bordersH.append(0)
            find = True

        for i, pixel in enumerate(mn):
            if not np.array_equal(empty, pixel):
                # left border
                if not find:
                    find = True
                    bordersH.append(i)

            else:
                # right border
                if find:
                    find = False
                    bordersH.append(i)

        if len(bordersH) % 2 != 0:
            bordersH.append(h)

        complete_data.append([bordersV[x], bordersH[1], bordersV[x + 1] - bordersV[x], bordersH[1] - bordersH[0]])

    return complete_data


if __name__ == '__main__':
    cook_all()
