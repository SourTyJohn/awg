#version 460
#constant float AMBIENT_LIGHT

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;

out vec4 fragColor;


void main() {
   fragColor = texture(samplerTex, TexCoords);
   fragColor = vec4(fragColor.xyz * AMBIENT_LIGHT, fragColor.a);
   if (fragColor.a == 0) { discard; }
}
