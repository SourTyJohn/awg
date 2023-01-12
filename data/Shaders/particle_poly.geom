#version 410
#constant vec2 STN_WINDOW_RESOLUTION

layout (points) in;
layout (triangle_strip, max_vertices=4) out;

uniform vec4 LineColor;
uniform int Thickness;

out vec4 FragColor;

in VS_OUT {
    vec4 Color;
    vec2 Size;
} gs_in[];


void main() {
    vec4 pos1 = gl_in[0].gl_Position;
    vec2 size = gs_in[0].Size / STN_WINDOW_RESOLUTION;
    FragColor = gs_in[0].Color;

        gl_Position = pos1 + vec4(0, size.y, 0, 0); EmitVertex();
        gl_Position = pos1 + vec4(size.x, 0, 0, 0); EmitVertex();
        gl_Position = pos1 - vec4(size.x, 0, 0, 0); EmitVertex();
        gl_Position = pos1 - vec4(0, size.y, 0, 0); EmitVertex();

    EndPrimitive();
}
