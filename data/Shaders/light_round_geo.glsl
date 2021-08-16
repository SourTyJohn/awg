#version 460
#constant vec2 WINDOW_RESOLUTION
#constant int LIGHT_POLYGONS
const float  ANGLE = 3.14159 * 2 / LIGHT_POLYGONS;

layout (points) in;
layout (triangle_strip, max_vertices=LIGHT_POLYGONS * 3) out;

out vec4 FragColor;

in VS_OUT {
    vec4 Color;
    float Radius;
} gs_in[];


vec2 getOffset(float angle, float radius) {
    return vec2(radius * cos(angle), radius * sin(angle)) / WINDOW_RESOLUTION;
}


void main() {
    vec4  pos = gl_in[0].gl_Position;
    vec4  middle_color = gs_in[0].Color;
    vec4  distant_color = vec4(middle_color.xyz, 0.0);
    float radius = gs_in[0].Radius;
    vec2  offset;

    offset = getOffset(0, radius);
    for (int x = 1; x <= LIGHT_POLYGONS; x++) {
        gl_Position = pos;
        FragColor = middle_color; EmitVertex();

        // offset from previos iteration
        gl_Position = pos + vec4(offset, 0.0, 0.0);
        FragColor = distant_color; EmitVertex();

        offset = getOffset(ANGLE * x, radius);
        gl_Position = pos + vec4(offset, 0.0, 0.0);
        FragColor = distant_color; EmitVertex();

        EndPrimitive();
    }
}
