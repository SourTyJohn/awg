#version 460
#constant uint MAX_INSTANCES

layout(location = 0) in vec3 position;
layout(location = 1) in vec4 color;
layout(location = 2) in vec2 InTexCoords;

uniform mat4 Scale;
uniform mat4[MAX_INSTANCES] Transform;

out vec4 Color;
out vec2 TexCoords;


void main() {
    gl_Position = vec4(position, 1.0) * Transform[gl_InstanceID];
    Color = color;
    TexCoords = InTexCoords;
}
