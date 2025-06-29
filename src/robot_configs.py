"""
Robot configurations for Isaac Sim DOF simulation.
This file maps friendly robot names to their USD paths and metadata.
"""

ROBOT_CONFIGS = {
    # Manipulator Robots
    "franka": {
        "name": "Franka Emika Panda",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Franka/franka.usd",
        "prim_path": "/World/Franka",
        "description": "7-DOF robotic arm with parallel gripper"
    },
    "ur5": {
        "name": "Universal Robots UR5",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/UniversalRobots/ur5/ur5.usd",
        "prim_path": "/World/UR5",
        "description": "6-DOF collaborative robot arm"
    },
    "kinova": {
        "name": "Kinova Gen3",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Kinova/Gen3/gen3n7_instanceable.usd",
        "prim_path": "/World/Kinova",
        "description": "7-DOF lightweight robotic arm"
    },
    "flexiv": {
        "name": "Flexiv Rizon 4",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Flexiv/Rizon4/flexiv_rizon4.usd",
        "prim_path": "/World/FlexivRizon4",
        "description": "7-DOF adaptive robotic arm"
    },
    
    # Mobile Robots
    "carter": {
        "name": "NVIDIA Carter",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Carter/carter_v1.usd",
        "prim_path": "/World/Carter",
        "description": "Differential drive mobile robot"
    },
    "jetbot": {
        "name": "NVIDIA JetBot",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Jetbot/jetbot.usd",
        "prim_path": "/World/JetBot",
        "description": "Educational AI robot platform"
    },
    
    # Humanoid Robots
    "digit": {
        "name": "Agility Robotics Digit",
        "usd_path": "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/4.5/Isaac/Robots/Agility/Digit/digit_v4.usd",
        "prim_path": "/World/Digit",
        "description": "Bipedal humanoid robot"
    }
}

def get_robot_config(robot_name: str) -> dict:
    """Get robot configuration by name.
    
    Args:
        robot_name: Name of the robot (case insensitive)
        
    Returns:
        Dictionary containing robot configuration
        
    Raises:
        KeyError: If robot name is not found
    """
    robot_name = robot_name.lower()
    if robot_name not in ROBOT_CONFIGS:
        available = list(ROBOT_CONFIGS.keys())
        raise KeyError(f"Robot '{robot_name}' not found. Available robots: {available}")
    return ROBOT_CONFIGS[robot_name] 