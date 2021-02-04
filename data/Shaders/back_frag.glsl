#version 410

in vec4 Color;
uniform sampler2D samplerTex;

void main() {
   gl_FragColor = Color;
}
