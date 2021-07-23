from zlib import decompress
from utils.files import get_full_path
import core.screens.game
import pygame

objs = []


def load_map(map_name):
    global objs
    map_data = open(get_full_path(map_name + '.lvl', file_type='maps'), 'rb').read()
    map_decom = decompress(map_data).decode('utf-8')
    content = map_decom.splitlines()
    content = [lines.strip() for lines in content]
    for element in content:
        element_list = element.split()
        # ID:     0
        # TYPE:   1
        # GROUP:  2
        # POS_X:  3
        # POX_Y:  4
        # SIZE_W: 5
        # SIZE_H: 6


        """
        Types: 
        | 1 - WorldRectangleRigid  | 
        | 2 - WorldRectangleSensor |
        """

        if element_list[0][0] != "[":
            type_obj = 1
            if element_list[1] == "WorldRectangleRigid":
                type_obj = 1
            elif element_list[1] == "WorldRectangleSensor":
                type_obj = 2
            elif element_list[1] == "MetalCrate":
                type_obj = 3
            elif element_list[1] == "FireLight":
                type_obj = 4
            elif element_list[1] == "LightSource":
                type_obj = 5

            size_h = 0
            size_w = 0

            if type_obj != 3 and type_obj != 4 and type_obj != 5:
                size_h = int(element_list[6])
                size_w = int(element_list[5])

            pos_y = int(element_list[4])
            pos_x = int(element_list[3])

            group = core.screens.game.obstacles_gr # Default

            if element_list[2] == "obstacles_gr":
                group = core.screens.game.obstacles_gr

            if type_obj == 1:
                obj = core.screens.game.WorldRectangleRigid(group, pos=[pos_x, pos_y], size=[size_w, size_h])
                objs.append(obj)
            if type_obj == 2:
                obj = core.screens.game.WorldRectangleSensor(group, pos=[pos_x, pos_y], size=[size_w, size_h], layer=int(element_list[7]))
                objs.append(obj)
            if type_obj == 3:
                obj = core.screens.game.MetalCrate(group, pos=[pos_x, pos_y])
                objs.append(obj)
            if type_obj == 4:
                if len(element_list) > 8:
                    obj = core.screens.game.addLight(core.screens.game.FireLight, [pos_x, pos_y], int(element_list[5]),
                                                     element_list[6], int(element_list[7]), element_list[8])
                else:
                    obj = core.screens.game.addLight(core.screens.game.FireLight, [pos_x, pos_y], int(element_list[5]),
                                                     element_list[6], int(element_list[7]))
                objs.append(obj)
            if type_obj == 5:
                if len(element_list) > 8:
                    obj = core.screens.game.addLight(core.screens.game.LightSource, [pos_x, pos_y], int(element_list[5]),
                                                     element_list[6], int(element_list[7]), element_list[8])
                else:
                    obj = core.screens.game.addLight(core.screens.game.LightSource, [pos_x, pos_y], int(element_list[5]),
                                                     element_list[6], int(element_list[7]))
                objs.append(obj)
        else:
            tmp = element_list[0].replace("[", "")
            tmp = tmp.replace("]", "")
            tmp_array = tmp.split(":")

            if tmp_array[3] == "float":
               setattr(objs[int(tmp_array[0])], tmp_array[1], float(tmp_array[2]))
            elif tmp_array[3] == "str":
               setattr(objs[int(tmp_array[0])], tmp_array[1], tmp_array[2])
