#version 460

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;
uniform float brightness;


void main() {
   vec4 color = texture(samplerTex, TexCoords) * Color;
   gl_FragColor = color * brightness;
}
