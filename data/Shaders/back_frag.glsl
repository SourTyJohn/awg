#version 410

in vec4 Color;

out vec4 fragColor;

uniform sampler2D samplerTex;


void main() {
   fragColor = Color;
}
