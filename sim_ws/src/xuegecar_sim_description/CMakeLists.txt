cmake_minimum_required(VERSION 3.8)
project(xuegecar_sim_description)

find_package(ament_cmake REQUIRED)

# 关键：把 urdf / rviz 目录安装到 share/<包名>/ 下。
# 没有这几行，get_package_share_directory('xuegecar_sim_description')
# 就找不到 URDF —— launch 会直接报文件不存在。
install(
  DIRECTORY urdf rviz
  DESTINATION share/${PROJECT_NAME}
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
