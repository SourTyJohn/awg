#include "collision.h"

#ifdef PLATFORM_WINDOWS

BOOL WINAPI DllMain(
    HINSTANCE hinstDLL,  // handle to DLL module
    DWORD fdwReason,     // reason for calling function
    LPVOID lpReserved)  // reserved
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

int countHitboxes = 0;
struct Rect hitboxes[256];

void fill_one_element(int x, int y, int w, int h)
{
    hitboxes[countHitboxes].x = x;
    hitboxes[countHitboxes].y = y;
    hitboxes[countHitboxes].w = w;
    hitboxes[countHitboxes].h = h;

    countHitboxes++;
}

bool checkAABB(struct Rect r1, struct Rect r2)
{ 
	if (r1.x < r2.x + r2.w && r1.x + r1.w > r2.x && r1.y < r2.y + r2.h && r1.y + r1.h > r2.y) {
		return true;
	}
	else {
		return false;
	}
}