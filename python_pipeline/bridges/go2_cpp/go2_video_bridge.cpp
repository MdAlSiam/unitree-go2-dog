#include "go2_video_bridge.hpp"

#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/go2/video/video_client.hpp>

#include <cstring>
#include <memory>
#include <mutex>
#include <new>
#include <vector>

namespace {

std::mutex g_mutex;
std::unique_ptr<unitree::robot::go2::VideoClient> g_video_client;
bool g_initialized = false;

}  // namespace

extern "C" int go2_video_init(const char* network_interface) {
    std::lock_guard<std::mutex> lock(g_mutex);

    if (g_initialized) {
        return 0;
    }

    try {
        if (network_interface != nullptr && std::strlen(network_interface) > 0) {
            unitree::robot::ChannelFactory::Instance()->Init(0, network_interface);
        } else {
            unitree::robot::ChannelFactory::Instance()->Init(0);
        }

        g_video_client = std::make_unique<unitree::robot::go2::VideoClient>();
        g_video_client->SetTimeout(1.0f);
        g_video_client->Init();
        g_initialized = true;
        return 0;
    } catch (...) {
        g_video_client.reset();
        g_initialized = false;
        return -1;
    }
}

extern "C" int go2_video_get_frame(void** out_data, int* out_size) {
    if (out_data == nullptr || out_size == nullptr) {
        return -2;
    }

    std::lock_guard<std::mutex> lock(g_mutex);
    if (!g_initialized || !g_video_client) {
        return -3;
    }

    std::vector<uint8_t> frame;
    int ret = g_video_client->GetImageSample(frame);
    if (ret != 0) {
        return ret;
    }

    if (frame.empty()) {
        *out_data = nullptr;
        *out_size = 0;
        return 0;
    }

    auto* copied = new (std::nothrow) uint8_t[frame.size()];
    if (copied == nullptr) {
        return -4;
    }

    std::memcpy(copied, frame.data(), frame.size());
    *out_data = copied;
    *out_size = static_cast<int>(frame.size());
    return 0;
}

extern "C" void go2_video_free_frame(uint8_t* data) {
    delete[] data;
}

extern "C" void go2_video_shutdown() {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_video_client.reset();
    g_initialized = false;
}
