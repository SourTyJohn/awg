"""
Module containing all engine and game exceptions
"""


class MaterialLoadingError(Exception):

    def __init__(self, file, message=" Error while loading material file "):
        super().__init__(message + file)


class ShaderError( Exception ):

    def __init__(self, shader_path, message, base_message="FILE: {0}.\n{1}"):
        super().__init__(base_message.format( shader_path, message ))


class MaterialRuntimeError( Exception ):
    pass
