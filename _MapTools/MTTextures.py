from pygame import transform
from SupFuntions import load_image


# texture_packs = {}  # pack_name: [texture, texture...]


class Texture:
    def __init__(self, pack, name):
        self.name, self.pack = name, pack
        self.repeat = self.name[0] == 'r'

        self.image = load_image(f'{pack}/{name}')[1]
        self.size = self.image.get_size()
        self.image = transform.scale(self.image, [x // 2 for x in self.size])

    def __repr__(self):
        return f'<Tex from {self.pack} Pack "{self.name}" {self.size[0]}x{self.size[1]}>'

    def kill(self):
        pass

    def fullname(self):
        return f'{self.pack}/{self.name}'


textures = {'Devs/devs_1': Texture('Devs', 'devs_1.png'), }  # pack/name: texture,
packs = set()


# def load_texPack(full_name):
#     textures = os.listdir(full_name)
#     name = os.path.basename(full_name)
#     texture_packs[name] = [Texture(name, tex) for tex in textures]
