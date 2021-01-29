#version 460
#constant float LIGHT_MULTIPLY

in float dist;
in vec2 TexCoords;
in vec4 Color;

uniform sampler2D LightTex;
uniform float Smooth;


void main() {
   float dist = distance( TexCoords, vec2(0.5, 0.5) );

   if (dist <= 0.5) {
      dist = smoothstep( (1 - dist) * Smooth, 0, 0.5);
      gl_FragColor = vec4(Color.xyz, dist);

   } else {
      gl_FragColor = vec4(0, 0, 0, 0);
   }

}
