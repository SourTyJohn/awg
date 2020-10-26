class Screen:
    def __init__(self, groups):
        self.groups = groups
        self.hero_life = True

    def init_screen(self, hero_life, first):
        pass

    def render(self, events):
        self.update_and_draw()

    def update_and_draw(self):
        for x in self.groups:
            x.update()
            x.draw()

    def close(self):
        pass
