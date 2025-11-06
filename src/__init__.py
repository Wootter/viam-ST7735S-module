"""
Viam Vision Service module for ST7735S display to show robot face
"""

from viam.services.vision import Vision
from viam.resource.registry import Registry, ResourceCreatorRegistration

from .robot_face import RobotFaceDisplay

Registry.register_resource_creator(
    Vision.API,
    RobotFaceDisplay.MODEL,
    ResourceCreatorRegistration(RobotFaceDisplay.new, RobotFaceDisplay.validate)
)
