# Recomputed on every build, not just configure. Never retain a cached identity
# after Git failure, and do not rewrite the header if its contents are unchanged.
set(GIT_RETRIEVED_STATE 0)
set(GIT_HEAD_SHA1 "unknown")
set(GIT_IS_DIRTY 1)
set(GIT_COMMIT_DATE_ISO8601 "unknown")
find_package(Git QUIET)
if(Git_FOUND)
    execute_process(COMMAND "${GIT_EXECUTABLE}" rev-parse --verify HEAD
        WORKING_DIRECTORY "${SOURCE_DIRECTORY}"
        RESULT_VARIABLE head_result OUTPUT_VARIABLE head
        OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
    execute_process(COMMAND "${GIT_EXECUTABLE}" status --porcelain --untracked-files=normal
        WORKING_DIRECTORY "${SOURCE_DIRECTORY}"
        RESULT_VARIABLE status_result OUTPUT_VARIABLE status
        OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
    string(LENGTH "${head}" head_length)
    if(head_result EQUAL 0 AND status_result EQUAL 0
       AND head_length EQUAL 40 AND head MATCHES "^[0-9a-f]+$")
        set(GIT_RETRIEVED_STATE 1)
        set(GIT_HEAD_SHA1 "${head}")
        if(status STREQUAL "")
            set(GIT_IS_DIRTY 0)
        endif()
        execute_process(COMMAND "${GIT_EXECUTABLE}" show -s --format=%cI HEAD
            WORKING_DIRECTORY "${SOURCE_DIRECTORY}"
            RESULT_VARIABLE date_result OUTPUT_VARIABLE date
            OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)
        if(date_result EQUAL 0)
            set(GIT_COMMIT_DATE_ISO8601 "${date}")
        endif()
    endif()
endif()
file(MAKE_DIRECTORY "${OUTPUT_DIRECTORY}")
configure_file("${CMAKE_CURRENT_LIST_DIR}/gitmetadata.h.in"
    "${OUTPUT_DIRECTORY}/gitmetadata.h" @ONLY)
