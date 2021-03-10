from openal import *
from utils.files import load_sound


class AudioManager:
    """Вот тут вот ебани описание класса пожалуйста.
    Можешь на русском, я перевду потом"""

    def __init__(self):
        pyoggSetStreamBufferSize(4096*4)
        oalSetStreamBufferCount(4)
        self.audioBuff1: SourceStream = oalStream(load_sound('null.ogg'))
        self.audioBuff2: SourceStream = oalStream(load_sound('null.ogg'))
        self.audioBuff3: SourceStream = oalStream(load_sound('null.ogg'))

        self.audioBuff1_currentSound = ''
        self.audioBuff2_currentSound = ''
        self.audioBuff3_currentSound = ''

    def __del__(self):
        self.audioBuff1.stop()
        self.audioBuff2.stop()
        self.audioBuff3.stop()
        oalQuit()

    def play_sound(self, sound):
        sound_to_play = load_sound(sound)

        if not self.audioBuff1.get_state() == AL_PLAYING:
            self.audioBuff1 = oalStream(sound_to_play)
            self.audioBuff1.play()
            self.audioBuff1_currentSound = sound
            return

        if not self.audioBuff2.get_state() == AL_PLAYING:
            self.audioBuff2 = oalStream(sound_to_play)
            self.audioBuff2.play()
            self.audioBuff2_currentSound = sound
            return

        if not self.audioBuff3.get_state() == AL_PLAYING:
            self.audioBuff3 = oalStream(sound_to_play)
            self.audioBuff3.play()
            self.audioBuff3_currentSound = sound
            return

    def stop_sound(self, sound):
        if self.audioBuff1_currentSound == sound:
            self.audioBuff1.stop()
            return

        if self.audioBuff2_currentSound == sound:
            self.audioBuff2.stop()
            return

        if self.audioBuff3_currentSound == sound:
            self.audioBuff3.stop()
            return

    def stop_all_sounds(self):
        self.audioBuff1.stop()
        self.audioBuff2.stop()
        self.audioBuff3.stop()

    def update(self):
        if self.audioBuff1.get_state() == AL_PLAYING:
            self.audioBuff1.update()

        if self.audioBuff2.get_state() == AL_PLAYING:
            self.audioBuff2.update()

        if self.audioBuff3.get_state() == AL_PLAYING:
            self.audioBuff3.update()
