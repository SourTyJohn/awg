#pragma once

class Rect
{
public:

	Rect(int x, int y, int w, int h);
	~Rect();

	Rect copy();

	int* GetCenter();

	void SetCenter(int* center);

	int* GetPos();

	void SetX(int x);
	void SetY(int y);

	void SetPos(int x, int y);
	void SetPos(int xNy[2]);

	int* GetSize();

	void SetSize(int w, int h);
	void SetSize(int* wNh);

private:

	//char* __slots__[256] = {(char*)"values"};

	int _x, _y;
	int _w, _h;
};

