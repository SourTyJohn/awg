#version 410

layout(location = 0) in vec2 position;
layout(location = 1) in vec4 color;

uniform mat4 Translate;
uniform mat4 Ortho;

uniform float cameraPos;

out vec4 Color;
out vec2 TexCoords;


void main() {
    gl_Position =  vec4(position, 0.0, 1.0) * Translate * Ortho;
    float k = sin(gl_Position[1] + cameraPos);
    Color = color * k;
}
