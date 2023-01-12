#version 460
#constant uint MAX_TEXTURES_BIND
#constant uint MAX_INSTANCES

in vec4 Color;
in vec3 TexCoords;

out vec4 FragColor;

uniform sampler2DArray STexture;


void main() {
   vec4 base_color = texture( STexture, TexCoords );
   FragColor = base_color * Color;
}
