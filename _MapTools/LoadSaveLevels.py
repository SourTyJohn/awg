from easygui import filesavebox, fileopenbox
from os.path import basename
from ast import literal_eval


def save(geometry, objects):
    try:
        name = filesavebox(filetypes=["*.txt"], default="*.txt")

        data = {
            'base': {'name': basename(name), 'size': [1, 1], 'tex_packs': set()},
            'geometry': [],
            'objects': []
        }

        for obj in geometry.sprites():
            obj_data, tex_pack = obj.getData()

            data['base']['tex_packs'].add(tex_pack)
            data['geometry'].append(obj_data)

        for obj in objects:
            pass

        file = open(name, mode='w')
        file.write(str(data))
        file.close()

    except TypeError:
        print('error: wrong file')


def load():
    file = open(fileopenbox(filetypes=["*.txt"], default="*.txt"), mode='r', encoding='utf-8')
    data = literal_eval(file.read())

    file.close()
    return data
