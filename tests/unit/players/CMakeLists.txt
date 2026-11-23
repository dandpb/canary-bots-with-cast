target_sources(
    canary_ut
    PRIVATE player_item_batch_test.cpp reward_iteration_test.cpp
)

add_subdirectory(components)
add_subdirectory(condition)
add_subdirectory(imbuements)
target_sources(canary_ut PRIVATE bot_brain_admission_test.cpp bot_brain_protocol_test.cpp bot_save_queue_test.cpp bot_database_scope_test.cpp cast_publisher_test.cpp)

target_sources(
    canary_ut
    PRIVATE forge_test.cpp
            party_test.cpp
            ip_throttle_prune_test.cpp
)
