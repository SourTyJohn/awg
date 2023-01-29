#version
#constant vec2 STN_WINDOW_RESOLUTION

layout (lines) in;
layout (triangle_strip, max_vertices=4) out;

uniform vec4 LineColor;
uniform int Thickness;

out vec4 FragColor;


void main() {
    vec4 pos1 = gl_in[0].gl_Position;
    vec4 pos2 = gl_in[1].gl_Position;
    float dx = pos2.x - pos1.x;
    float dy = pos2.y - pos1.y;
    float len = sqrt(pow(dx, 2) + pow(dy, 2));
    vec2 sincos = (vec2(dy / len, dx / len) * Thickness / STN_WINDOW_RESOLUTION);
    FragColor = LineColor;

        gl_Position = vec4(pos1.x + sincos.x, pos1.y - sincos.y, pos1.z, 1.0);
        EmitVertex();

        gl_Position = vec4(pos2.x + sincos.x, pos2.y - sincos.y, pos2.z, 1.0);
        EmitVertex();

        gl_Position = pos1;
        FragColor = vec4(FragColor.xyz, FragColor.w * 0.5);
        EmitVertex();

        gl_Position = pos2;
        FragColor = vec4(FragColor.xyz, FragColor.w * 0.5);
        EmitVertex();

    EndPrimitive();
}
