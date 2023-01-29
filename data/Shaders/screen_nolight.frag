#version

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;
uniform float brightness;

out vec4 FragColor;


void main() {
   vec4 color = texture(samplerTex, TexCoords) * Color;
   FragColor = color * brightness;
}
