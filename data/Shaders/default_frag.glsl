#version 410

in vec4 Color;
in vec2 TexCoords;

out vec4 fragColor;
uniform sampler2D samplerTex;

void main() {
   fragColor = texture(samplerTex, TexCoords) * Color;
}