#version 460

layout(location = 0) in vec3 position;
layout(location = 1) in vec4 color;
layout(location = 2) in vec2 InTexCoords;


out vec4 Color;
out vec2 TexCoords;


void main() {
    gl_Position = vec4(position.x, -position.y, position.z, 1.0);
    Color = color;
    TexCoords = InTexCoords;
}
