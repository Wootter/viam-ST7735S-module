"""
Entry point for the ST7735S robot face display module
"""

import asyncio
from viam.module.module import Module
from viam.services.vision import Vision
from .robot_face import RobotFaceDisplay

async def main():
    """Main entry point for the module"""
    module = Module.from_args()
    module.add_model_from_registry(Vision.API, RobotFaceDisplay.MODEL)
    await module.start()

if __name__ == "__main__":
    asyncio.run(main())
