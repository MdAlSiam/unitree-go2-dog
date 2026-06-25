#include "go2_sport_bridge.hpp"

#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/go2/sport/sport_client.hpp>

#include <cstring>
#include <memory>
#include <mutex>

namespace {

std::mutex g_mutex;
std::unique_ptr<unitree::robot::go2::SportClient> g_sport_client;
bool g_initialized = false;

int EnsureInitialized() {
    if (!g_initialized || !g_sport_client) {
        return -2;
    }
    return 0;
}

}  // namespace

extern "C" int go2_sport_init(const char* network_interface) {
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

        g_sport_client = std::make_unique<unitree::robot::go2::SportClient>();
        g_sport_client->SetTimeout(10.0f);
        g_sport_client->Init();
        g_initialized = true;
        return 0;
    } catch (...) {
        g_sport_client.reset();
        g_initialized = false;
        return -1;
    }
}

extern "C" int go2_sport_stand_up() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->StandUp();
}

extern "C" int go2_sport_stand_down() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->StandDown();
}

extern "C" int go2_sport_balance_stand() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->BalanceStand();
}

extern "C" int go2_sport_move(float vx, float vy, float vyaw) {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->Move(vx, vy, vyaw);
}

extern "C" int go2_sport_speed_level(int level) {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->SpeedLevel(level);
}

extern "C" int go2_sport_damp() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->Damp();
}

extern "C" int go2_sport_recovery_stand() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->RecoveryStand();
}

extern "C" int go2_sport_sit() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->Sit();
}

extern "C" int go2_sport_rise_sit() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->RiseSit();
}

extern "C" int go2_sport_stop_move() {
    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }
    return g_sport_client->StopMove();
}

extern "C" int go2_sport_trajectory_follow(const go2_path_point_t* points, int count) {
    if (points == nullptr || count <= 0) {
        return -4;
    }

    std::lock_guard<std::mutex> lock(g_mutex);
    int init_ret = EnsureInitialized();
    if (init_ret != 0) {
        return init_ret;
    }

    // This SDK build does not expose SportClient::TrajectoryFollow.
    return -5;
}

extern "C" void go2_sport_shutdown() {
    std::lock_guard<std::mutex> lock(g_mutex);
    g_sport_client.reset();
    g_initialized = false;
}
