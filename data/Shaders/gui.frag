#version

in vec4 Color;
in vec2 TexCoords;

out vec4 FragColor;

uniform sampler2D samplerTex;


void main() {
   vec4 tex = texture(samplerTex, TexCoords);
   FragColor = vec4(tex.xyz, tex.a);
}
