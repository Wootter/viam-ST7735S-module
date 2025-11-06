"""
ST7735S Display Vision Service for Robot Face
Displays animated robot faces that can be controlled via Viam commands
"""

from typing import ClassVar, Mapping, Sequence, Any, Dict, Optional, List
from typing_extensions import Self
from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily
from viam.services.vision import Vision
from viam.media.video import RawImage
from viam.logging import getLogger
from viam.proto.service.vision import Classification, Detection

import asyncio
from PIL import Image, ImageDraw

LOGGER = getLogger(__name__)

class RobotFaceDisplay(Vision, Reconfigurable):
    """
    Vision Service for controlling ST7735S display to show robot faces
    
    Supported do_command operations:
    - set_face: {"command": "set_face", "expression": "happy|sad|surprised|sleepy|neutral"}
    - get_face: {"command": "get_face"}
    - clear: {"command": "clear"}
    - custom_text: {"command": "custom_text", "text": "Hello!", "x": 10, "y": 50}
    """
    
    MODEL: ClassVar[Model] = Model(ModelFamily("wootter", "vision"), "robot_face")
    
    display = None
    current_face: str = "neutral"
    width: int = 128
    height: int = 160
    
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        """Create new instance of RobotFaceDisplay"""
        service = cls(config.name)
        service.reconfigure(config, dependencies)
        return service
    
    @classmethod
    def validate(cls, config: ComponentConfig):
        """Validate configuration"""
        return [], []
    
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        """Configure the display hardware"""
        attrs = config.attributes.fields
        
        # Get pin configuration (with defaults)
        cs_pin_num = int(attrs.get("cs_pin", {}).number_value or 8)
        dc_pin_num = int(attrs.get("dc_pin", {}).number_value or 25)
        reset_pin_num = int(attrs.get("reset_pin", {}).number_value or 24)
        rotation = int(attrs.get("rotation", {}).number_value or 90)
        
        # Optional: custom width/height
        self.width = int(attrs.get("width", {}).number_value or 128)
        self.height = int(attrs.get("height", {}).number_value or 160)
        
        try:
            # Import hardware libraries (only when actually running on Pi)
            import board
            import digitalio
            from adafruit_rgb_display import st7735
            
            # Setup GPIO pins
            cs_pin = digitalio.DigitalInOut(getattr(board, f"D{cs_pin_num}"))
            dc_pin = digitalio.DigitalInOut(getattr(board, f"D{dc_pin_num}"))
            reset_pin = digitalio.DigitalInOut(getattr(board, f"D{reset_pin_num}"))
            
            # Initialize display
            self.display = st7735.ST7735S(
                board.SPI(),
                cs=cs_pin,
                dc=dc_pin,
                rst=reset_pin,
                rotation=rotation,
                width=self.width,
                height=self.height,
                bgr=True  # Color order for W180 display
            )
            
            LOGGER.info(f"ST7735S display initialized (pins: CS={cs_pin_num}, DC={dc_pin_num}, RST={reset_pin_num})")
            
            # Show initial neutral face
            self._draw_face("neutral")
            
        except ImportError as e:
            LOGGER.warning(f"Display libraries not available (probably not on Pi): {e}")
            self.display = None
        except Exception as e:
            raise Exception(f"Failed to initialize ST7735S display: {e}")
    
    def _draw_face(self, expression: str):
        """Draw a robot face with the given expression"""
        if self.display is None:
            LOGGER.warning("Display not initialized, skipping draw")
            return
        
        # Create black background
        image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Face positioning
        center_x = self.width // 2
        eye_y = self.height // 3
        eye_spacing = 35
        mouth_y = int(self.height * 0.65)
        
        # Draw based on expression
        if expression == "happy":
            # Happy eyes (circles)
            draw.ellipse((center_x - eye_spacing - 15, eye_y - 10, center_x - eye_spacing + 5, eye_y + 10), 
                        fill=(0, 255, 255))  # Cyan eyes
            draw.ellipse((center_x + eye_spacing - 5, eye_y - 10, center_x + eye_spacing + 15, eye_y + 10), 
                        fill=(0, 255, 255))
            # Big smile
            draw.arc((center_x - 30, mouth_y - 15, center_x + 30, mouth_y + 20), 
                    start=0, end=180, fill=(255, 255, 0), width=4)  # Yellow smile
        
        elif expression == "sad":
            # Sad eyes (half-closed)
            draw.arc((center_x - eye_spacing - 15, eye_y - 5, center_x - eye_spacing + 5, eye_y + 15), 
                    start=180, end=360, fill=(100, 100, 255), width=3)
            draw.arc((center_x + eye_spacing - 5, eye_y - 5, center_x + eye_spacing + 15, eye_y + 15), 
                    start=180, end=360, fill=(100, 100, 255), width=3)
            # Frown
            draw.arc((center_x - 25, mouth_y - 20, center_x + 25, mouth_y + 10), 
                    start=180, end=360, fill=(255, 100, 100), width=3)
        
        elif expression == "surprised":
            # Wide open eyes
            draw.ellipse((center_x - eye_spacing - 20, eye_y - 15, center_x - eye_spacing + 10, eye_y + 15), 
                        fill=(255, 255, 255))
            draw.ellipse((center_x + eye_spacing - 10, eye_y - 15, center_x + eye_spacing + 20, eye_y + 15), 
                        fill=(255, 255, 255))
            # Small pupils
            draw.ellipse((center_x - eye_spacing - 7, eye_y - 5, center_x - eye_spacing + 3, eye_y + 5), 
                        fill=(0, 0, 0))
            draw.ellipse((center_x + eye_spacing - 3, eye_y - 5, center_x + eye_spacing + 7, eye_y + 5), 
                        fill=(0, 0, 0))
            # Open mouth (O shape)
            draw.ellipse((center_x - 12, mouth_y - 5, center_x + 12, mouth_y + 20), 
                        fill=(255, 255, 255))
        
        elif expression == "sleepy":
            # Closed eyes (horizontal lines)
            draw.line((center_x - eye_spacing - 15, eye_y, center_x - eye_spacing + 5, eye_y), 
                     fill=(200, 200, 200), width=4)
            draw.line((center_x + eye_spacing - 5, eye_y, center_x + eye_spacing + 15, eye_y), 
                     fill=(200, 200, 200), width=4)
            # Zzz
            draw.text((center_x + 30, eye_y - 30), "Z", fill=(150, 150, 150))
            draw.text((center_x + 40, eye_y - 40), "Z", fill=(100, 100, 100))
            # Small smile
            draw.arc((center_x - 20, mouth_y - 5, center_x + 20, mouth_y + 10), 
                    start=0, end=180, fill=(200, 200, 200), width=2)
        
        elif expression == "angry":
            # Angry eyes (angled lines)
            draw.line((center_x - eye_spacing - 20, eye_y - 10, center_x - eye_spacing, eye_y), 
                     fill=(255, 0, 0), width=4)
            draw.line((center_x - eye_spacing - 15, eye_y, center_x - eye_spacing + 5, eye_y + 10), 
                     fill=(255, 0, 0), width=4)
            draw.line((center_x + eye_spacing, eye_y, center_x + eye_spacing + 20, eye_y - 10), 
                     fill=(255, 0, 0), width=4)
            draw.line((center_x + eye_spacing - 5, eye_y + 10, center_x + eye_spacing + 15, eye_y), 
                     fill=(255, 0, 0), width=4)
            # Angry mouth
            draw.line((center_x - 25, mouth_y, center_x + 25, mouth_y), 
                     fill=(255, 0, 0), width=4)
        
        else:  # neutral
            # Neutral eyes (circles)
            draw.ellipse((center_x - eye_spacing - 12, eye_y - 8, center_x - eye_spacing + 8, eye_y + 12), 
                        fill=(255, 255, 255))
            draw.ellipse((center_x + eye_spacing - 8, eye_y - 8, center_x + eye_spacing + 12, eye_y + 12), 
                        fill=(255, 255, 255))
            # Pupils
            draw.ellipse((center_x - eye_spacing - 5, eye_y - 2, center_x - eye_spacing + 5, eye_y + 8), 
                        fill=(0, 0, 0))
            draw.ellipse((center_x + eye_spacing - 5, eye_y - 2, center_x + eye_spacing + 5, eye_y + 8), 
                        fill=(0, 0, 0))
            # Straight mouth
            draw.line((center_x - 20, mouth_y, center_x + 20, mouth_y), 
                     fill=(200, 200, 200), width=3)
        
        # Display the image
        self.display.image(image)
        self.current_face = expression
        LOGGER.debug(f"Drew face: {expression}")
    
    async def do_command(self, command: Mapping[str, Any], *, timeout: Optional[float] = None, **kwargs) -> Mapping[str, Any]:
        """
        Handle custom commands
        
        Commands:
        - set_face: Change the robot's expression
        - get_face: Get current expression
        - clear: Clear the display
        - custom_text: Draw custom text (future feature)
        """
        
        def _execute_command():
            cmd = command.get("command")
            
            if cmd == "set_face":
                expression = command.get("expression", "neutral")
                valid_expressions = ["happy", "sad", "surprised", "sleepy", "angry", "neutral"]
                
                if expression not in valid_expressions:
                    return {
                        "success": False, 
                        "error": f"Invalid expression. Must be one of: {valid_expressions}"
                    }
                
                self._draw_face(expression)
                return {"success": True, "expression": expression}
            
            elif cmd == "get_face":
                return {"current_face": self.current_face}
            
            elif cmd == "clear":
                if self.display:
                    image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
                    self.display.image(image)
                return {"success": True}
            
            elif cmd == "custom_text":
                text = command.get("text", "")
                x = int(command.get("x", 10))
                y = int(command.get("y", 50))
                
                if self.display:
                    image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
                    draw = ImageDraw.Draw(image)
                    draw.text((x, y), text, fill=(255, 255, 255))
                    self.display.image(image)
                
                return {"success": True, "text": text}
            
            else:
                return {"success": False, "error": f"Unknown command: {cmd}"}
        
        return await asyncio.to_thread(_execute_command)
    
    # Vision service required methods (not used for display, but required by API)
    async def get_detections(self, image: RawImage, *, extra: Optional[Dict[str, Any]] = None, 
                            timeout: Optional[float] = None) -> List[Detection]:
        """Not implemented - display doesn't detect objects"""
        return []
    
    async def get_detections_from_camera(self, camera_name: str, *, extra: Optional[Dict[str, Any]] = None, 
                                        timeout: Optional[float] = None) -> List[Detection]:
        """Not implemented - display doesn't detect objects"""
        return []
    
    async def get_classifications(self, image: RawImage, count: int, *, extra: Optional[Dict[str, Any]] = None, 
                                 timeout: Optional[float] = None) -> List[Classification]:
        """Not implemented - display doesn't classify objects"""
        return []
    
    async def get_classifications_from_camera(self, camera_name: str, count: int, *, 
                                             extra: Optional[Dict[str, Any]] = None, 
                                             timeout: Optional[float] = None) -> List[Classification]:
        """Not implemented - display doesn't classify objects"""
        return []
    
    async def get_object_point_clouds(self, camera_name: str, *, extra: Optional[Dict[str, Any]] = None, 
                                     timeout: Optional[float] = None) -> List[Any]:
        """Not implemented - display doesn't generate point clouds"""
        return []
    
    async def close(self):
        """Clean up resources"""
        if self.display:
            try:
                # Clear display on shutdown
                image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
                self.display.image(image)
                LOGGER.info("Display cleared on shutdown")
            except Exception as e:
                LOGGER.error(f"Error clearing display: {e}")
