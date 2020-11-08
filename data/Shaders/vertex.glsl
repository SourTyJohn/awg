#version 330 core

layout (location=0) in vec3 VertexPosition;
layout (location=1) in vec3 VertexColor;

out vec3 Color;

void main()
{
  Color = vec3(1.0, 1.0, 1.0);
  gl_Position = vec4(VertexPosition, 1.0);
}
