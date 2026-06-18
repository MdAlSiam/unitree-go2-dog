#ifndef GO2_VIDEO_BRIDGE_HPP
#define GO2_VIDEO_BRIDGE_HPP

#include <cstdint>

extern "C" {

int go2_video_init(const char* network_interface);
int go2_video_get_frame(void** out_data, int* out_size);
void go2_video_free_frame(uint8_t* data);
void go2_video_shutdown();

}

#endif
