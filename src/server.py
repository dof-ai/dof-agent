#!/usr/bin/env python3

import asyncio
from mcp.server import Server, InitializationOptions, NotificationOptions
import mcp.types as types
from robot_configs import ROBOT_CONFIGS
from dof import DOF
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

server = Server("dof-sim")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    # Get list of available robots for the dropdown
    robot_choices = [{"title": config["name"], "value": robot_name} 
                    for robot_name, config in ROBOT_CONFIGS.items()]
    
    return [
        types.Tool(
            name="add_ground",
            description="Add ground plane to Isaac Sim DOF simulation",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="add_ball",
            description="Add ball object to Isaac Sim DOF simulation",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="add_robot",
            description="Add robot to Isaac Sim DOF simulation",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_name": {
                        "type": "string",
                        "description": "Name of the robot to add",
                        "enum": [choice["value"] for choice in robot_choices],
                        "enumTitles": [choice["title"] for choice in robot_choices]
                    }
                },
                "required": ["robot_name"]
            },
        ),
        types.Tool(
            name="list_robots",
            description="List all robots currently in the simulation",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="set_robot_positions",
            description="Set joint positions for a robot",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_name": {
                        "type": "string",
                        "description": "Name of the robot to control"
                    },
                    "positions": {
                        "type": "array",
                        "description": "Target joint positions in radians",
                        "items": {"type": "number"}
                    }
                },
                "required": ["robot_name", "positions"]
            },
        ),
        types.Tool(
            name="set_robot_velocities",
            description="Set joint velocities for a robot",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_name": {
                        "type": "string",
                        "description": "Name of the robot to control"
                    },
                    "velocities": {
                        "type": "array",
                        "description": "Target joint velocities in radians/second",
                        "items": {"type": "number"}
                    }
                },
                "required": ["robot_name", "velocities"]
            },
        ),
        types.Tool(
            name="get_robot_state",
            description="Get current joint positions and velocities of a robot",
            inputSchema={
                "type": "object",
                "properties": {
                    "robot_name": {
                        "type": "string",
                        "description": "Name of the robot to query"
                    }
                },
                "required": ["robot_name"]
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    try:
        # Initialize DOF simulation for Isaac Sim
        sim = DOF()
        
        if name == "add_ground":
            logger.info("Adding ground plane...")
            result = sim.add_ground()    # Add ground plane for physics interactions
            logger.info(f"Raw response from add_ground: {result}")
            return [types.TextContent(type="text", text="Ground added to DOF simulation")]
            
        elif name == "add_ball":
            logger.info("Adding ball...")
            result = sim.add_ball()      # Add ball object to the scene
            logger.info(f"Raw response from add_ball: {result}")
            return [types.TextContent(type="text", text="Ball added to DOF simulation")]
            
        elif name == "add_robot":
            robot_name = arguments.get("robot_name") if arguments else None
            if not robot_name:
                raise ValueError("Robot name must be specified")
            logger.info(f"Adding robot {robot_name}...")
            result = sim.add_robot(robot_name)  # Add specified robot to the simulation
            logger.info(f"Raw response from add_robot: {result}")
            try:
                if result and result.strip():
                    response = json.loads(result)
                    logger.info(f"Decoded response: {response}")
                    return [types.TextContent(type="text", text=f"{ROBOT_CONFIGS[robot_name]['name']} added to DOF simulation")]
                else:
                    logger.warning("Empty response from add_robot")
                    return [types.TextContent(type="text", text=f"{ROBOT_CONFIGS[robot_name]['name']} added to DOF simulation")]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response was: '{result}'")
                # If JSON decoding fails, still try to return a success message
                return [types.TextContent(type="text", text=f"{ROBOT_CONFIGS[robot_name]['name']} added to DOF simulation")]

        elif name == "list_robots":
            logger.info("Listing robots...")
            result = sim.list_robots()
            logger.info(f"Raw response from list_robots: {result}")
            try:
                if result and result.strip():
                    response = json.loads(result)
                    if response["status"] == "success":
                        # Handle both response formats
                        if "data" in response:
                            robots = response["data"]
                            if robots:
                                return [types.TextContent(type="text", text=f"Robots in simulation:\n" + "\n".join(robots))]
                            else:
                                return [types.TextContent(type="text", text="No robots found in simulation")]
                        else:
                            # Handle the generic success message format
                            return [types.TextContent(type="text", text=response.get("message", "No robots found in simulation"))]
                    else:
                        raise ValueError(response.get("message", "Unknown error listing robots"))
                else:
                    logger.warning("Empty response from list_robots")
                    return [types.TextContent(type="text", text="No robots found in simulation")]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response was: '{result}'")
                raise ValueError("Failed to decode response from Isaac Sim")

        elif name == "set_robot_positions":
            robot_name = arguments.get("robot_name") if arguments else None
            positions = arguments.get("positions") if arguments else None
            if not robot_name or positions is None:
                raise ValueError("Robot name and positions must be specified")
            
            logger.info(f"Setting positions for robot {robot_name}: {positions}")
            result = sim.set_joint_positions(robot_name, positions)
            logger.info(f"Raw response from set_joint_positions: {result}")
            try:
                if result and result.strip():
                    response = json.loads(result)
                    if response["status"] == "success":
                        return [types.TextContent(type="text", text=response["message"])]
                    else:
                        raise ValueError(response.get("message", "Unknown error setting positions"))
                else:
                    logger.warning("Empty response from set_joint_positions")
                    return [types.TextContent(type="text", text=f"Positions set for {robot_name}")]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response was: '{result}'")
                return [types.TextContent(type="text", text=f"Positions set for {robot_name}")]

        elif name == "set_robot_velocities":
            robot_name = arguments.get("robot_name") if arguments else None
            velocities = arguments.get("velocities") if arguments else None
            if not robot_name or velocities is None:
                raise ValueError("Robot name and velocities must be specified")
            
            logger.info(f"Setting velocities for robot {robot_name}: {velocities}")
            result = sim.set_joint_velocities(robot_name, velocities)
            logger.info(f"Raw response from set_joint_velocities: {result}")
            try:
                if result and result.strip():
                    response = json.loads(result)
                    if response["status"] == "success":
                        return [types.TextContent(type="text", text=response["message"])]
                    else:
                        raise ValueError(response.get("message", "Unknown error setting velocities"))
                else:
                    logger.warning("Empty response from set_joint_velocities")
                    return [types.TextContent(type="text", text=f"Velocities set for {robot_name}")]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response was: '{result}'")
                return [types.TextContent(type="text", text=f"Velocities set for {robot_name}")]

        elif name == "get_robot_state":
            robot_name = arguments.get("robot_name") if arguments else None
            if not robot_name:
                raise ValueError("Robot name must be specified")
            
            logger.info(f"Getting state for robot {robot_name}")
            result = sim.get_joint_states(robot_name)
            logger.info(f"Raw response from get_joint_states: {result}")
            try:
                if result and result.strip():
                    response = json.loads(result)
                    if response["status"] == "success":
                        state = response["data"]
                        state_str = f"Positions: {state['positions']}\nVelocities: {state['velocities']}"
                        return [types.TextContent(type="text", text=f"Robot {robot_name} state:\n{state_str}")]
                    else:
                        raise ValueError(response.get("message", "Unknown error getting state"))
                else:
                    logger.warning("Empty response from get_joint_states")
                    raise ValueError("No response received from Isaac Sim")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response was: '{result}'")
                raise ValueError("Failed to decode response from Isaac Sim")
            
        else:
            raise ValueError(f"Unknown tool: {name}")
            
    except Exception as e:
        logger.error(f"Error in handle_call_tool: {str(e)}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dof-sim",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())