# Share one fresh identity across the core and the independently built bot engine.
include_guard(GLOBAL)
set(_canary_metadata_directory "${CMAKE_BINARY_DIR}/source-metadata")
add_custom_target(canary_source_metadata
    COMMAND "${CMAKE_COMMAND}"
        "-DSOURCE_DIRECTORY=${CMAKE_SOURCE_DIR}"
        "-DOUTPUT_DIRECTORY=${_canary_metadata_directory}"
        -P "${CMAKE_CURRENT_LIST_DIR}/WriteSourceMetadata.cmake"
    BYPRODUCTS "${_canary_metadata_directory}/gitmetadata.h"
    COMMENT "Refreshing source commit and dirty state"
    VERBATIM
)

function(canary_target_source_metadata target)
    add_dependencies(${target} canary_source_metadata)
    target_include_directories(${target} PRIVATE "${CMAKE_BINARY_DIR}/source-metadata")
endfunction()
