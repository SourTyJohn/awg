#version
#constant uint MAX_TEXTURES_BIND

layout(location = 0) in vec3 position;
layout(location = 1) in vec2 InTexCoords;


uniform mat4 sTransform[MAX_TEXTURES_BIND];
uniform vec4 sColor[MAX_TEXTURES_BIND];
uniform vec2 sScale[MAX_TEXTURES_BIND];
uniform uint sStencil[MAX_TEXTURES_BIND];


flat out vec4 Color;
flat out uint StencilId;
out vec2 TexCoords;


void main() {
    vec4 full_scale = vec4( sScale[gl_InstanceID], 1.0, 1.0 );
    gl_Position = vec4(position, 1.0) * full_scale * sTransform[gl_InstanceID];

    Color = sColor[gl_InstanceID];
    TexCoords = InTexCoords;
    StencilId =  sStencil[gl_InstanceID];
}
