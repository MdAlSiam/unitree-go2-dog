cmake_minimum_required(VERSION 3.5)

get_filename_component(PYTHON_PIPELINE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)

add_library(go2_video_bridge SHARED go2_video_bridge.cpp)

add_library(go2_sport_bridge SHARED go2_sport_bridge.cpp)

target_include_directories(go2_video_bridge
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(go2_video_bridge
    PRIVATE
        unitree_sdk2
)

target_link_libraries(go2_sport_bridge
    PRIVATE
        unitree_sdk2
)

set_target_properties(go2_video_bridge PROPERTIES
    OUTPUT_NAME "go2_video_bridge"
    POSITION_INDEPENDENT_CODE ON
)

set_target_properties(go2_sport_bridge PROPERTIES
    OUTPUT_NAME "go2_sport_bridge"
    POSITION_INDEPENDENT_CODE ON
)

add_custom_command(TARGET go2_video_bridge POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${PYTHON_PIPELINE_ROOT}/bin
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:go2_video_bridge> ${PYTHON_PIPELINE_ROOT}/bin/
    COMMENT "Copying go2_video_bridge to python_pipeline/bin"
)

add_custom_command(TARGET go2_sport_bridge POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory ${PYTHON_PIPELINE_ROOT}/bin
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:go2_sport_bridge> ${PYTHON_PIPELINE_ROOT}/bin/
    COMMENT "Copying go2_sport_bridge to python_pipeline/bin"
)
