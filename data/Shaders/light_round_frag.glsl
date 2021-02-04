#version 460
#constant float LIGHT_MULTIPLY

in float dist;
in vec2 TexCoords;
in vec4 Color;

uniform sampler2D LightTex;


void main() {
   float dist = distance( TexCoords, vec2(0.5, 0.5) );
   dist = ( (0.5 - dist) * 2 ) * (1 - step(0.5, dist));
   gl_FragColor = vec4( Color.xyz, dist );
}
