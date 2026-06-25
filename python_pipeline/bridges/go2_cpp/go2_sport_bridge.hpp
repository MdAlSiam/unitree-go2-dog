#ifndef GO2_SPORT_BRIDGE_HPP
#define GO2_SPORT_BRIDGE_HPP

#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct go2_path_point_t {
    float time_from_start;
    float x;
    float y;
    float yaw;
    float vx;
    float vy;
    float vyaw;
} go2_path_point_t;

int go2_sport_init(const char* network_interface);
int go2_sport_stand_up();
int go2_sport_stand_down();
int go2_sport_balance_stand();
int go2_sport_speed_level(int level);
int go2_sport_move(float vx, float vy, float vyaw);
int go2_sport_damp();
int go2_sport_recovery_stand();
int go2_sport_sit();
int go2_sport_rise_sit();
int go2_sport_stop_move();
int go2_sport_trajectory_follow(const go2_path_point_t* points, int count);
void go2_sport_shutdown();

#ifdef __cplusplus
}
#endif

#endif
