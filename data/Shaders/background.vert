#version

layout(location = 0) in vec3 position;
layout(location = 1) in vec4 color;

uniform float cameraPos;

out vec4 Color;


void main() {
    Color = color * (tan(gl_Position[1]) + cameraPos);
    gl_Position =  vec4(position, 1.0);
}
