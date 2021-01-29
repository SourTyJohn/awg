#version 460

layout(location = 0) in vec3 position;
layout(location = 1) in vec4 color;

uniform mat4 Transform;
uniform float cameraPos;

out vec4 Color;
out vec2 TexCoords;


void main() {
    gl_Position =  vec4(position, 1.0) * Transform;
    float k = tan(gl_Position[1]) + cameraPos;
    Color = color * k;
}
