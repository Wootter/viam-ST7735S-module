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
from viam.logging import getLogger
from viam.proto.service.vision import Classification, Detection
from viam.proto.service.vision import GetPropertiesResponse, CaptureAllFromCameraResponse

import asyncio
from PIL import Image, ImageDraw

LOGGER = getLogger(__name__)

class RobotFaceDisplay(Vision, Reconfigurable):
    """
    Vision Service for controlling ST7735S display to show robot faces
    
    Supported do_command operations:
    - set_face: {"command": "set_face", "expression": "happy|sad|surprised|sleepy|neutral|angry|confused|thinking"}
    - get_face: {"command": "get_face"}
    - clear: {"command": "clear"}
    - custom_text: {"command": "custom_text", "text": "Hello!", "x": 10, "y": 50}
    """
    
    MODEL: ClassVar[Model] = Model(ModelFamily("wootter", "vision"), "st7789")
    
    display = None
    current_face: str = "neutral"
    width: int = 240
    height: int = 240
    
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
        
        # Helper function to get value from protobuf Value object
        def get_int_attr(name: str, default: int) -> int:
            if name not in attrs:
                return default
            value = attrs[name]
            # Handle both direct values and protobuf Value objects
            if hasattr(value, 'number_value'):
                return int(value.number_value)
            elif isinstance(value, (int, float)):
                return int(value)
            else:
                return default
        
        # Get pin configuration (with defaults)
        cs_pin_num = get_int_attr("cs_pin", 8)
        dc_pin_num = get_int_attr("dc_pin", 25)
        reset_pin_num = get_int_attr("reset_pin", 24)
        backlight_pin_num = get_int_attr("backlight_pin", 18) # <-- ADDED
        rotation = get_int_attr("rotation", 90)
        
        # Optional: custom width/height
        self.width = get_int_attr("width", 240)
        self.height = get_int_attr("height", 240)
        
        try:
            # Import hardware libraries (only when actually running on Pi)
            import board
            import digitalio
            from adafruit_rgb_display import st7789
            
            # Setup GPIO pins
            cs_pin = digitalio.DigitalInOut(getattr(board, f"D{cs_pin_num}"))
            dc_pin = digitalio.DigitalInOut(getattr(board, f"D{dc_pin_num}"))
            reset_pin = digitalio.DigitalInOut(getattr(board, f"D{reset_pin_num}"))
            backlight_pin = digitalio.DigitalInOut(getattr(board, f"D{backlight_pin_num}")) # <-- ADDED
            
            # Initialize display
            self.display = st7789.ST7789(
                board.SPI(),
                cs=cs_pin,
                dc=dc_pin,
                rst=reset_pin,
                baudrate=24000000, # <-- ADDED: Faster SPI
                rotation=rotation,
                width=self.width,
                height=self.height,
                backlight_pin=backlight_pin # <-- ADDED
            )
            backlight_pin.switch_to_output(value=True) # <-- ADDED: Turn on backlight

            LOGGER.info(f"ST7789 display initialized (pins: CS={cs_pin_num}, DC={dc_pin_num}, RST={reset_pin_num}, BL={backlight_pin_num})")
            
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
        
        # Face positioning (scaled for 240x240)
        center_x = self.width // 2
        eye_y = self.height // 3
        eye_spacing = self.width // 4  # Approx 60px
        eye_radius = self.width // 12 # Approx 20px
        mouth_y = int(self.height * 0.7)
        mouth_width = self.width // 3 # Approx 80px
        line_width = 6

        # Draw based on expression
        if expression == "happy":
            # Happy eyes (circles)
            draw.ellipse((center_x - eye_spacing - eye_radius, eye_y - eye_radius, center_x - eye_spacing + eye_radius, eye_y + eye_radius), fill=(0, 255, 255))
            draw.ellipse((center_x + eye_spacing - eye_radius, eye_y - eye_radius, center_x + eye_spacing + eye_radius, eye_y + eye_radius), fill=(0, 255, 255))
            # Big smile
            draw.arc((center_x - mouth_width//2, mouth_y - 20, center_x + mouth_width//2, mouth_y + 20), 
                    start=0, end=180, fill=(255, 255, 0), width=line_width)

        elif expression == "sad":
            # Sad eyes (half-closed)
            draw.arc((center_x - eye_spacing - eye_radius, eye_y, center_x - eye_spacing + eye_radius, eye_y + eye_radius*1.5), 
                    start=180, end=360, fill=(100, 100, 255), width=line_width)
            draw.arc((center_x + eye_spacing - eye_radius, eye_y, center_x + eye_spacing + eye_radius, eye_y + eye_radius*1.5), 
                    start=180, end=360, fill=(100, 100, 255), width=line_width)
            # Frown
            draw.arc((center_x - mouth_width//2, mouth_y, center_x + mouth_width//2, mouth_y + 40), 
                    start=180, end=360, fill=(255, 100, 100), width=line_width)

        elif expression == "surprised":
            # Wide open eyes
            draw.ellipse((center_x - eye_spacing - eye_radius, eye_y - eye_radius, center_x - eye_spacing + eye_radius, eye_y + eye_radius), fill=(255, 255, 255))
            draw.ellipse((center_x + eye_spacing - eye_radius, eye_y - eye_radius, center_x + eye_spacing + eye_radius, eye_y + eye_radius), fill=(255, 255, 255))
            # Small pupils
            pupil_radius = eye_radius // 3
            draw.ellipse((center_x - eye_spacing - pupil_radius, eye_y - pupil_radius, center_x - eye_spacing + pupil_radius, eye_y + pupil_radius), fill=(0, 0, 0))
            draw.ellipse((center_x + eye_spacing - pupil_radius, eye_y - pupil_radius, center_x + eye_spacing + pupil_radius, eye_y + pupil_radius), fill=(0, 0, 0))
            # Open mouth (O shape)
            draw.ellipse((center_x - 20, mouth_y, center_x + 20, mouth_y + 35), fill=(255, 255, 255))

        elif expression == "sleepy":
            # Closed eyes (horizontal lines)
            draw.line((center_x - eye_spacing - eye_radius, eye_y, center_x - eye_spacing + eye_radius, eye_y), fill=(200, 200, 200), width=line_width)
            draw.line((center_x + eye_spacing - eye_radius, eye_y, center_x + eye_spacing + eye_radius, eye_y), fill=(200, 200, 200), width=line_width)
            # Zzz
            draw.text((center_x + 60, eye_y - 50), "Z", fill=(150, 150, 150))
            draw.text((center_x + 75, eye_y - 70), "Z", fill=(100, 100, 100))
            # Small smile
            draw.arc((center_x - 30, mouth_y, center_x + 30, mouth_y + 20), start=0, end=180, fill=(200, 200, 200), width=line_width-2)

        elif expression == "angry":
            # Angry eyes (angled lines)
            draw.line((center_x - eye_spacing - eye_radius, eye_y - 10, center_x - eye_spacing + eye_radius, eye_y + 10), fill=(255, 0, 0), width=line_width)
            draw.line((center_x + eye_spacing - eye_radius, eye_y + 10, center_x + eye_spacing + eye_radius, eye_y - 10), fill=(255, 0, 0), width=line_width)
            # Angry mouth
            draw.line((center_x - mouth_width//2, mouth_y + 15, center_x + mouth_width//2, mouth_y), fill=(255, 0, 0), width=line_width)

        elif expression == "confused":
            # Eyes at different heights
            draw.ellipse((center_x - eye_spacing - eye_radius, eye_y - eye_radius, center_x - eye_spacing + eye_radius, eye_y + eye_radius), fill=(255, 255, 255))
            draw.ellipse((center_x + eye_spacing - eye_radius, eye_y - eye_radius + 10, center_x + eye_spacing + eye_radius, eye_y + eye_radius + 10), fill=(255, 255, 255))
            # Pupils
            pupil_radius = eye_radius // 3
            draw.ellipse((center_x - eye_spacing - pupil_radius, eye_y - pupil_radius, center_x - eye_spacing + pupil_radius, eye_y + pupil_radius), fill=(0, 0, 0))
            draw.ellipse((center_x + eye_spacing - pupil_radius, eye_y - pupil_radius + 10, center_x + eye_spacing + pupil_radius, eye_y + pupil_radius + 10), fill=(0, 0, 0))
            # Squiggly mouth
            mouth_x = center_x - mouth_width//2
            draw.line((mouth_x, mouth_y + 5, mouth_x + 20, mouth_y - 5), fill=(200, 200, 0), width=line_width)
            draw.line((mouth_x + 20, mouth_y - 5, mouth_x + 40, mouth_y + 5), fill=(200, 200, 0), width=line_width)
            draw.line((mouth_x + 40, mouth_y + 5, mouth_x + 60, mouth_y - 5), fill=(200, 200, 0), width=line_width)

        elif expression == "thinking":
            # Spiral eyes
            for i in range(int(eye_radius / 2)):
                angle1 = i * 72
                angle2 = (i + 1) * 72
                r = i * 2
                # Left eye
                draw.arc((center_x - eye_spacing - r, eye_y - r, center_x - eye_spacing + r, eye_y + r),
                         start=angle1, end=angle2, fill=(100, 100, 255), width=3)
                # Right eye
                draw.arc((center_x + eye_spacing - r, eye_y - r, center_x + eye_spacing + r, eye_y + r),
                         start=angle1, end=angle2, fill=(100, 100, 255), width=3)
            # Thinking mouth
            draw.line((center_x - 25, mouth_y, center_x + 25, mouth_y), fill=(200, 200, 200), width=line_width)
            draw.line((center_x + 25, mouth_y, center_x + 35, mouth_y - 10), fill=(200, 200, 200), width=line_width)

        else:  # neutral
            # Neutral eyes (circles)
            draw.ellipse((center_x - eye_spacing - eye_radius, eye_y - eye_radius, center_x - eye_spacing + eye_radius, eye_y + eye_radius), fill=(255, 255, 255))
            draw.ellipse((center_x + eye_spacing - eye_radius, eye_y - eye_radius, center_x + eye_spacing + eye_radius, eye_y + eye_radius), fill=(255, 255, 255))
            # Pupils
            pupil_radius = eye_radius // 2
            draw.ellipse((center_x - eye_spacing - pupil_radius, eye_y - pupil_radius, center_x - eye_spacing + pupil_radius, eye_y + pupil_radius), fill=(0, 0, 0))
            draw.ellipse((center_x + eye_spacing - pupil_radius, eye_y - pupil_radius, center_x + eye_spacing + pupil_radius, eye_y + pupil_radius), fill=(0, 0, 0))
            # Straight mouth
            draw.line((center_x - mouth_width//2, mouth_y, center_x + mouth_width//2, mouth_y), fill=(200, 200, 200), width=line_width)
        
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
                valid_expressions = ["happy", "sad", "surprised", "sleepy", "angry", "neutral", "confused", "thinking"]
                
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
    async def get_detections(self, image: bytes, *, extra: Optional[Dict[str, Any]] = None, 
                            timeout: Optional[float] = None) -> List[Detection]:
        """Not implemented - display doesn't detect objects"""
        return []
    
    async def get_detections_from_camera(self, camera_name: str, *, extra: Optional[Dict[str, Any]] = None, 
                                        timeout: Optional[float] = None) -> List[Detection]:
        """Not implemented - display doesn't detect objects"""
        return []
    
    async def get_classifications(self, image: bytes, count: int, *, extra: Optional[Dict[str, Any]] = None, 
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
    
    async def capture_all_from_camera(self, camera_name: str, 
                                     return_image: bool = False,
                                     return_classifications: bool = False,
                                     return_detections: bool = False,
                                     return_object_point_clouds: bool = False,
                                     *, extra: Optional[Dict[str, Any]] = None,
                                     timeout: Optional[float] = None) -> CaptureAllFromCameraResponse:
        """Not implemented - display doesn't capture from cameras"""
        return CaptureAllFromCameraResponse()
    
    async def get_properties(self, *, extra: Optional[Dict[str, Any]] = None,
                            timeout: Optional[float] = None) -> GetPropertiesResponse:
        """Return properties of this vision service"""
        return GetPropertiesResponse(
            classifications_supported=False,
            detections_supported=False,
            object_point_clouds_supported=False
        )
    
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
