#version 460

in vec4 Color;
in vec2 TexCoords;

out vec4 fragColor;

uniform sampler2D samplerTex;
uniform float brightness;

void main() {
   fragColor = texture(samplerTex, TexCoords);
   float average = 0.2126 * fragColor.r + 0.7152 * fragColor.g + 0.0722 * fragColor.b;
   fragColor = vec4(average, average, average, 1.0);
   if (fragColor.a == 0) { discard; }
}
