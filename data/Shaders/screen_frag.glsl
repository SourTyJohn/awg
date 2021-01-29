#version 460

in vec4 Color;
in vec2 TexCoords;


uniform sampler2D samplerTex;  // texture containing scene without lighting
uniform sampler2D lightMap;  // texture containing scene lights
uniform sampler2D depthMap;  // texture containing scene depth
uniform float brightness;  // overall game brightness


void main() {
   vec4 lightColor = texture(lightMap, TexCoords);
   vec4 color = texture(samplerTex, TexCoords) * Color;
   float depth = texture(depthMap, TexCoords).r ;

   if (lightColor.a == 0 || depth > 0.4 ) {
      gl_FragColor = color * brightness;

   } else {
      float intence = lightColor.a * depth;
      vec3 color_n = normalize(color.xyz);
      vec3 light = vec3(intence * color_n.x, intence * color_n.y, intence * color_n.z);

      gl_FragColor = vec4(color.xyz + light, color.a) * brightness;
   }

   if (gl_FragColor.a == 0) {
      discard;
   }
}
