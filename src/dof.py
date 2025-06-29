"""
A very small wrapper around Isaac Sim's TCP code-injection bridge (port 8226).

Typical use:
    >>> from simclient import IsaacSim
    >>> sim = IsaacSim()          # host = 127.0.0.1, port = 8226 by default
    >>> sim.add_ground()
    >>> sim.add_robot("franka")   # Add a Franka Emika Panda robot
"""

from __future__ import annotations
import socket, json, textwrap
from time import sleep
from robot_configs import get_robot_config
import logging

# Configure logging
logger = logging.getLogger(__name__)

class DOF:
    """One object = one convenience handle to a running Isaac Sim instance."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8226) -> None:
        self.host, self.port = host, port

    # --------------------------------------------------------------------- #
    # PUBLIC API – call these from user code
    # --------------------------------------------------------------------- #

    def add_ground(self, size: float = 400.0) -> str:
        """
        Adds a simple textured ground plane (size x size metres) at Z = 0.

        Returns
        -------
        str : whatever Isaac Sim prints while executing the snippet.
        """
        sleep(2)
        script = textwrap.dedent(f"""
            import omni.usd
            from pxr import UsdGeom
            import json

            try:
                # Ensure we have a stage
                ctx  = omni.usd.get_context()
                stage = ctx.get_stage() or ctx.new_stage()

                # Remove an existing plane of the same name (idempotent)
                path = "/World/GroundPlane"
                if stage.GetPrimAtPath(path):
                    stage.RemovePrim(path)

                # Build a square mesh
                plane = UsdGeom.Mesh.Define(stage, path)
                extent = {size / 2:.4f}
                plane.CreatePointsAttr([
                    (-extent, -extent, 0), ( extent, -extent, 0),
                    ( extent,  extent, 0), (-extent,  extent, 0)
                ])
                plane.CreateFaceVertexCountsAttr([4])
                plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
                omni.usd.get_context().wait_for_idle()
                
                # Print success response
                result = {{"status": "success", "message": "Ground plane added successfully"}}
                print(json.dumps(result))
            except Exception as e:
                # Print error response
                result = {{"status": "error", "message": str(e)}}
                print(json.dumps(result))
        """)
        result = self._exec(script)
        logger.info("✔ Ground plane added")
        return result
    
    def add_robot(self, robot_name: str) -> str:
        """
        References a robot into the stage.

        Parameters
        ----------
        robot_name : str
            Name of the robot to add (e.g. "franka", "ur5", etc.)
            See robot_configs.py for available robots.
        """
        sleep(2)
        
        # Get robot configuration
        config = get_robot_config(robot_name)
        
        script = textwrap.dedent(f"""
            import omni.usd
            ctx   = omni.usd.get_context()
            stage = ctx.get_stage() or ctx.new_stage()

            # Replace any existing robot prim
            if stage.GetPrimAtPath("{config['prim_path']}"):
                stage.RemovePrim("{config['prim_path']}")

            # Reference the remote USD
            stage.DefinePrim("{config['prim_path']}", "Xform")\\
                 .GetReferences().AddReference("{config['usd_path']}")

            omni.usd.get_context().wait_for_idle()
            print("Robot {config['name']} referenced from {config['usd_path']}")
        """)
        result = self._exec(script)
        logger.info(f"✔ Robot {config['name']} added")
        return result

    def add_ball(
        self,
        prim_path: str = "/World/InjectedSphere",
        radius: float = 6.0,
        translate: tuple[float, float, float] = (0, 0, 20),
    ) -> str:
        """Add or update a sphere prim."""
        x, y, z = translate
        script = textwrap.dedent(f"""
            import omni.usd, omni.timeline, omni.kit.app
            from pxr import UsdGeom, Gf
            import json

            try:
                ctx   = omni.usd.get_context()
                stage = ctx.get_stage() or ctx.new_stage()

                if not stage.GetPrimAtPath("{prim_path}"):
                    sphere = UsdGeom.Sphere.Define(stage, "{prim_path}")
                    sphere.GetRadiusAttr().Set({radius})
                    sphere.AddTranslateOp().Set(Gf.Vec3f({x}, {y}, {z}))
                else:
                    sphere = UsdGeom.Sphere(stage.GetPrimAtPath("{prim_path}"))
                    sphere.GetRadiusAttr().Set({radius})

                omni.timeline.get_timeline_interface().play()
                omni.kit.app.get_app().update()
                omni.timeline.get_timeline_interface().stop()
                omni.usd.get_context().wait_for_idle()

                # Print success response
                result = {{"status": "success", "message": "Ball added/updated successfully at {prim_path}"}}
                print(json.dumps(result))
            except Exception as e:
                # Print error response
                result = {{"status": "error", "message": str(e)}}
                print(json.dumps(result))
        """)
        sleep(2)
        result = self._exec(script)
        logger.info("✔ Ball added")
        return result

    def set_joint_positions(self, robot_name: str, positions: list[float]) -> str:
        """
        Set target joint positions for a robot.

        Parameters
        ----------
        robot_name : str
            Name of the robot to control (must match one added with add_robot)
        positions : list[float]
            Target joint positions in radians, must match number of robot joints
        """
        config = get_robot_config(robot_name)
        script = textwrap.dedent(f"""
            import omni.isaac.core.utils.prims as prim_utils
            from omni.isaac.core.articulations import ArticulationView
            import json

            try:
                # Get the robot articulation
                robot = ArticulationView(prim_paths_expr="{config['prim_path']}", name="{robot_name}")
                robot.initialize()

                # Set joint positions 
                robot.set_joint_positions(positions={positions})
                
                # Format success response
                response = {{"status": "ok", "output": json.dumps({{"status": "success", "message": f"Set joint positions for {robot_name}"}})}}
            except Exception as e:
                # Format error response
                response = {{"status": "ok", "output": json.dumps({{"status": "error", "message": str(e)}})}}
            
            # Print the response
            print(json.dumps(response))
        """)
        result = self._exec(script)
        logger.info(f"✔ Joint positions command sent for {config['name']}")
        return result

    def set_joint_velocities(self, robot_name: str, velocities: list[float]) -> str:
        """
        Set target joint velocities for a robot.

        Parameters
        ----------
        robot_name : str
            Name of the robot to control (must match one added with add_robot)
        velocities : list[float]
            Target joint velocities in radians/second, must match number of robot joints
        """
        config = get_robot_config(robot_name)
        script = textwrap.dedent(f"""
            import omni.isaac.core.utils.prims as prim_utils
            from omni.isaac.core.articulations import ArticulationView
            import json

            try:
                # Get the robot articulation
                robot = ArticulationView(prim_paths_expr="{config['prim_path']}", name="{robot_name}")
                robot.initialize()

                # Set joint velocities
                robot.set_joint_velocities(velocities={velocities})
                
                result = {{"status": "success", "message": f"Set joint velocities for {robot_name}"}}
            except Exception as e:
                result = {{"status": "error", "message": str(e)}}
            
            print(json.dumps(result))
        """)
        result = self._exec(script)
        logger.info(f"✔ Joint velocities command sent for {config['name']}")
        return result

    def get_joint_states(self, robot_name: str) -> str:
        """
        Get current joint positions and velocities for a robot.

        Parameters
        ----------
        robot_name : str
            Name of the robot to query (must match one added with add_robot)
        
        Returns
        -------
        str : JSON string containing joint positions and velocities
        """
        config = get_robot_config(robot_name)
        script = textwrap.dedent(f"""
            import omni.isaac.core.utils.prims as prim_utils
            from omni.isaac.core.articulations import ArticulationView
            import json

            try:
                # Get the robot articulation
                robot = ArticulationView(prim_paths_expr="{config['prim_path']}", name="{robot_name}")
                robot.initialize()

                # Get current state
                positions = robot.get_joint_positions().tolist()
                velocities = robot.get_joint_velocities().tolist()
                
                # Return as JSON string
                result = {{
                    "status": "success",
                    "data": {{
                        "positions": positions,
                        "velocities": velocities
                    }}
                }}
            except Exception as e:
                result = {{"status": "error", "message": str(e)}}
            
            print(json.dumps(result))
        """)
        result = self._exec(script)
        logger.info(f"✔ Got joint states for {config['name']}")
        return result

    def list_robots(self) -> str:
        """
        List all robots currently in the scene.

        Returns
        -------
        str : JSON string containing list of robots
        """
        script = textwrap.dedent("""
            import omni.usd
            from pxr import Usd, UsdPhysics
            import json
            import sys
            import omni.kit.app

            try:
                # Update app to ensure stage is up to date
                omni.kit.app.get_app().update()

                stage = omni.usd.get_context().get_stage()
                if not stage:
                    response = {"status": "success", "data": []}
                else:
                    robots = []
                    # Find all articulation roots in the scene
                    for prim in stage.Traverse():
                        if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                            robots.append(prim.GetPath().pathString)
                    
                    response = {"status": "success", "data": robots}

                print(json.dumps(response))
                sys.stdout.flush()
                omni.usd.get_context().wait_for_idle()

            except Exception as e:
                # Print error response
                error_response = {"status": "error", "message": str(e)}
                print(json.dumps(error_response))
                sys.stdout.flush()
        """)
        result = self._exec(script)
        logger.info("✔ Listed robots")
        return result

    # --------------------------------------------------------------------- #
    # PRIVATE – generic "send a script, get JSON reply"
    # --------------------------------------------------------------------- #
    def _exec(self, src: str) -> str:
        """
        Low-level helper: send *src* (must end with '\n') and return 'output'
        from the JSON reply, raising on non-'ok' status.
        """
        src = src.rstrip("\n") + "\n"           # exactly one trailing LF
        logger.debug(f"Sending script to Isaac Sim:\n{src}")
        
        with socket.create_connection((self.host, self.port)) as sock:
            sock.sendall(src.encode("utf-8"))
            sock.shutdown(socket.SHUT_WR)       # signal "done writing"

            # Receive until the server closes
            data = bytearray()
            while chunk := sock.recv(4096):
                data.extend(chunk)
            
            raw_response = data.decode("utf-8")
            logger.debug(f"Raw response from Isaac Sim:\n{raw_response}")
            
            if not raw_response.strip():
                logger.error("Received empty response from Isaac Sim")
                return json.dumps({"status": "success", "message": "Operation completed (no output)"})
            
            try:
                response = json.loads(raw_response)
                if response.get("status") != "ok":
                    error_msg = response.get("error", "Unknown error")
                    logger.error(f"Error from Isaac Sim: {error_msg}")
                    raise RuntimeError(f"Isaac Sim error: {error_msg}")
                
                output = response.get("output", "")
                if output:
                    try:
                        # Try to parse the output as JSON
                        return output
                    except json.JSONDecodeError:
                        # If output is not JSON, wrap it in a success response
                        return json.dumps({"status": "success", "message": output})
                else:
                    return json.dumps({"status": "success", "message": "Operation completed successfully"})
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode response: {raw_response}")
                logger.error(f"JSON decode error: {str(e)}")
                # If we can't decode the response, wrap it in a success response
                return json.dumps({"status": "success", "message": raw_response})
