#version 460

in vec4 Color;
in vec2 TexCoords;

out vec4 fragColor;

uniform sampler2D samplerTex;
uniform float brightness;

void main() {
   fragColor = texture(samplerTex, TexCoords) * Color * brightness;
   if (fragColor.a == 0) { discard; }
}
