#version 460

in vec4 Color;
in vec2 TexCoords;

out vec4 FragColor;

uniform sampler2D samplerTex;


void main() {
   FragColor = texture(samplerTex, TexCoords) * Color;
}
