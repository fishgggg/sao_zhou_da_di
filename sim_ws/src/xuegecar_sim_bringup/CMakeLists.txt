cmake_minimum_required(VERSION 3.8)
project(xuegecar_sim_bringup)

find_package(ament_cmake REQUIRED)

# 安装 launch 与 worlds 目录到 share/<包名>/
# 少一行，ros2 launch 就找不到文件、world:=默认值也指向不存在的路径。
install(
  DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}
)

# 回归脚本（阶段 10）：ros2 run xuegecar_sim_bringup regression 或
# 直接 bash install/xuegecar_sim_bringup/lib/xuegecar_sim_bringup/regression.sh
install(
  PROGRAMS scripts/regression.sh
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
