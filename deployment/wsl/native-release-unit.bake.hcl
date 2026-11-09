# Opt-in only. Invoke from a clean standalone source root with an admitted
# native ARM64 builder; resource caps and the global deadline are external.
variable "SOURCE_REVISION" { default = "unknown" }
variable "GIT_METADATA" { default = "./.git" }
variable "RELEASE_OCI" { default = "" }
variable "UNIT_EVIDENCE" { default = "" }

group "default" {
  targets = ["release", "native-tests"]
}

target "common" {
  context = "."
  dockerfile = "deployment/wsl/Dockerfile.release.arm64"
  platforms = ["linux/arm64"]
  contexts = { gitmeta = "${GIT_METADATA}" }
  args = {
    SOURCE_REVISION = "${SOURCE_REVISION}"
    BUILD_JOBS = "1"
    VCPKG_MAX_CONCURRENCY = "1"
  }
}

target "release" {
  inherits = ["common"]
  target = "game"
  output = ["type=oci,dest=${RELEASE_OCI}"]
}

target "native-tests" {
  inherits = ["common"]
  target = "native-unit-evidence"
  output = ["type=local,dest=${UNIT_EVIDENCE}"]
}
