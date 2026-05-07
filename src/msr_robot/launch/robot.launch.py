robot_description_launcher = IncludeLaunchDescription(
        PathJoinSubstitution(
            [FindPackageShare("rover_moveit_config"), "launch",
            "rsp.launch.py"]
        ),
    )
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        output="screen"
    )