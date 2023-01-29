#version
#constant float AMBIENT_LIGHT

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D geomMap;
uniform sampler2D lightMap;
uniform sampler2D depthMap;
uniform float brightness;

out vec4 FragColor;


void main() {
   vec4 lightColor = texture(lightMap, TexCoords);
   float power = lightColor.a;
   lightColor = vec4(lightColor.xyz, 0);

   vec4 color = texture(geomMap, TexCoords) * Color;
   float depth = texture(depthMap, TexCoords).x;

   float intence = clamp( (power + AMBIENT_LIGHT) * depth, 0.2, 1.0 );

   FragColor = ( color * brightness + lightColor ) * intence;
}
