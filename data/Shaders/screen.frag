#version 410
#constant float AMBIENT_LIGHT

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;
uniform sampler2D lightMap;
uniform sampler2D depthMap;
uniform float brightness;

out vec4 FragColor;


void main() {
   vec4 lightColor = texture(lightMap, TexCoords);
   float power = lightColor.a;
   lightColor = vec4(lightColor.xyz, 0);

   vec4 color = texture(samplerTex, TexCoords) * Color;
   float depth = texture(depthMap, TexCoords).x;

   float intence = (power + AMBIENT_LIGHT) * depth;

   FragColor = ( color * brightness + lightColor ) * intence;
}
