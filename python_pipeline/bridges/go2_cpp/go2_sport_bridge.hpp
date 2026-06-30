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
int go2_sport_hello();
int go2_sport_content();
int go2_sport_heart();
int go2_sport_pose(int flag);
int go2_sport_scrape();
int go2_sport_dance1();
int go2_sport_dance2();
int go2_sport_front_flip();
int go2_sport_back_flip();
int go2_sport_left_flip();
int go2_sport_front_jump();
int go2_sport_front_pounce();
int go2_sport_hand_stand(int flag);
int go2_sport_stretch();
void go2_sport_shutdown();

#ifdef __cplusplus
}
#endif

#endif
