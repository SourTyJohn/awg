from openal import *

from utils.files import get_full_path
from utils.debug import dprint
from core.math.prandom import randf
from core.Constants import \
    STN_MASTER_VOLUME, STN_GAME_VOLUME, STN_MUSIC_VOLUME, STN_SOUND_PACK, MAX_SOUND_SOURCES

from pyogg import VorbisFile
from os.path import join, splitext
from os import listdir


class AudioManager:
    sources: list  # list of sources OpenAl ids
    free_ids: set
    streams: dict
    streams_fade: dict

    ambient_paths: dict  # dict of longer files from .music
    buffers: dict  # dict of short files from .sounds

    listener_position: list

    __instance = None

    # AUDIO MANAGER
    def __init__(self):
        device = alcGetString(ALC_DEVICE_SPECIFIER, ALC_DEFAULT_DEVICE_SPECIFIER)
        oalInit(device)
        self.reset_listener()

        self.buffers = dict()

        self.streams = {   # buffer, sound name, looping,
            'music':        [None,   '',         False],
            'ambient 0':    [None,   '',         False],
            'ambient 1':    [None,   '',         False],
        }
        #                          time, remaining time
        self.streams_fade = {key: [-1,   -1] for key in self.streams.keys()}
        self.ambient_paths = dict()

        self.sources = list( )
        self.free_ids = set( )
        for key in range(MAX_SOUND_SOURCES):
            source = ctypes.c_uint()
            alGenSources(1, ctypes.pointer( source ))
            self.sources.append( source.value )
            self.free_ids.add( source.value )

        print('AudioManager initialized!')

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
                    self.check_fade_for_stream(key, stream, dt)
                    stream.set_position(self.listener_position)
                    stream.update()
                elif loop:
                    gain = stream.gain / STN_MUSIC_VOLUME
                    self.set_stream(key, sound, loop, gain)

    def check_fade_for_stream(self, stream_key, stream, dt):
        fade_m, fade_r = self.streams_fade[stream_key]
        if fade_m != -1:
            if fade_r <= 0:
                self.streams_fade[stream_key] = [-1, -1]
                self.clear_stream(stream_key)
            else:
                stream.set_gain(stream.gain * (fade_r / fade_m))
                self.streams_fade[stream_key][1] -= dt

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
        alListenerf(AL_GAIN, STN_MASTER_VOLUME)

    # BUFFERS
    def load_sound(self, path: str, name: str):
        buffer = ctypes.c_uint()
        alGenBuffers(1, ctypes.pointer(buffer))

        ops = VorbisFile(path)
        data = soundData(ops)
        alBufferData(buffer, *data)
        self.buffers[name] = buffer.value
        del ops

        dprint(f'<Sound[{buffer.value}]\tsize: {data[2].value}\tname:{name}>')

    # SOURCES
    def play_sound(self, sound: str, pos3f, vel3f=(0.0, 0.0, 0.0), volume=1.0, pitch=(1.0, 1.0)):
        """pitch:: (min, max)"""
        pos3f = gamePosToSoundPos(pos3f)
        vel3f = gamePosToSoundPos(vel3f)

        if not self.free_ids:
            return

        source = self.free_ids.pop()

        alSource3f(source, AL_POSITION, *pos3f)
        alSource3f(source, AL_VELOCITY, *vel3f)
        alSourcef(source, AL_PITCH, randf(*pitch))
        alSourcef(source, AL_GAIN, volume * STN_GAME_VOLUME)

        alSourcei(source, AL_BUFFER, self.buffers[sound])
        alSourcePlay(source)

    def delete_source(self, source: int):
        alDeleteSources(1, ctypes.c_ulong(source))
        self.free_ids.add(source)
        self.sources.remove(source)

    def clear_empty_sources(self):
        for s in self.sources:
            pointer = ctypes.pointer(ctypes.c_long())
            alGetSourcei(s, AL_SOURCE_STATE, pointer)
            if pointer.contents != AL_PLAYING:
                self.free_ids.add(s)

    # AMBIENT-MUSIC [STREAM SOUND]
    def set_stream(self, stream: str, sound: str, looping=False, volume: float = 1.0):
        if stream in self.streams.keys():
            stream_obj = oalStream(self.ambient_paths[sound])
            self.streams[stream] = [stream_obj, sound, looping]
            volume = volume * STN_MUSIC_VOLUME
            stream_obj.set_position(self.listener_position)
            stream_obj.set_gain(volume)
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
        AudioManagerSingleton.load_sound(path=join(path, file), name=splitext(file)[-2])

    # SOUNDS [STREAM]
    path = get_full_path(join(name, 'music'), file_type='snd')
    files = listdir(path)
    for file in files:
        AudioManagerSingleton.ambient_paths[splitext(file)[-2]] = join(path, file)

    dprint(f'-- Done.\n')
    

def gamePosToSoundPos(pos):
    if len(pos) == 3:
        return [x / 128 for x in pos]
    return [x / 128 for x in (*pos, 0)]


AudioManagerSingleton = AudioManager()
loadSoundPack(STN_SOUND_PACK)
