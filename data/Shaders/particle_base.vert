#version

layout(location = 0) in vec3 position;
layout(location = 1) in vec4 color;
layout(location = 2) in vec2 size;

uniform mat4 Transform;

out VS_OUT {
    vec4 Color;
    vec2 Size;
} vs_out;


void main() {
    gl_Position = vec4(position, 1.0) * Transform;
    vs_out.Color = color;
    vs_out.Size = size;
}
