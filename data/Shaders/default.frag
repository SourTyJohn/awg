#version
#constant uint MAX_TEXTURES_BIND
#constant uint MAX_INSTANCES

in vec4 Color;
in vec2 TexCoords;

out vec4 FragColor;

uniform sampler2D Textures[MAX_TEXTURES_BIND];
uniform uint InstanceTex[MAX_INSTANCES];
flat in uint InstanceID;


void main() {
   vec4 base_color = texture( Textures[InstanceTex[InstanceID]], TexCoords);
   FragColor = base_color * Color;
}
