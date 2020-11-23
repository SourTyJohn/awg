#include "Hitbox.h"

Hitbox::Hitbox(int x, int y, int w, int h)
{
	_x = x;
	_y = y;

	_w = w;
	_h = h;
}

int* Hitbox::GetRect()
{
	int* Rect = new int[4];

	Rect[0] = _x;
	Rect[1] = _y;

	Rect[2] = _w;
	Rect[3] = _h;
}