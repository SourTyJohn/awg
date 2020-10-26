import pygame as pg
import SupFuntions as Sf
from _MapTools.LoadSaveLevels import load, save
from easygui import fileopenbox
from os.path import basename, dirname


# Main preparations
pg.init()
screen: pg.Surface = pg.display.set_mode((1366, 768))
pg.display.set_caption('TheGameMapTools')
pg.font.init()
clock = pg.time.Clock()


from _MapTools.MTTextures import *


# Sprite .Groups and sprite lists init
buttons_group = pg.sprite.Group()
buttons = {}

arrow_group = pg.sprite.GroupSingle()
workSp_group = pg.sprite.GroupSingle()

LevelObjects = pg.sprite.Group()  # Rectangles and Entities
Rectangles = pg.sprite.Group()
Entities = pg.sprite.Group()

highlight = pg.sprite.Group()

# Grid Constants and variables
MAX_GRID = 64
MIN_GRID = 1
grid = 16
GRID_COLOR = (255, 0, 0)
GRID_ALPHA = 100
MIN_GRID_DISPLAY = 8

# Rect Constants
"""

solid - Textured Shape with collision. Can be Fixed and Dynamic. 
Dynamic Solid Rectangle is affected by Physics, Fixed is not.

back - Textured Shape with no collision. Placed far from camera

front -

trigger - Non-textured Shape with no collision. 
If player touches Trigger, some event will happen

"""

RECT_TYPES = ['solid', 'background', 'front']
RECT_COLORS = {'solid': (255, 255, 0), 'back': (255, 0, 255), 'front': (0, 255, 255)}
SELECTED_RECT_COLOR = (255, 0, 50)
show_textures = 1

# Quill Data. [rect/focus, rect types: solid/back/front]
quill = ['rect', 'solid']
current_texture = textures['Devs/devs_1']


class Cursor(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.rect = pg.rect.Rect([0, 0, 2, 2])

        self.selected_objects = []
        self.selected_texture = 0
        self.selected_type = 0

        self.rectStartPoint = []

    @staticmethod
    def check_press_button():
        return pg.sprite.spritecollide(arrow, buttons_group, False, collided=pg.sprite.collide_rect)

    # Check if pressed
    def check_workspace_press(self):
        if pg.sprite.spritecollide(arrow, workSp_group, False, collided=pg.sprite.collide_rect):
            if self.rectStartPoint:
                return 'f_rect'
            return 's_rect'
        return False

    # Drawing Rectangles
    def start_drawing(self):
        self.rectStartPoint = [self.rect.center[0] // grid * grid,
                               self.rect.center[1] // grid * grid + WorkSpace.pos[1]]

    def finish_drawing(self, pos, tex_offset: bool):
        start_pos = self.rectStartPoint
        end_pos = [(pos[0] + 10) // grid * grid, (pos[1] - 10) // grid * grid + WorkSpace.pos[1]]
        size = [abs(end_pos[x] - start_pos[x]) for x in range(2)]

        self.rectStartPoint = []
        return Rectangle(start_pos, size, tex_offset)

    # Select and Drag LevelObjects
    def check_select_object(self, ctrl_pressed=False):
        clicked = pg.sprite.spritecollide(arrow, LevelObjects, False, collided=pg.sprite.collide_rect)
        if not clicked:
            return False
        obj = clicked[0]

        if not ctrl_pressed:  # You can select multiple objects if you are holding Ctrl button
            self.unSelectAll()
            self.Select(clicked[0])
        else:
            if obj.selected:
                self.unSelect(obj)
            else:
                self.Select(obj)

        return True

    def unSelect(self, obj):
        self.selected_objects.remove(obj)
        obj.selected = False

    def Select(self, obj):
        self.selected_objects.append(obj)
        obj.selected = True

    def unSelectAll(self):
        for x in self.selected_objects:
            x.selected = False
        self.selected_objects = []

    # Actions with Selected
    def deleteSelected(self):
        for obj in self.selected_objects:
            obj.kill()
        self.selected_objects = []

    def moveSelected(self, amount):
        for obj in self.selected_objects:
            obj.move(amount)


arrow: Cursor


class Rectangle(pg.sprite.Sprite):
    texture = None
    __texture_surface_show = None
    __texture_surface_grid = None
    texture_offset = None

    def __init__(self, pos, size, tex_offset=False, texture='current', rect_type='current'):
        super().__init__(Rectangles, LevelObjects)
        self.true_rect = [*pos, *size]
        self.rect = [*pos, *[x // 6 for x in size]]  # Focus collision rect
        self.selected = False

        if texture == 'current':
            texture = current_texture

        if tex_offset and arrow.selected_objects:
            tex_offset = self.relativeOffset(arrow.selected_objects[0], texture.size)
        else:
            tex_offset = (0, 0)
        self.texture_offset = tex_offset

        if rect_type == 'current':
            rect_type = quill[1]
        self.rect_type = rect_type

        self.setTextureAndOffset(texture)
        if self.texture:
            self.setTextureGrid(RECT_COLORS[self.rect_type], self.texture.size)

    def move(self, amount):
        new_pos = [self.rect[x] + amount[x] * grid for x in range(2)]

        if new_pos[0] >= 0 and new_pos[0] + self.true_rect[2] <= WorkSpace.resolution[0] and\
                new_pos[1] >= WorkSpace.pos[1] and \
                new_pos[1] + self.true_rect[3] - WorkSpace.pos[1] <= WorkSpace.resolution[1]:

            self.rect = [*new_pos, self.rect[2], self.rect[3]]
            self.true_rect = [*new_pos, self.true_rect[2], self.true_rect[3]]

    def update(self, *args):
        color = RECT_COLORS[self.rect_type]

        if show_textures:
            self.draw_texture()
        else:
            self.draw_grid()

        pg.draw.rect(screen, color, self.true_rect, 3)

        if self.selected:
            color = SELECTED_RECT_COLOR

        pg.draw.rect(screen, color, self.rect, 1 + self.selected)

    def relativeOffset(self, to, tex_size):
        offset = [0, 0]
        offset[0] = ((self.rect[0] - to.rect[0]) / tex_size[0] + to.texture_offset[0]) % 1
        offset[1] = ((self.rect[1] - to.rect[1]) / tex_size[1] + to.texture_offset[1]) % 1
        return offset

    def setTextureAndOffset(self, texture):
        self.texture = texture
        self.__texture_surface_show = None

        rect = self.true_rect

        if self.texture:
            grid_surface = pg.Surface(size=(rect[2], rect[3])).convert_alpha()
            grid_surface.fill([0, 0, 0, 0])

            offset_units = [int(self.texture_offset[x] * self.texture.size[x]) for x in range(2)]

            for x in range(int(offset_units[0]), rect[2], self.texture.size[0] // 2):
                for y in range(int(offset_units[1]), rect[3], self.texture.size[1] // 2):
                    grid_surface.blit(self.texture.image, [x, y])

            self.__texture_surface_show = grid_surface

        return False

    def setTextureGrid(self, color, size):
        rect = self.true_rect
        grid_surface = pg.Surface(size=(rect[2], rect[3])).convert_alpha()
        grid_surface.fill([0, 0, 0, 0])

        size = [x // 2 for x in size]
        offset_units = [int(self.texture_offset[x] * size[x]) for x in range(2)]

        for x in range(offset_units[0], rect[2], size[0]):
            pg.draw.line(grid_surface, (*color, GRID_ALPHA + 50), [x, offset_units[1]], [x, rect[3]], 1)

        for y in range(offset_units[1], rect[3], size[1]):
            pg.draw.line(grid_surface, (*color, GRID_ALPHA + 50), [offset_units[0], y], [rect[2], y], 1)

        self.__texture_surface_grid = grid_surface

    def draw_texture(self):
        if self.texture:
            screen.blit(self.__texture_surface_show, self.rect)

    def draw_grid(self):
        if self.texture:
            screen.blit(self.__texture_surface_grid, self.rect)

    def getData(self):
        complete_obj_data = {
            'texture': self.texture.fullname(),
            'rect': self.true_rect,
            'type': self.rect_type,
            'tex_offset': self.texture_offset,
            'rotation': 1
        }

        return complete_obj_data, self.texture.pack


class HighlightButton(pg.sprite.Sprite):
    def __init__(self, color):
        super().__init__(highlight)
        self.color = color
        self.rect = pg.rect.Rect(0, 0, 50, 50)

    def set_button(self, button):
        self.rect = button.rect.copy()

    def update(self, *args):
        super().update(*args)
        pg.draw.rect(screen, self.color, self.rect, 2)


quill_type_highlight = HighlightButton((200, 0, 0))
rect_type_highlight = HighlightButton((0, 128, 128))


class ButtonsFunctions:

    # Very basics: Files
    @classmethod
    def new_level(cls):
        pass

    @classmethod
    def load(cls):
        data = load()

        for rct in data['geometry']:
            name, tex = addTexture(*rct['texture'].split('/'))
            Rectangle(pos=rct['rect'][:2], size=rct['rect'][2:], texture=tex, tex_offset=rct['tex_offset'], rect_type=rct['type'])

    @classmethod
    def save(cls):
        save(Rectangles, Entities)

    # Grid change
    @classmethod
    def grid_m(cls):
        global grid
        if grid > MIN_GRID:
            grid //= 2

    @classmethod
    def grid_b(cls):
        global grid
        if grid < MAX_GRID:
            grid *= 2

    # Empty function. Does nothing
    @classmethod
    def empty_func(cls):
        pass

    # Quill mode change
    @classmethod
    def rect_mode(cls):
        global quill
        quill_type_highlight.set_button(buttons['rm'])
        quill[0] = 'rect'

    @classmethod
    def focus_mode(cls):
        global quill
        quill_type_highlight.set_button(buttons['fm'])
        quill[0] = 'focus'

    # Rect Quill mode change
    @classmethod
    def rect_mode_solid(cls):
        global quill
        rect_type_highlight.set_button(buttons['rs'])
        quill[1] = 'solid'

    @classmethod
    def rect_mode_back(cls):
        global quill
        rect_type_highlight.set_button(buttons['rb'])
        quill[1] = 'back'

    @classmethod
    def rect_mode_front(cls):
        global quill
        rect_type_highlight.set_button(buttons['rf'])
        quill[1] = 'front'

    # Textures
    # @classmethod
    # def add_texture_pack(cls):
    #     pack_name = diropenbox(msg='select texture pack directory',
    #                            title='open tex pack', default=Sf.get_full_path('data/Textures'))
    #     load_texPack(pack_name)

    @classmethod
    def add_texture(cls):
        global current_texture

        file_path = fileopenbox(title='select texture', default=Sf.get_full_path('data/Textures'), filetypes=["*.png"])
        pack = basename(dirname(file_path))
        texture = basename(file_path)

        name, current_texture = addTexture(pack, texture)


def addTexture(pack, texture):
    fullname = f'{pack}/{texture}'

    if fullname not in textures.keys():
        textures[fullname] = Texture(pack, texture)
    packs.add(pack)

    return fullname, textures[fullname]


class _EditorButton(pg.sprite.Sprite):
    image = Sf.load_image('GUI/button_menu_default.png')[1]
    size = [86, 16]
    image = pg.transform.scale(image, size)
    font = pg.font.SysFont('Arial Black', 12)

    def __init__(self, pos, text, func, tags=None):
        super().__init__(buttons_group)
        self.image = _EditorButton.image
        self.func = func

        self.rect = pg.rect.Rect(*pos, *_EditorButton.size)
        self.text = _EditorButton.font.render(text, True, (100, 10, 255))
        self.text_rect = pg.rect.Rect(*pos, *self.text.get_size())
        self.text_rect.center = self.rect.center

        if not tags:
            tags = []
        self.tags = tags

    def press(self):
        return self.func()

    def update(self, *args):
        super().update(*args)
        screen.blit(self.text, self.text_rect)


class WorkSpace(pg.sprite.Sprite):
    resolution = (960, 576)
    pos = (0, 18)

    def __init__(self):
        super().__init__(workSp_group)
        self.rect = pg.rect.Rect(*WorkSpace.pos, *WorkSpace.resolution)

    def grid_draw(self):
        if grid < MIN_GRID_DISPLAY:
            return

        grid_surface = pg.Surface(size=WorkSpace.resolution).convert_alpha()
        grid_surface.fill([0, 0, 0, 0])

        for x in range(0, WorkSpace.resolution[0], grid):
            pg.draw.line(grid_surface, (255, 0, 0, GRID_ALPHA), [x, 0], [x, WorkSpace.resolution[1]], 1)

        for y in range(0, WorkSpace.resolution[1], grid):
            pg.draw.line(grid_surface, (255, 0, 0, GRID_ALPHA), [0, y], [WorkSpace.resolution[0], y], 1)

        screen.blit(grid_surface, self.rect)

    def draw(self):
        pg.draw.rect(screen, (255, 0, 0), self.rect, 2)

    @staticmethod
    def draw_current_rect(pos):
        pos2 = arrow.rectStartPoint
        pos = [(pos[0] + 10) // grid * grid, (pos[1] - 10) // grid * grid + WorkSpace.pos[1]]

        if pos2:
            size = [abs(pos[x] - pos2[x]) for x in range(2)]
            pg.draw.rect(screen, RECT_COLORS[quill[1]], [*arrow.rectStartPoint, *size], 1)


workspace: WorkSpace
gridSizeRect: pg.rect.Rect


def drawGridSize():
    sur = _EditorButton.font.render(str(grid * 2), True, (100, 10, 255))
    screen.blit(sur, gridSizeRect)


WRITE_TEX_RECT = pg.rect.Rect(_EditorButton.size[0] * 11 + 26, _EditorButton.size[1] * 5 + 4, 100, 50)
DISPLAY_TEX_RECT = pg.rect.Rect(_EditorButton.size[0] * 11 + 26, _EditorButton.size[1] * 6 + 4, 128, 128)


def writeCurrentTex():
    if current_texture:
        screen.blit(_EditorButton.font.render(str(current_texture), True, (100, 10, 255)), WRITE_TEX_RECT)
        screen.blit(current_texture.image, DISPLAY_TEX_RECT)


WRITE_TEX_RECT_2 = pg.rect.Rect(_EditorButton.size[0] * 11 + 26, _EditorButton.size[1] * 20 + 4, 100, 50)
DISPLAY_TEX_RECT_2 = pg.rect.Rect(_EditorButton.size[0] * 11 + 26, _EditorButton.size[1] * 21 + 4, 128, 128)


def writeSelectedRectTex():
    if len(arrow.selected_objects) == 1:
        obj = arrow.selected_objects[0]
        tex = obj.texture

        screen.blit(_EditorButton.font.render(str(tex), True, (100, 10, 255)), WRITE_TEX_RECT_2)
        if tex:
            screen.blit(tex.image, DISPLAY_TEX_RECT_2)


def main():
    global clock, buttons, arrow, workspace, gridSizeRect
    bf = ButtonsFunctions

    buttons = {
        # main editor buttons
        'nl': _EditorButton((0, 0), 'new level', bf.new_level),
        'll': _EditorButton((_EditorButton.size[0], 0), 'load level', bf.load),
        'sl': _EditorButton((_EditorButton.size[0] * 2, 0), 'save level', bf.save),

        'gm': _EditorButton((_EditorButton.size[0] * 4, 0), '--', bf.grid_m),
        'gb': _EditorButton((_EditorButton.size[0] * 6, 0), '+', bf.grid_b),

        # select or rect buttons
        # 'fm': _EditorButton((_EditorButton.size[0] * 14, 0), 'focus', bf.focus_mode, tags=['focus_mode', ]),
        'rm': _EditorButton((_EditorButton.size[0] * 12, 0), 'rect', bf.rect_mode, tags=['rect_mode', ]),

        'rs': _EditorButton((_EditorButton.size[0] * 12, _EditorButton.size[1] + 4),
                            'solid', bf.rect_mode_solid, tags=['rect_solid', ]),
        'rb': _EditorButton((_EditorButton.size[0] * 12, _EditorButton.size[1] * 2 + 4),
                            'background', bf.rect_mode_back, tags=['rect_back', ]),
        'rf': _EditorButton((_EditorButton.size[0] * 12, _EditorButton.size[1] * 3 + 4),
                            'front', bf.rect_mode_front, tags=['rect_front', ]),

        'tpo': _EditorButton((_EditorButton.size[0] * 14, _EditorButton.size[1]), 'select tex', bf.add_texture),
    }

    rect_type_highlight.set_button(buttons['rs'])
    quill_type_highlight.set_button(buttons['rm'])

    grid_display = _EditorButton((_EditorButton.size[0] * 5, 0), '  ', bf.grid_b)
    gridSizeRect = grid_display.text_rect

    workspace = WorkSpace()
    arrow = Cursor()


def loop():
    global screen, arrow
    screen.fill((64, 64, 64))

    mouse_pos = pg.mouse.get_pos()
    if not loop_events(mouse_pos):
        return False

    # Draw and Update
    buttons_group.draw(screen)
    buttons_group.update()
    workspace.draw()
    workspace.grid_draw()
    drawGridSize()
    workspace.draw_current_rect(mouse_pos)
    # Display current textures
    writeCurrentTex()
    writeSelectedRectTex()
    # selected buttons highlighting
    highlight.update()
    Rectangles.update()

    pg.display.flip()
    clock.tick(60)
    return True


isCtrlPressed = False
isAltPressed = False


def loop_events(pos):
    global isCtrlPressed, isAltPressed, show_textures

    for event in pg.event.get():
        if event.type == pg.QUIT:
            return False

        elif event.type == pg.MOUSEBUTTONDOWN:
            arrow.rect.center = pos

            # Check buttons press
            button = arrow.check_press_button()
            if button:
                # try:
                button[0].press()

                # except Exception as error:
                #     print('\nError while ButtonPress:')
                #     print(error.__class__.__name__, error)

            # Check workspace press
            press = arrow.check_workspace_press()
            if press:
                # If quill = rect, You are able to draw Rectangles
                if event.button == 1:
                    if press == 's_rect':
                        arrow.start_drawing()
                    else:
                        arrow.finish_drawing(pos, isCtrlPressed)

                # If quill = focus, You are able to select and then drag Objects
                elif event.button == 3:
                    if arrow.rectStartPoint:
                        arrow.rectStartPoint = []
                    arrow.check_select_object(isCtrlPressed)

        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_LCTRL:
                isCtrlPressed = True
            elif event.key == pg.K_LALT:
                isAltPressed = True
            elif event.key == pg.K_DELETE:
                arrow.deleteSelected()

            elif isAltPressed:
                if event.key == pg.K_UP:
                    arrow.moveSelected([0, -1])
                elif event.key == pg.K_DOWN:
                    arrow.moveSelected([0, 1])
                elif event.key == pg.K_RIGHT:
                    arrow.moveSelected([1, 0])
                elif event.key == pg.K_LEFT:
                    arrow.moveSelected([-1, 0])

            elif event.key == pg.K_t:
                show_textures = abs(show_textures - 1)

        elif event.type == pg.KEYUP:
            if event.key == pg.K_LCTRL:
                isCtrlPressed = False
            elif event.key == pg.K_LALT:
                isAltPressed = False
    return True


if __name__ == '__main__':
    main()

    while loop():
        pass
