#version 460
#constant uint MAX_TEXTURES_BIND

in vec2 TexCoords;
flat in vec4 Color;
flat in uint StencilId;

out vec4 diffuseColor;

uniform sampler2D textures[MAX_TEXTURES_BIND];
//  0 = light texture    1:MAX = stencil textures

void main() {
   vec4 color = texture( textures[0], TexCoords ).a * Color;
   diffuseColor = color;
}
