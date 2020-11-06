from os.path import join, dirname


MAIN_DIRECTORY = dirname(dirname(__file__))
TEXTURES_DIRECTORY = join(MAIN_DIRECTORY, 'data/Textures')
SHADERS_DIRECTORY = join(MAIN_DIRECTORY, 'data/Shaders')


def get_full_path(*path):
    return join(MAIN_DIRECTORY, *path)


def get_shader_path(path):
    return join(SHADERS_DIRECTORY, path)
