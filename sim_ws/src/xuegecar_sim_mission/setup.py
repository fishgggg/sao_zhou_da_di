from setuptools import setup

package_name = 'xuegecar_sim_mission'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='y',
    maintainer_email='y@example.com',
    description='任务状态机：唯一速度出口 + 状态管理（阶段 8）',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mission_control = xuegecar_sim_mission.mission_control:main',
            'fake_chassis = xuegecar_sim_mission.fake_chassis:main',
        ],
    },
)
