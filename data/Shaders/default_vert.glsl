#version 410

layout(location = 0) in vec2 position;
layout(location = 1) in vec4 color;
layout(location = 2) in vec2 InTexCoords;

uniform mat4 Translate;
uniform mat4 Scale;
uniform mat4 RotationZ;
//uniform mat4 RotationY;
uniform mat4 Ortho;

out vec4 Color;
out vec2 TexCoords;


void main() {
    gl_Position = vec4(position, 0.0, 1.0) * RotationZ * Translate * Ortho;
    Color = color;
    TexCoords = InTexCoords;
}