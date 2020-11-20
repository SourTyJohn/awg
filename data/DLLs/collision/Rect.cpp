#include "Rect.h"

Rect::Rect(int x, int y, int w, int h)
{
	_x = x;
	_y = y;

	_w = w;
	_h = h;
}

Rect::~Rect()
{
}

Rect Rect::copy()
{
	return Rect(_x, _y, _w, _h);
}

int* Rect::GetCenter()
{
	int* Center = new int[2];
	
	Center[0] = (_y + _h / 2);
	Center[1] = (_x + _w / 2);

	return Center;
}

void Rect::SetCenter(int* center)
{
	_x = center[0] / 2;
	_y = center[1] / 2;
}

int* Rect::GetPos()
{
	int* pos = new int[2];

	pos[0] = _x;
	pos[1] = _y;
	
	return pos;
}

void Rect::SetX(int x)
{
	_x = x;
}

void Rect::SetY(int y)
{
	_y = y;
}

void Rect::SetPos(int x, int y)
{
	_x = x;
	_y = y;
}

void Rect::SetPos(int xNy[2])
{
	_x = xNy[0];
	_y = xNy[1];
}

int* Rect::GetSize()
{
	int* size = new int[2];

	size[0] = _w;
	size[1] = _h;

	return size;
}

void Rect::SetSize(int w, int h)
{
	_w = w;
	_h = h;
}

void Rect::SetSize(int* wNh)
{
	_w = wNh[0];
	_h = wNh[1];
}
