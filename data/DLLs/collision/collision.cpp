#include "collision.h"

#include <map>

#ifdef PLATFORM_WINDOWS

#ifdef __cplusplus

extern "C" BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved)

#else

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpReserved)

#endif 
{
    // Perform actions based on the reason for calling.
    switch (fdwReason)
    {
    case DLL_PROCESS_ATTACH:
        // Initialize once for each new process.
        // Return FALSE to fail DLL load.
        break;

    case DLL_THREAD_ATTACH:
        // Do thread-specific initialization.
        break;

    case DLL_THREAD_DETACH:
        // Do thread-specific cleanup.
        break;

    case DLL_PROCESS_DETACH:
        // Perform any necessary cleanup.
        break;
    }
    return TRUE;  // Successful DLL_PROCESS_ATTACH.
}

#else
int main(int argc, char const* argv[])
{
    return 0;
}
#endif

struct FixedAndDynamic
{
    int Fixed[256];
    int Dynamic[256];
};

int countFixed = 0;
int countDynamic = 0;

std::map<int, struct Rect> FixedObjs;
std::map<int, struct Rect> DynamicObjs;

void DLL_EXPORT fill_one_element(int x, int y, int w, int h, bool Fixed)
{
    if(Fixed)
    {
        FixedObjs[countFixed].x = x;
        FixedObjs[countFixed].y = y;
        FixedObjs[countFixed].w = w;
        FixedObjs[countFixed].h = h;

        countFixed++;
    }
    else
    {
        DynamicObjs[countDynamic].x = x;
        DynamicObjs[countDynamic].y = y;
        DynamicObjs[countDynamic].w = w;
        DynamicObjs[countDynamic].h = h;

        countDynamic++;
    }
}

FixedAndDynamic DLL_EXPORT startPhysics(int x, int y)
{
    
}

bool DLL_EXPORT checkAABB(struct Rect r1, struct Rect r2)
{ 
	if (r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y) {
		return true;
	}
	else {
		return false;
	}
}