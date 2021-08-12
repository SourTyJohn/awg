#version 460

layout(location = 0) in vec3 position;

uniform mat4 Transform;


void main() {
    gl_Position = vec4(position, 1.0) * Transform;
}
