if(NOT CANARY_BUILD_TESTS)
    log_option_disabled("tests")
    return()
endif()

log_option_enabled("tests")
enable_testing()

find_package(
    GTest
    CONFIG
    REQUIRED
)

include(GoogleTest)

function(
    setup_test
    TARGET_NAME
    DIR
)
    if(NOT
       TARGET
       canary_core
    )
        if(NOT CANARY_BUILD_TESTS)
            return()
        endif()
        message(
            FATAL_ERROR
                "canary_core is required when building tests. Ensure CANARY_BUILD_TESTS is ON."
        )
    endif()

    add_executable(${TARGET_NAME})

    target_sources(
        ${TARGET_NAME}
        PRIVATE ${CMAKE_SOURCE_DIR}/tests/${DIR}/main.cpp
    )

    target_compile_definitions(
        ${TARGET_NAME}
        PUBLIC -DDEBUG_LOG -DBUILD_TESTS
    )

    target_link_libraries(
        ${TARGET_NAME}
        PRIVATE canary_core GTest::gtest
    )

    target_include_directories(
        ${TARGET_NAME}
        PRIVATE ${CMAKE_SOURCE_DIR}/tests/fixture
                ${CMAKE_SOURCE_DIR}/tests/${DIR}
    )

    target_compile_features(
        ${TARGET_NAME}
        PRIVATE cxx_std_20
    )

    if(USE_PRECOMPILED_HEADER)
        target_precompile_headers(
            ${TARGET_NAME}
            PRIVATE
            ${CMAKE_SOURCE_DIR}/tests/test_pch.hpp
        )
        target_compile_definitions(
            ${TARGET_NAME}
            PRIVATE USE_PRECOMPILED_HEADERS
        )
    endif()

    # Note: setup_target is internal, assume it works for generic targets
    if(COMMAND setup_target)
        setup_target(${TARGET_NAME})
    endif()

    # Note: configure_linking handles global flags
    if(COMMAND configure_linking)
        configure_linking(${TARGET_NAME})
    endif()

    set_target_properties(
        ${TARGET_NAME}
        PROPERTIES UNITY_BUILD OFF
                   INTERPROCEDURAL_OPTIMIZATION OFF
    )
    log_option_disabled("Build unity")

    if(MSVC)
        target_link_options(
            ${TARGET_NAME}
            PRIVATE
            /DEBUG:FASTLINK
        )
        # Ensure correct runtime if static
        if(BUILD_STATIC_LIBRARY)
            set_property(
                TARGET ${TARGET_NAME}
                PROPERTY MSVC_RUNTIME_LIBRARY
                         "MultiThreaded$<$<CONFIG:Debug>:Debug>"
            )
        else()
            set_property(
                TARGET ${TARGET_NAME}
                PROPERTY MSVC_RUNTIME_LIBRARY
                         "MultiThreaded$<$<CONFIG:Debug>:Debug>DLL"
            )
        endif()
    endif()

    gtest_discover_tests(
        ${TARGET_NAME}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/tests/${DIR}
        PROPERTIES
        TIMEOUT 120
                DISCOVERY_MODE PRE_TEST
    )
endfunction()

add_subdirectory(unit)
add_subdirectory(integration)

if(UNIX AND CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    add_test(NAME bot_engine_loader_regression
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tools/bot_brain/test_engine_loader.py)
    set_tests_properties(bot_engine_loader_regression PROPERTIES
        ENVIRONMENT "BOT_TEST_CXX=${CMAKE_CXX_COMPILER};BOT_TEST_INCLUDES=${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/include"
        TIMEOUT 180)
    find_program(BOT_TEST_LUAJIT luajit HINTS "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/tools/luajit")
    if(BOT_TEST_LUAJIT)
        foreach(BOT_RELOAD_TEST test_reload test_reload_missing test_reload_failures)
            add_test(NAME ${BOT_RELOAD_TEST}
                COMMAND ${BOT_TEST_LUAJIT} tools/bot_brain/${BOT_RELOAD_TEST}.lua)
            set_tests_properties(${BOT_RELOAD_TEST} PROPERTIES WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
        endforeach()
    endif()
endif()
