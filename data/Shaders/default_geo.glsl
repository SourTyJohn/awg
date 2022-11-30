#version 460
#constant vec2 WINDOW_RESOLUTION

layout (points) in;
layout (triangle_strip, max_vertices=6) out;

out vec4 FragColor;
out vec2 TexCoords;

in ObjectData {
	vec4 Color;
	vec3 Size;
	vec3 CameraOffset;
    mat4 InTexCoords;
} obj_data[];


void main() {
    vec4 center_pos = gl_in[0].gl_Position;
    float x = size.x;
    float y = size.y;

    gl_Position = pos + vec3(-x, +y, 0); TexCoords = obj_data[0].InTexCoords[0]; EmitVertex();
    gl_Position = pos + vec3(-x, -y, 0); TexCoords = obj_data[0].InTexCoords[1]; EmitVertex();
    gl_Position = pos + vec3(+x, +y, 0); TexCoords = obj_data[0].InTexCoords[2]; EmitVertex();
    EndPrimitive();

    gl_Position = pos + vec3(+x, -y, 0); TexCoords = obj_data[0].InTexCoords[3]; EmitVertex();
    gl_Position = pos + vec3(-x, -y, 0); TexCoords = obj_data[0].InTexCoords[1]; EmitVertex();
    gl_Position = pos + vec3(+x, +y, 0); TexCoords = obj_data[0].InTexCoords[2]; EmitVertex();
    EndPrimitive();
}
