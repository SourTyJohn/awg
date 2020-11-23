#pragma once

class Hitbox
{
	Hitbox(int x, int y, int w, int h);

	virtual ~Hitbox() = 0;

	int* GetRect();

private:

	int _x, _y;
	int _w, _h;
};

