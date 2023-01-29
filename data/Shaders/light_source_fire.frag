#version
#constant float LIGHT_MULTIPLY

in float dist;
in vec2 TexCoords;
in vec4 Color;

out vec4 FragColor;

uniform float RandK;


void main() {
   float dist = distance( TexCoords, vec2(0.5, 0.5) ) * ( 1 + clamp( 0.0, 1.0, RandK ));
   dist = smoothstep(1 - dist, -0.1, 0.5) * (1 - step(0.5, dist));
   FragColor = vec4( Color.xyz, dist * LIGHT_MULTIPLY );
}
