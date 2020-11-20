#ifndef _H_
#define _H_

#ifdef  __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdbool.h>
#include <math.h>

#define PLATFORM_WINDOWS  1
#define PLATFORM_MAC      2
#define PLATFORM_UNIX     3

#if defined(_WIN32)
	#define PLATFORM PLATFORM_WINDOWS
#elif defined(__APPLE__)
	#define PLATFORM PLATFORM_MAC
#else
	#define PLATFORM PLATFORM_UNIX
#endif

struct Rect 
{
	int x, y;

	int w, h;
};

#ifdef PLATFORM_WINDOWS
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT
#endif

#ifndef PLATFORM_WINDOWS
	int main(int argc, char const *argv[]);
#else
	#include <Windows.h>
	BOOL DLL_EXPORT WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved);
#endif

bool DLL_EXPORT checkAABB(struct Rect r1, struct Rect r2);
void DLL_EXPORT fill_one_element(int x, int y, int w, int h);

#ifdef  __cplusplus
}
#endif

#endif