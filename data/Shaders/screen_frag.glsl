#version 410
#constant float AMBIENT_LIGHT

in vec4 Color;
in vec2 TexCoords;

uniform sampler2D samplerTex;
uniform sampler2D lightMap;
uniform sampler2D depthMap;
uniform float brightness;


void main() {
   vec4 lightColor = texture(lightMap, TexCoords);
   float power = lightColor.a;
   lightColor = vec4(lightColor.xyz, 0);

   vec4 color = texture(samplerTex, TexCoords) * Color;
   float depth = texture(depthMap, TexCoords).x;

   float intence = 1.0;
   if ( depth < 0.6 ) {
      intence = (power * 4 + AMBIENT_LIGHT) * depth;
   }

   gl_FragColor = ( color + lightColor ) * intence * brightness;
//   gl_FragColor = texture(lightMap, TexCoords);
}
