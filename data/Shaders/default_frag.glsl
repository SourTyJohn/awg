#version 410

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;


void main() {
   vec4 tex = texture(samplerTex, TexCoords) * Color;
   gl_FragColor = vec4(tex.xyz, tex.a);
}
