from openal import *
from os import listdir
from utils.files import get_full_path
from core.Constants import settings
from pyogg import VorbisFile
from os.path import join, splitext


class AudioManager:
    sources: set  # list of sources OpenAl ids
    streams: dict
    streams_fade: dict

    ambient_paths: dict  # dict of longer files from .music
    buffers: dict  # dict of short files from .sounds

    listener_position: list

    __instance = None

    # AUDIO MANAGER
    def __init__(self):
        print('AudioManager initialized!')
        self.buffers = dict()
        self.sources = set()
        self.streams = {   # buffer, sound name, looping,
            'music':        [None,   '',         False],
            'ambient 0':    [None,   '',         False],
            'ambient 1':    [None,   '',         False],
        }
        #                          time, remaining time
        self.streams_fade = {key: [-1,   -1] for key in self.streams.keys()}
        self.ambient_paths = dict()

        device = alcGetString(ALC_DEVICE_SPECIFIER, ALC_DEFAULT_DEVICE_SPECIFIER)
        oalInit(device)
        alListenerf(AL_GAIN, settings['Volume'])  # Master Volume

        self.set_listener_position(0, 0)

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(AudioManager, cls).__new__(cls)
        return cls.__instance

    def destroy(self):
        self.buffers = {}
        oalQuit()

    def update_streams(self, dt):
        for key, [stream, sound, loop] in self.streams.items():
            if stream:
                if stream.get_state() == AL_PLAYING:
                    fade_m, fade_r = self.streams_fade[key]
                    if fade_m != -1:
                        if fade_r <= 0:
                            self.streams_fade[key] = [-1, -1]
                            self.clear_stream(key)
                        else:
                            stream.set_gain(stream.gain * (fade_r / fade_m))
                            self.streams_fade[key][1] -= dt

                    stream.set_position(self.listener_position)
                    stream.update()
                elif loop:
                    gain = stream.gain / settings['Volume' if sound != 'music' else 'Music Volume']
                    self.set_stream(key, sound, loop, gain)

    # LISTENER
    @staticmethod
    def set_listener_position(x, y, z=0):
        alListener3f(AL_POSITION, x, y, z)

    @staticmethod
    def set_listener_velocity(x, y, z=0):
        alListener3f(AL_VELOCITY, x, y, z)

    def update_listener(self, pos, vel):
        pos = gamePosToSoundPos(pos)
        vel = gamePosToSoundPos(vel)

        self.set_listener_position(*pos)
        self.set_listener_velocity(*vel)
        self.listener_position = pos

    def reset_listener(self):
        self.update_listener([0, 0, 0], [0, 0, 0])
        alListenerf(AL_GAIN, settings['Volume'])

    # BUFFERS
    def load_sound(self, path: str, name: str):
        buffer = ctypes.c_uint()
        alGenBuffers(1, ctypes.pointer(buffer))

        ops = VorbisFile(path)
        data = soundData(ops)
        alBufferData(buffer, *data)
        self.buffers[name] = buffer.value
        del ops

        print(f'<Sound[{buffer.value}]\tsize: {data[2].value}\tname:{name}>')

    # SOURCES
    def play_sound(self, sound, pos3f, vel3f=(0.0, 0.0, 0.0), volume=1.0):
        pos3f = gamePosToSoundPos(pos3f)
        vel3f = gamePosToSoundPos(vel3f)

        source = ctypes.c_uint()
        alGenSources(1, ctypes.pointer(source))

        alSource3f(source, AL_POSITION, *pos3f)
        alSource3f(source, AL_VELOCITY, *vel3f)
        alSourcei(source, AL_PITCH, 1)
        alSourcef(source, AL_GAIN, volume)

        alSourcei(source, AL_BUFFER, self.buffers[sound])
        alSourcePlay(source)

        self.sources.add(source.value)

    def delete_source(self, source: int):
        alDeleteSources(1, ctypes.c_ulong(source))
        self.sources.remove(source)

    def clear_empty_sources(self):
        to_delete = set()

        for s in self.sources:
            pointer = ctypes.pointer(ctypes.c_long())
            alGetSourcei(s, AL_SOURCE_STATE, pointer)
            if pointer.contents != AL_PLAYING:
                to_delete.add(s)

        while to_delete:
            s = to_delete.pop()
            self.sources.remove(s)
            alDeleteSources(1, ctypes.c_ulong(s))

    # AMBIENT-MUSIC [STREAM SOUND]
    def set_stream(self, stream: str, sound: str, looping=False, gain: float = 1.0):
        if stream in self.streams.keys():
            stream_obj = oalStream(self.ambient_paths[sound])
            self.streams[stream] = [stream_obj, sound, looping]
            gain = settings['Volume' if sound != 'music' else 'Music Volume'] * gain
            stream_obj.set_position(self.listener_position)
            stream_obj.set_gain(gain)
            stream_obj.play()

    def clear_stream(self, stream: str):
        self.streams[stream][0].destroy()
        self.streams[stream][0] = None

    def fade_stream(self, stream: str, fade: float = 1):
        #  sound will fade in <fade> seconds
        self.streams_fade[stream] = [fade, fade]


def soundData(py_ogg_file: VorbisFile):
    file = py_ogg_file
    channels = AL_FORMAT_MONO16 if file.channels == 1 else AL_FORMAT_STEREO16
    length = ctypes.c_int(file.buffer_length)
    freq = ctypes.c_int(file.frequency)
    return [channels, file.buffer, length, freq]


def loadSoundPack(name):
    print(f'\n-- loading Sound Pack: {name}')

    # SOUNDS [LOAD]
    path = get_full_path(join(name, 'sound'), file_type='snd')
    files = listdir(path)
    for file in files:
        AudioManager.load_sound(path=join(path, file), name=splitext(file)[-2])

    # SOUNDS [STREAM]
    path = get_full_path(join(name, 'music'), file_type='snd')
    files = listdir(path)
    for file in files:
        AudioManager.ambient_paths[splitext(file)[-2]] = join(path, file)

    print(AudioManager.ambient_paths)
    print(f'-- Done.\n')
    

def gamePosToSoundPos(pos):
    if len(pos) == 3:
        return [x / 128 for x in pos]
    return [x / 128 for x in (*pos, 0)]


AudioManager = AudioManager()
loadSoundPack(settings['Sound Pack'])
