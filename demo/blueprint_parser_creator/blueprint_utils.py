"""
Utility module for blueprint analysis and DXF creation.

This module encapsulates the core logic from the original bootcamp project
into a standalone set of classes and functions.  The goal is to expose the
heavy lifting (file conversion, feature extraction, blueprint modifications
and DXF generation) independently of any particular user interface.  These
classes will later be wrapped by Sherpa actions so that an agent can call
them in a controlled way.

To use this module directly you can instantiate the ``BlueprintAnalyzer``
class and call its methods.  For example::

    from blueprint_utils import BlueprintAnalyzer, create_dxf_plot
    analyzer = BlueprintAnalyzer()
    # Convert or ingest a blueprint file
    status = analyzer.handle_file_input("'/path/to/blueprint.dwg'")
    # Extract rooms and walls
    summary = analyzer.extract_features()
    # Query the area of a room
    room_area = analyzer.get_room_area("Kitchen")
    # Merge two rooms (now handled by LLM through ModifyBlueprint action)
    # analyzer._merge_rooms(["room1", "room2"], "merge room1 and room2")
    # Generate a report
    report = analyzer.generate_report()

Note that this module does not depend on Streamlit or any UI framework.

"""

import cloudconvert
import ezdxf
import logging
import os
# import re  # No longer needed - removed regex-based methods
from collections import defaultdict
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from typing import Any, Dict, List, Tuple, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables once at import time.  The CloudConvert API key
# is required for file conversions; if it is missing a ValueError will be
# raised when the CloudConvertJob is instantiated.
load_dotenv()
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")
if CLOUDCONVERT_API_KEY:
    cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

class CloudConvertJob:
    """
    Handles file conversion using the CloudConvert API.  Supported file
    extensions are automatically converted to DXF.  If the file is already
    a DXF it is passed through unchanged.
    """
    def __init__(self, api_key: str, convert_path: str) -> None:
        self.api_key = api_key
        self.convert_path = convert_path
        if self.api_key:
            cloudconvert.configure(api_key=self.api_key)

    def create_job(self) -> Dict[str, Any]:
        """Create a conversion job with CloudConvert."""
        payload = {
            "tasks": {
                "upload-my-file": {
                    "operation": "import/upload",
                    "filename": Path(self.convert_path).name,
                },
                "convert-my-file": {
                    "operation": "convert",
                    "input": "upload-my-file",
                    "output_format": "dxf",
                    "autocad_version": "2010",
                },
                "export-my-file": {
                    "operation": "export/url",
                    "input": "convert-my-file",
                },
            }
        }
        return cloudconvert.Job.create(payload=payload)

    def handle_file_input(self, user_input: str) -> str:
        """
        Processes a file path provided in quotes.  Converts files to DXF if
        necessary.  This function is a thin wrapper around CloudConvert
        operations; it is kept here for backward compatibility.

        Args:
            user_input: User input containing a file path in quotes

        Returns:
            Status message about the file processing
        """
        # Extract file path from quotes - simple string parsing instead of regex
        if "'" in user_input:
            parts = user_input.split("'")
            if len(parts) >= 2:
                file_path_str = parts[1].strip()
            else:
                return "Error: No valid file path found in input. Please provide the file path in quotes."
        else:
            return "Error: No valid file path found in input. Please provide the file path in quotes."
        file_path = Path(file_path_str).resolve()
        if not file_path.exists():
            return f"Error: File '{file_path}' does not exist."

        convertible_extensions = {
            ".ai", ".cdr", ".cgm", ".dwg", ".emf", ".eps", ".pdf", ".ps",
            ".sk", ".sk1", ".svg", ".svgz", ".vsd", ".wmf",
        }
        extension = file_path.suffix.lower()

        if extension == ".dxf":
            self.ingested_file_path = str(file_path)
            return f"DXF file ready at: {file_path}"

        if extension in convertible_extensions:
            if not self.api_key:
                return "Error: CLOUDCONVERT_API_KEY is not set; cannot perform conversion."
            try:
                job = self.create_job()
                self.upload_file(job)
                converted_file = self.download_file(job)
                self.ingested_file_path = converted_file
                return f"Converted file ready at: {converted_file}"
            except Exception as e:
                logging.error(f"Conversion error: {e}", exc_info=True)
                return f"Error: Could not convert file '{file_path}' to DXF. Details: {e}"
        return f"Error: Unsupported or unhandled file type '{extension}'."

    def upload_file(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to CloudConvert for processing."""
        try:
            upload_task_id = next(task['id'] for task in job['tasks'] if task['name'] == 'upload-my-file')
            upload_task = cloudconvert.Task.find(id=upload_task_id)
            return cloudconvert.Task.upload(file_name=self.convert_path, task=upload_task)
        except Exception as e:
            logging.error(f"Error uploading file: {e}", exc_info=True)
            raise

    def download_file(self, job: Dict[str, Any]) -> str:
        """Download the converted file from CloudConvert."""
        try:
            export_task_id = next(task['id'] for task in job['tasks'] if task['name'] == 'export-my-file')
            res = cloudconvert.Task.wait(id=export_task_id)
            file_info = res.get("result", {}).get("files", [{}])[0]
            return cloudconvert.download(filename=file_info['filename'], url=file_info['url'])
        except Exception as e:
            logging.error(f"Error downloading file: {e}", exc_info=True)
            raise

class BlueprintFeatureExtractor:
    """
    Extracts features from DXF blueprints using either layer-based or entity type
    mapping.  The extractor identifies walls, windows, doors, rooms and room
    names from a DXF file.  Internally it relies on shapely to represent
    geometry.
    """
    def __init__(self) -> None:
        self.layer_mapping = {
            "A-WALL": "walls",
            "WALL": "walls",
            "WALLS": "walls",
            "WALL-": "walls",  # Common prefix
            "A-GLAZ": "windows",
            "GLAZ": "windows",
            "WINDOW": "windows",
            "WINDOWS": "windows",
            "A-DOOR": "doors",
            "DOOR": "doors",
            "DOORS": "doors",
            "A-FLOR": "floors",
            "FLOOR": "floors",
            "FLOORS": "floors",
            "AREA-ASSIGN": "rooms",
            "ROOM": "rooms",
            "ROOMS": "rooms",
            "TEXT": "rooms_name",
            "TEXT-": "rooms_name",
            "LABEL": "rooms_name",
            "LABELS": "rooms_name",
            "NAME": "rooms_name",
            "NAMES": "rooms_name",
            "INFO": "rooms_name",
            "INFORMATION": "rooms_name",
            "TITLE": "rooms_name",
            "TITLES": "rooms_name",
            "HEADER": "rooms_name",
            "HEADERS": "rooms_name",
            "CAPTION": "rooms_name",
            "CAPTIONS": "rooms_name",
            "LEGEND": "rooms_name",
            "LEGENDS": "rooms_name",
            "NOTE": "rooms_name",
            "NOTES": "rooms_name",
            "DESCRIPTION": "rooms_name",
            "DESCRIPTIONS": "rooms_name",
            "COMMENT": "rooms_name",
            "COMMENTS": "rooms_name",
            "ANNOTATION": "rooms_name",
            "ANNOTATIONS": "rooms_name",
            "REFERENCE": "rooms_name",
            "REFERENCES": "rooms_name",
            "DETAIL": "rooms_name",
            "DETAILS": "rooms_name",
            "SPECIFICATION": "rooms_name",
            "SPECIFICATIONS": "rooms_name",
            "DIMENSION": "rooms_name",
            "DIMENSIONS": "rooms_name",
            "MEASUREMENT": "rooms_name",
            "MEASUREMENTS": "rooms_name",
            "SCALE": "rooms_name",
            "SCALES": "rooms_name",
            "UNITS": "rooms_name",
            "UNIT": "rooms_name",
            "SYMBOL": "rooms_name",
            "SYMBOLS": "rooms_name",
            "MARKER": "rooms_name",
            "MARKERS": "rooms_name",
            "INDICATOR": "rooms_name",
            "INDICATORS": "rooms_name",
            "IDENTIFIER": "rooms_name",
            "IDENTIFIERS": "rooms_name",
            "Rooms-Information": "rooms_name",
        }
        self.entity_mapping = {
            "walls": ["LINE", "LWPOLYLINE", "POLYLINE", "ARC"],  
            "windows": ["LINE", "LWPOLYLINE", "POLYLINE", "ARC"], 
            "doors": ["LINE", "LWPOLYLINE", "POLYLINE", "ARC"],    
            "rooms": ["LWPOLYLINE", "POLYLINE", "CIRCLE"],         
            "floors": ["LWPOLYLINE", "POLYLINE", "CIRCLE"],        
            "rooms_name": ["TEXT", "MTEXT", "ATTDEF"],            
        }
        # Storage for extracted features
        self.features: Dict[str, Any] = {
            "walls": [],
            "windows": [],
            "doors": [],
            "floors": [],
            "rooms": {},
            "rooms_name": [],
        }
        # LLM used to parse text labels into room names
        self.llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")

    def _parse_room_name(self, text: str) -> str:
        """Use an LLM to extract a clean room name from a raw text string."""
        system_prompt = """Extract the simple room name or number from the architectural text.
        Rules:
        1. Remove metadata like square footage, capacity, etc.
        2. Remove special characters and line breaks
        3. If there's a room number, prioritize it
        4. Keep the response brief and clean
        5. If no clear room name/number is found, return 'unnamed room'

        Examples:
        Input: "bldg.1, room 124^m^j125000-administration^m^jasf: 332"
        Output: "room 124"

        Input: "CONFERENCE ROOM A^m^jcap: 30^m^jasf: 450"
        Output: "conference room a"
        """
        try:
            response = self.llm.invoke(system_prompt + f"\n\nInput: {text}\nOutput: ")
            return response.content.strip().lower()
        except Exception as e:
            logging.warning(f"Error parsing room name '{text}': {e}")
            return "unnamed room"

    def extract_features(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract features from a DXF file.  Depending on whether the DXF uses
        standard layer names, the extractor will use a layer-based or entity
        based approach.

        Args:
            file_path: Path to the DXF file

        Returns:
            A tuple consisting of a human readable summary and a dictionary
            containing the extracted features.
        """
        # Clear any previous features
        for feature_type in self.features:
            if isinstance(self.features[feature_type], dict):
                self.features[feature_type].clear()
            else:
                self.features[feature_type].clear()

        absolute_path = Path(file_path).resolve()
        if not absolute_path.exists():
            return (f"Error: File '{absolute_path}' does not exist.", {})
        try:
            doc = ezdxf.readfile(str(absolute_path))
            msp = doc.modelspace()
        except IOError as e:
            logging.error(f"IO error reading DXF file: {e}", exc_info=True)
            return (f"Error: Cannot read DXF file '{file_path}'. {str(e)}", {})
        except Exception as e:
            logging.error(f"Error during feature extraction: {e}", exc_info=True)
            return (f"Error during feature extraction: {str(e)}", {})

        uses_standard_layers = any(layer in doc.layers for layer in self.layer_mapping.keys())
        if uses_standard_layers:
            self._extract_by_layers(msp)
        else:
            self._extract_by_entity_type(msp)

        # Match text labels with polygons
        self._match_rooms_with_names()
        return (self._generate_summary(), self.features)

    def _extract_by_layers(self, msp) -> None:
        """Extract features based on standard layer names."""
        temp_rooms = []
        for entity in msp.query('*'):
            layer_name = entity.dxf.layer
            if layer_name in self.layer_mapping:
                feature_type = self.layer_mapping[layer_name]
                if feature_type in ["walls", "windows", "doors"]:
                    if entity.dxftype() == "LINE":
                        self._process_line_entity(entity, feature_type)
                elif feature_type == "rooms":
                    if entity.dxftype() == "LWPOLYLINE" and entity.closed:
                        points = [(x, y) for x, y, *_ in entity.get_points()]
                        temp_rooms.append(Polygon(points))
                elif feature_type == "rooms_name":
                    if entity.dxftype() in ["TEXT", "MTEXT"]:
                        self._process_text_entity(entity)
        self.features["_temp_rooms"] = temp_rooms

    def _extract_by_entity_type(self, msp) -> None:
        """Extract features based on entity types when no standard layers are present."""
        temp_rooms = []
        
        # Debug wall extraction
        wall_entities = []
        if isinstance(self.entity_mapping["walls"], list):
            for entity_type in self.entity_mapping["walls"]:
                entities = list(msp.query(entity_type))
                wall_entities.extend(entities)
                logging.info(f"Found {len(entities)} {entity_type} entities")
        else:
            wall_entities = list(msp.query(self.entity_mapping["walls"]))
            logging.info(f"Found {len(wall_entities)} {self.entity_mapping['walls']} entities")
        
        logging.info(f"Total wall entities found: {len(wall_entities)}")
        
        for entity in wall_entities:
            self._process_line_entity(entity, "walls")
        
        # Extract windows and doors using same entity types
        for feature_type in ["windows", "doors"]:
            entities = []
            if isinstance(self.entity_mapping[feature_type], list):
                for entity_type in self.entity_mapping[feature_type]:
                    feature_entities = list(msp.query(entity_type))
                    entities.extend(feature_entities)
                    logging.info(f"Found {len(feature_entities)} {entity_type} entities for {feature_type}")
            else:
                entities = list(msp.query(self.entity_mapping[feature_type]))
                logging.info(f"Found {len(entities)} {self.entity_mapping[feature_type]} entities for {feature_type}")
            
            logging.info(f"Total {feature_type} entities found: {len(entities)}")
            
            for entity in entities:
                self._process_line_entity(entity, feature_type)
        
        # Extract floors using multiple entity types
        floor_entities = []
        if isinstance(self.entity_mapping["floors"], list):
            for entity_type in self.entity_mapping["floors"]:
                entities = list(msp.query(entity_type))
                floor_entities.extend(entities)
                logging.info(f"Found {len(entities)} {entity_type} entities for floors")
        else:
            floor_entities = list(msp.query(self.entity_mapping["floors"]))
            logging.info(f"Found {len(entities)} {self.entity_mapping['floors']} entities for floors")
        
        logging.info(f"Total floor entities found: {len(floor_entities)}")
        
        for entity in floor_entities:
            if entity.dxftype() == "LWPOLYLINE" and entity.closed:
                points = [(x, y) for x, y, *_ in entity.get_points()]
                temp_rooms.append(Polygon(points))  # Add floors to temp_rooms for now
            elif entity.dxftype() == "POLYLINE" and entity.is_closed:
                vertices = list(entity.vertices)
                points = [(v.dxf.location.x, v.dxf.location.y) for v in vertices]
                temp_rooms.append(Polygon(points))
            elif entity.dxftype() == "CIRCLE":
                # For circles, create a polygon approximation
                center = entity.dxf.center
                radius = entity.dxf.radius
                import math
                # Create a 32-sided polygon approximation of the circle
                points = []
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                temp_rooms.append(Polygon(points))
        
        # Extract rooms using multiple entity types
        room_entities = []
        if isinstance(self.entity_mapping["rooms"], list):
            for entity_type in self.entity_mapping["rooms"]:
                entities = list(msp.query(entity_type))
                room_entities.extend(entities)
                logging.info(f"Found {len(entities)} {entity_type} entities for rooms")
        else:
            room_entities = list(msp.query(self.entity_mapping["rooms"]))
            logging.info(f"Found {len(entities)} {self.entity_mapping['rooms']} entities for rooms")
        
        logging.info(f"Total room entities found: {len(room_entities)}")
        
        for entity in room_entities:
            if entity.dxftype() == "LWPOLYLINE" and entity.closed:
                points = [(x, y) for x, y, *_ in entity.get_points()]
                temp_rooms.append(Polygon(points))
            elif entity.dxftype() == "POLYLINE" and entity.is_closed:
                vertices = list(entity.vertices)
                points = [(v.dxf.location.x, v.dxf.location.y) for v in vertices]
                temp_rooms.append(Polygon(points))
            elif entity.dxftype() == "CIRCLE":
                # For circles, create a polygon approximation
                center = entity.dxf.center
                radius = entity.dxf.radius
                import math
                # Create a 32-sided polygon approximation of the circle
                points = []
                for i in range(32):
                    angle = 2 * math.pi * i / 32
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                temp_rooms.append(Polygon(points))
        # Extract text labels using multiple entity types
        text_entities = []
        if isinstance(self.entity_mapping["rooms_name"], list):
            for entity_type in self.entity_mapping["rooms_name"]:
                entities = list(msp.query(entity_type))
                text_entities.extend(entities)
                logging.info(f"Found {len(entities)} {entity_type} entities for text labels")
        else:
            text_entities = list(msp.query(self.entity_mapping["rooms_name"]))
            logging.info(f"Found {len(entities)} {self.entity_mapping['rooms_name']} entities for text labels")
        
        logging.info(f"Total text entities found: {len(text_entities)}")
        
        for entity in text_entities:
            self._process_text_entity(entity)
        self.features["_temp_rooms"] = temp_rooms

    def _process_line_entity(self, entity, feature_type: str) -> None:
        if entity.dxftype() == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            wall_polygon = Polygon([
                (start[0], start[1]),
                (end[0], end[1]),
                (end[0] + 0.1, end[1] + 0.1),
                (start[0] + 0.1, start[1] + 0.1),
            ])
        elif entity.dxftype() == "LWPOLYLINE":
            # For LWPOLYLINE, get the points and create a line segment
            points = list(entity.get_points())
            if len(points) >= 2:
                start = points[0][:2]  # First point
                end = points[1][:2]    # Second point
                wall_polygon = Polygon([
                    (start[0], start[1]),
                    (end[0], end[1]),
                    (end[0] + 0.1, end[1] + 0.1),
                    (start[0] + 0.1, start[1] + 0.1),
                ])
            else:
                logging.warning(f"LWPOLYLINE entity has insufficient points: {len(points)}")
                return
        elif entity.dxftype() == "POLYLINE":
            # For POLYLINE, get the vertices and create a line segment
            vertices = list(entity.vertices)
            if len(vertices) >= 2:
                start = (vertices[0].dxf.location.x, vertices[0].dxf.location.y)
                end = (vertices[1].dxf.location.x, vertices[1].dxf.location.y)
                wall_polygon = Polygon([
                    (start[0], start[1]),
                    (end[0], end[1]),
                    (end[0] + 0.1, end[1] + 0.1),
                    (start[0] + 0.1, start[1] + 0.1),
                ])
            else:
                logging.warning(f"POLYLINE entity has insufficient vertices: {len(vertices)}")
                return
        elif entity.dxftype() == "ARC":
            # For ARC, create a line segment from start to end points
            start_angle = entity.dxf.start_angle
            end_angle = entity.dxf.end_angle
            center = entity.dxf.center
            radius = entity.dxf.radius
            
            # Convert angles to radians and calculate start/end points
            import math
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            start = (center[0] + radius * math.cos(start_rad), center[1] + radius * math.sin(start_rad))
            end = (center[0] + radius * math.cos(end_rad), center[1] + radius * math.sin(end_rad))
            
            wall_polygon = Polygon([
                (start[0], start[1]),
                (end[0], end[1]),
                (end[0] + 0.1, end[1] + 0.1),
                (start[0] + 0.1, start[1] + 0.1),
            ])
        else:
            logging.warning(f"Unsupported entity type for walls: {entity.dxftype()}")
            return
            
        self.features[feature_type].append(wall_polygon)
        logging.info(f"Processed {feature_type} entity ({entity.dxftype()}): start={start}, end={end}")

    def _process_text_entity(self, entity) -> None:
        text = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
        x, y, _ = entity.dxf.insert
        self.features["rooms_name"].append({"content": text.strip(), "pos": (x, y)})

    def _match_rooms_with_names(self) -> None:
        temp_rooms = self.features.pop("_temp_rooms", [])
        for poly in temp_rooms:
            found_label = None
            for lbl in self.features["rooms_name"]:
                pt = Point(lbl["pos"])
                if pt.within(poly):
                    found_label = self._parse_room_name(lbl["content"].strip())
                    break
            if found_label and found_label != "unnamed room":
                self.features["rooms"][found_label] = poly
            else:
                room_id = f"unnamed_room_{len(self.features['rooms']) + 1}"
                self.features["rooms"][room_id] = poly

    def _generate_summary(self) -> str:
        summary_lines = ["Feature Extraction Summary:"]
        for feature_type, features in self.features.items():
            if features and not feature_type.startswith('_'):
                count = len(features)
                summary_lines.append(f"- {feature_type}: {count} elements")
        return "\n".join(summary_lines)

class BlueprintAnalyzer:
    """
    Encapsulates blueprint ingestion, feature extraction, modifications and
    reporting.  The analyzer keeps track of an ingested DXF file and
    extracted features.  Methods on this class are used by Sherpa actions
    to perform operations on the blueprint.
    """
    def __init__(self) -> None:
        self.ingested_file_path: Optional[str] = None
        self.original_filename: Optional[str] = None 
        self.features: Dict[str, Any] = {
            "rooms": {},
            "walls": [],
            "doors": [],
            "windows": [],
        }
        self.extractor = BlueprintFeatureExtractor()
        self.converter = CloudConvertJob(api_key=CLOUDCONVERT_API_KEY or "", convert_path="")
        self.spatial_analyzer = SpatialAnalyzer()
        self.last_removed_rooms = []  # Track recently removed rooms
        self.operation_history = []  # Track operations for duplicate prevention

    def handle_file_input(self, user_input: str) -> str:
        """
        Process a file path provided in quotes.  Converts files to DXF if
        necessary and updates ``ingested_file_path``.

        Args:
            user_input: File path inside single quotes

        Returns:
            A status message describing the outcome of the operation
        """
        # Extract file path from quotes - simple string parsing instead of regex
        if "'" in user_input:
            parts = user_input.split("'")
            if len(parts) >= 2:
                file_path_str = parts[1].strip()
            else:
                return "Error: No valid file path found in input. Please provide the file path in quotes."
        else:
            return "Error: No valid file path found in input. Please provide the file path in quotes."
        file_path = Path(file_path_str).resolve()
        if not file_path.exists():
            return f"Error: File '{file_path}' does not exist."
        
        # Store the original filename for display purposes
        self.original_filename = file_path.name
        
        convertible_extensions = {
            ".ai", ".cdr", ".cgm", ".dwg", ".emf", ".eps", ".pdf", ".ps",
            ".sk", ".sk1", ".svg", ".svgz", ".vsd", ".wmf",
        }
        extension = file_path.suffix.lower()
        if extension == ".dxf":
            self.ingested_file_path = str(file_path)
            return f"DXF file ready at: {file_path}"
        if extension in convertible_extensions:
            self.converter.convert_path = str(file_path)
            try:
                job = self.converter.create_job()
                self.converter.upload_file(job)
                converted_file = self.converter.download_file(job)
                self.ingested_file_path = converted_file
                return f"Converted file ready at: {converted_file}"
            except Exception as e:
                logging.error(f"Conversion error: {e}", exc_info=True)
                return f"Error: Could not convert file '{file_path}' to DXF. Details: {e}"
        return f"Error: Unsupported or unhandled file type '{extension}'."

    def extract_features(self) -> str:
        """
        Identify rooms and walls by matching text labels with polygons.  This
        method populates ``self.features`` and returns a summary of the
        extracted features.
        """
        if not self.ingested_file_path:
            return "Error: No file path set. Please handle the file input first."
        
        # Clear existing features to allow re-extraction
        self.features["rooms"] = {}
        self.features["walls"] = []
        self.features["doors"] = []
        self.features["windows"] = []
        
        summary, features = self.extractor.extract_features(str(self.ingested_file_path))
        self.features["rooms"] = features.get("rooms", {})
        self.features["walls"] = features.get("walls", [])
        self.features["doors"] = features.get("doors", [])
        self.features["windows"] = features.get("windows", [])
        
        # Add debugging information
        if not self.features["rooms"]:
            summary += "\n\nWARNING: No rooms were successfully matched. Room names were found but not matched to polygons."
        
        return summary

    def get_room_area(self, room_name: str) -> str:
        """
        Return the area of the specified room.  If the room is not found,
        return a message listing available rooms.
        """
        try:
            # Add some debugging information
            if not self.features or "rooms" not in self.features:
                return "Error: No rooms have been extracted. Please run feature extraction first."
            
            normalized = room_name.strip().lower()
            room_mapping = {key.lower(): key for key in self.features["rooms"]}
            
            if normalized in room_mapping:
                original_name = room_mapping[normalized]
                poly = self.features["rooms"][original_name]
                area_value = poly.area
                return f"The area of '{original_name}' is {area_value:.2f} square units."
            
            available_rooms = ", ".join(self.features.get('rooms', {}).keys()) or "No rooms available"
            return f"Room '{room_name}' not found. Available rooms: {available_rooms}"
        except Exception as e:
            # Return a helpful error message instead of crashing
            return f"Error calculating room area for '{room_name}': {str(e)}"

    def _is_duplicate_operation(self, operation_type: str, room_names: List[str], description: str) -> bool:
        """Check if this operation is a duplicate of a recent operation."""
        operation_signature = f"{operation_type}:{','.join(sorted(room_names))}:{description}"
        
        # Check if this exact operation was performed recently
        if operation_signature in self.operation_history:
            logging.warning(f"Duplicate operation detected: {operation_signature}")
            return True
        
        # Check if rooms were recently removed
        for room in room_names:
            if room.lower() in self.last_removed_rooms:
                logging.warning(f"Room '{room}' was recently removed, operation may be duplicate")
                return True
        
        return False

    def _record_operation(self, operation_type: str, room_names: List[str], description: str) -> None:
        """Record an operation to prevent duplicates."""
        operation_signature = f"{operation_type}:{','.join(sorted(room_names))}:{description}"
        self.operation_history.append(operation_signature)
        
        # Keep only last 10 operations to prevent memory bloat
        if len(self.operation_history) > 10:
            self.operation_history.pop(0)
        
        logging.info(f"Recorded operation: {operation_signature}")

    def _remove_rooms(self, room_names: List[str], description: str) -> str:
        """Remove rooms using structured parameters from LLM instead of regex parsing."""
        if not room_names:
            return "Error: No room names provided for removal."
        
        # Check for duplicate operations
        if self._is_duplicate_operation("remove_room", room_names, description):
            available_rooms = list(self.features["rooms"].keys())
            if available_rooms:
                return f"⚠️ Operation already performed. Room(s) '{', '.join(room_names)}' were already removed. Available rooms: {', '.join(available_rooms)}"
            else:
                return f"⚠️ Operation already performed. Room(s) '{', '.join(room_names)}' were already removed. No rooms remaining."
        
        # Record this operation
        self._record_operation("remove_room", room_names, description)
        
        removed_rooms = []
        for room in room_names:
            found_room = next((key for key in list(self.features["rooms"].keys()) if key.lower() == room.lower()), None)
            if found_room:
                del self.features["rooms"][found_room]
                removed_rooms.append(found_room)
                # Track removed room for potential follow-up queries
                self.last_removed_rooms.append(found_room.lower())
        
        if not removed_rooms:
            available_rooms = ", ".join(self.features["rooms"].keys()) or "No rooms available"
            return f"Error: Room(s) '{', '.join(room_names)}' not found. Available rooms: {available_rooms}"
        
        # Update DXF file
        if hasattr(self, 'ingested_file_path') and self.ingested_file_path:
            try:
                import ezdxf
                doc = ezdxf.readfile(self.ingested_file_path)
                msp = doc.modelspace()
                absolute_path = Path(self.ingested_file_path)
                self._update_room_entities(msp, doc, absolute_path)
            except Exception as e:
                logging.warning(f"Could not update DXF file: {e}")
        
        # Return a comprehensive response with current state
        remaining_rooms = list(self.features["rooms"].keys())
        if remaining_rooms:
            available_rooms_str = ", ".join(remaining_rooms)
            return f"Room(s) {', '.join(removed_rooms)} removed from the blueprint. Available rooms: {available_rooms_str}"
        else:
            return f"Room(s) {', '.join(removed_rooms)} removed from the blueprint. No rooms remaining."

    def _merge_rooms(self, room_names: List[str], description: str) -> str:
        """Merge rooms using structured parameters from LLM instead of regex parsing."""
        if len(room_names) < 2:
            return "Error: At least two room names are required for merging."
        
        # Validate all rooms exist
        existing_rooms = {}
        for room in room_names:
            found_room = next((key for key in list(self.features["rooms"].keys()) if key.lower() == room.lower()), None)
            if not found_room:
                return f"Error: Room '{room}' not found."
            existing_rooms[found_room] = self.features["rooms"][found_room]
        
        # Merge polygons
        merged_polygon = None
        merged_name = "merged_" + "_".join(name.lower() for name in room_names)
        
        for room_name, polygon in existing_rooms.items():
            if merged_polygon is None:
                merged_polygon = polygon
            else:
                merged_polygon = merged_polygon.union(polygon)
            del self.features["rooms"][room_name]
        
        # Handle MultiPolygon result
        if merged_polygon.geom_type == 'MultiPolygon':
            merged_polygon = max(merged_polygon.geoms, key=lambda p: p.area)
        
        self.features["rooms"][merged_name] = merged_polygon
        
        # Update DXF file
        if hasattr(self, 'ingested_file_path') and self.ingested_file_path:
            try:
                import ezdxf
                doc = ezdxf.readfile(self.ingested_file_path)
                msp = doc.modelspace()
                absolute_path = Path(self.ingested_file_path)
                self._update_room_entities(msp, doc, absolute_path)
            except Exception as e:
                logging.warning(f"Could not update DXF file: {e}")
        
        return f"Rooms {', '.join(room_names)} merged into '{merged_name}'."

    def _remove_walls(self, description: str) -> str:
        """Remove all walls using structured parameters from LLM."""
        self.features["walls"].clear()
        
        # Update DXF file
        if hasattr(self, 'ingested_file_path') and self.ingested_file_path:
            try:
                import ezdxf
                doc = ezdxf.readfile(self.ingested_file_path)
                msp = doc.modelspace()
                for entity in list(msp.query("LINE")):
                    msp.delete_entity(entity)
                doc.saveas(str(self.ingested_file_path))
            except Exception as e:
                logging.warning(f"Could not update DXF file: {e}")
        
        return "All walls have been removed from the blueprint."

    def _remove_doors(self, description: str) -> str:
        """Remove all doors using structured parameters from LLM."""
        self.features["doors"].clear()
        
        # Update DXF file
        if hasattr(self, 'ingested_file_path') and self.ingested_file_path:
            try:
                import ezdxf
                doc = ezdxf.readfile(self.ingested_file_path)
                msp = doc.modelspace()
                for entity in list(msp.query("LINE")):
                    if entity.dxf.layer == "A-DOOR":
                        msp.delete_entity(entity)
                doc.saveas(str(self.ingested_file_path))
            except Exception as e:
                logging.warning(f"Could not update DXF file: {e}")
        
        return "All doors have been removed from the blueprint."

    def _remove_windows(self, description: str) -> str:
        """Remove all windows using structured parameters from LLM."""
        self.features["windows"].clear()
        
        # Update DXF file
        if hasattr(self, 'ingested_file_path') and self.ingested_file_path:
            try:
                import ezdxf
                doc = ezdxf.readfile(self.ingested_file_path)
                msp = doc.modelspace()
                for entity in list(msp.query("LINE")):
                    if entity.dxf.layer == "A-GLAZ":
                        msp.delete_entity(entity)
                doc.saveas(str(self.ingested_file_path))
            except Exception as e:
                logging.warning(f"Could not update DXF file: {e}")
        
        return "All windows have been removed from the blueprint."

    def _update_room_entities(self, msp, doc, absolute_path: Path) -> None:
        for poly in list(msp.query("LWPOLYLINE")):
            if poly.closed:
                msp.delete_entity(poly)
        for room_name, polygon in self.features["rooms"].items():
            coords = list(polygon.exterior.coords)
            msp.add_lwpolyline(coords, close=True)
        doc.saveas(str(absolute_path))

    def generate_report(self, query: str = "") -> str:
        """
        Generate a report on the current blueprint using a language model.
        The report can be comprehensive or targeted based on the specific query.
        """
        room_count = len(self.features["rooms"])
        wall_count = len(self.features["walls"])
        door_count = len(self.features["doors"])
        window_count = len(self.features["windows"])
        
        # Debug logging
        logging.info(f"Report generation - Rooms: {room_count}, Walls: {wall_count}, Doors: {door_count}, Windows: {window_count}")
        
        if room_count == 0 and wall_count == 0 and door_count == 0 and window_count == 0:
            return "No rooms, walls, doors, or windows have been extracted. Please run feature extraction first."
        
        file_name = self.original_filename if self.original_filename else (Path(self.ingested_file_path).name if self.ingested_file_path else "Unknown File")
        room_data = []
        total_area = 0.0
        for room_name, poly in self.features["rooms"].items():
            area = poly.area
            total_area += area
            room_data.append(f"- {room_name}: {area:.2f} square units")
        
        # Determine the type of report based on the query
        query_lower = query.lower()
        
        if "room size" in query_lower or "room sizes" in query_lower:
            return self._generate_room_size_report(file_name, room_count, total_area, room_data)
        elif "total floor area" in query_lower or "total area" in query_lower:
            return self._generate_total_area_report(file_name, room_count, total_area, room_data)
        elif "room name" in query_lower or "room names" in query_lower:
            return self._generate_room_names_report(file_name, room_count, room_data)
        elif "wall" in query_lower and ("count" in query_lower or "number" in query_lower):
            return self._generate_wall_count_report(file_name, wall_count, room_count, total_area, room_data)
        elif "efficiency" in query_lower or "layout efficiency" in query_lower:
            # Use comprehensive report for efficiency analysis
            analysis_prompt = self._create_report_prompt(file_name, room_count, wall_count, door_count, window_count, total_area, room_data)
            try:
                llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")
                response = llm.invoke(analysis_prompt)
                return response.content
            except Exception as e:
                logging.error(f"Error generating report: {e}", exc_info=True)
                return self._generate_basic_report(file_name, room_count, wall_count, door_count, window_count, total_area, room_data)
        else:
            # Default comprehensive report
            analysis_prompt = self._create_report_prompt(file_name, room_count, wall_count, door_count, window_count, total_area, room_data)
            try:
                llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo")
                response = llm.invoke(analysis_prompt)
                return response.content
            except Exception as e:
                logging.error(f"Error generating report: {e}", exc_info=True)
                return self._generate_basic_report(file_name, room_count, wall_count, door_count, window_count, total_area, room_data)

    def _create_report_prompt(self, file_name: str, room_count: int, wall_count: int, door_count: int, window_count: int, total_area: float, room_data: List[str]) -> str:
        return f"""
        Analyze this blueprint data and generate a detailed report:

        Total Rooms: {room_count}
        Total Walls: {wall_count}
        Total Doors: {door_count}
        Total Windows: {window_count}
        Total Floor Area: {total_area:.2f} square units

        Room Details:
        {chr(10).join(room_data)}

        Please provide a detailed analysis with the following sections:
        1. Executive Summary: A brief overview of the blueprint layout and key features
        2. Layout Analysis: Detailed description of the room arrangement and flow
        3. Room Size Analysis: Evaluation of room sizes, proportions, and their suitability for intended purposes
        4. Space Utilization: Assessment of how effectively the space is utilized
        5. Design Features: Notable architectural elements and design choices
        6. Improvement Suggestions: Potential modifications to enhance functionality and aesthetics
        7. Conclusion: Overall assessment of the blueprint design

        Format the report in a clear, professional style with distinct sections. Be specific and detailed in your analysis, providing actionable insights based on architectural best practices.

        IMPORTANT: Provide a complete, detailed report with substantive content in each section. Do not return a generic response or refer to previous comments.
        """

    def _generate_room_size_report(self, file_name: str, room_count: int, total_area: float, room_data: List[str]) -> str:
        """Generate a focused report on room sizes."""
        report = [
            "Room Size Report",
            "Blueprint:",
            f"Total Rooms: {room_count}",
            f"Total Floor Area: {total_area:.2f} square units",
            "",
            "Room Sizes:",
            *room_data,
            "",
            "Summary:",
            f"The blueprint contains {room_count} rooms with a total area of {total_area:.2f} square units."
        ]
        return "\n".join(report)

    def _generate_total_area_report(self, file_name: str, room_count: int, total_area: float, room_data: List[str]) -> str:
        """Generate a focused report on total floor area."""
        report = [
            "Total Floor Area Report",
            "Blueprint:",
            "",
            f"Total Floor Area: {total_area:.2f} square units",
            f"Number of Rooms: {room_count}",
            "",
            "Room Breakdown:",
            *room_data,
            "",
            f"The total floor area of {total_area:.2f} square units is distributed across {room_count} rooms."
        ]
        return "\n".join(report)

    def _generate_efficiency_report(self, file_name: str, room_count: int, wall_count: int, door_count: int, window_count: int, total_area: float, room_data: List[str]) -> str:
        """Generate a focused report on layout efficiency."""
        efficiency_analysis = [
            "Layout Efficiency Analysis",
            "Blueprint:",
            "",
            f"Total Floor Area: {total_area:.2f} square units",
            f"Number of Rooms: {room_count}",
            f"Number of Walls: {wall_count}",
            f"Number of Doors: {door_count}",
            f"Number of Windows: {window_count}",
            "",
            "Room Distribution:",
            *room_data,
            "",
            "Efficiency Assessment:",
        ]
        
        # Add efficiency insights
        if wall_count == 0:
            efficiency_analysis.append("- Open-concept layout with no walls")
            efficiency_analysis.append("- Maximizes space utilization but may lack privacy")
        else:
            efficiency_analysis.append(f"- Traditional layout with {wall_count} walls")
            efficiency_analysis.append("- Provides good room separation and privacy")
        
        avg_room_size = total_area / room_count if room_count > 0 else 0
        efficiency_analysis.extend([
            f"- Average room size: {avg_room_size:.2f} square units",
            f"- Space distribution appears {'balanced' if room_count <= 3 else 'complex'}",
            "",
            "Spatial Analysis:",
        ])
        
        # Add spatial analysis information
        try:
            # Perform spatial analysis to get overlap information
            if hasattr(self, 'spatial_analyzer') and self.spatial_analyzer:
                # Add rooms to spatial analyzer for analysis
                for room_name, poly in self.features["rooms"].items():
                    bounds = poly.bounds  # (minx, miny, maxx, maxy)
                    x, y = bounds[0], bounds[1]
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]
                    self.spatial_analyzer.add_room(room_name, x, y, width, height)
                
                # Get spatial analysis results
                spatial_analysis = self.spatial_analyzer.analyze_layout()
                
                if spatial_analysis['is_valid']:
                    efficiency_analysis.append("✅ No room overlaps detected - layout is spatially valid")
                else:
                    room_overlaps = [i for i in spatial_analysis['issues'] if i['type'] == 'room_overlap']
                    if room_overlaps:
                        efficiency_analysis.append(f"⚠️ {len(room_overlaps)} room overlap(s) detected:")
                        for overlap in room_overlaps[:3]:  # Show first 3 overlaps
                            efficiency_analysis.append(f"  • {overlap['room1']} ↔ {overlap['room2']} ({overlap['overlap_percentage']:.1f}% overlap)")
                        if len(room_overlaps) > 3:
                            efficiency_analysis.append(f"  • ... and {len(room_overlaps) - 3} more overlap(s)")
                        
                        # Add severity summary
                        severity = spatial_analysis['severity_summary']
                        efficiency_analysis.append(f"  Severity: {severity['high']} high, {severity['medium']} medium, {severity['low']} low")
            else:
                efficiency_analysis.append("- Spatial analysis not available")
        except Exception as e:
            efficiency_analysis.append(f"- Spatial analysis error: {str(e)}")
        
        efficiency_analysis.extend([
            "",
            "Recommendations:",
            "- Consider room proportions for intended use",
            "- Evaluate traffic flow between rooms",
            "- Assess natural light distribution",
            "- Resolve any detected room overlaps for optimal space utilization"
        ])
        
        return "\n".join(efficiency_analysis)

    def _generate_room_names_report(self, file_name: str, room_count: int, room_data: List[str]) -> str:
        """Generate a focused report on room names."""
        room_names = [room.split(":")[0].strip("- ") for room in room_data]
        report = [
            "Room Names Report",
            "Blueprint:",
            f"Total Rooms: {room_count}",
            "",
            "Room Names:",
            *[f"- {name}" for name in room_names],
            "",
            f"The blueprint contains {room_count} rooms: {', '.join(room_names)}."
        ]
        return "\n".join(report)

    def _generate_wall_count_report(self, file_name: str, wall_count: int, room_count: int, total_area: float, room_data: List[str]) -> str:
        """Generate a focused report on wall count."""
        report = [
            "Wall Count Report",
            "Blueprint:",
            f"Total Walls: {wall_count}",
            f"Total Rooms: {room_count}",
            f"Total Floor Area: {total_area:.2f} square units",
            "",
            "Room Details:",
            *room_data,
            "",
            "Wall Analysis:",
        ]
        
        if wall_count == 0:
            report.extend([
                "- This blueprint has an open-concept layout with no interior walls",
                "- All rooms are connected without physical barriers",
                "- This design maximizes space utilization and creates a sense of openness"
            ])
        else:
            report.extend([
                f"- This blueprint contains {wall_count} walls",
                "- The walls provide room separation and privacy",
                "- This is a traditional partitioned layout design"
            ])
        
        report.extend([
            "",
            "Summary:",
            f"The blueprint contains {wall_count} walls, {room_count} rooms, and covers a total area of {total_area:.2f} square units."
        ])
        
        return "\n".join(report)

    def _generate_basic_report(self, file_name: str, room_count: int, wall_count: int, door_count: int, window_count: int, total_area: float, room_data: List[str]) -> str:
        basic_report = [
            "Blueprint Analysis Report",
            f"Total Rooms: {room_count}",
            f"Total Walls: {wall_count}",
            f"Total Doors: {door_count}",
            f"Total Windows: {window_count}",
            f"Total Floor Area: {total_area:.2f} square units",
            "",
            "Room Details:",
            *room_data,
        ]
        return "\n".join(basic_report)

    def analyze_spatial_layout(self) -> str:
        """
        Analyze the current blueprint for spatial conflicts and overlapping elements.
        Returns a detailed report of any issues found with architectural recommendations.
        """
        if not self.ingested_file_path:
            return "Error: No blueprint file has been loaded. Please upload a blueprint first."
        
        if not self.features["rooms"] and not self.features["walls"]:
            return "Error: No features have been extracted. Please run feature extraction first."
        
        # Clear previous analysis
        self.spatial_analyzer = SpatialAnalyzer()
        
        # Add rooms to spatial analyzer
        for room_name, polygon in self.features["rooms"].items():
            bounds = polygon.bounds  # (minx, miny, maxx, maxy)
            x, y = bounds[0], bounds[1]
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            self.spatial_analyzer.add_room(room_name, x, y, width, height)
        
        # Add walls to spatial analyzer
        for wall in self.features["walls"]:
            if hasattr(wall, 'bounds'):
                bounds = wall.bounds
                start_point = (bounds[0], bounds[1])
                end_point = (bounds[2], bounds[3])
                self.spatial_analyzer.add_wall(start_point, end_point)
        
        # Add doors to spatial analyzer
        for door in self.features["doors"]:
            if hasattr(door, 'bounds'):
                bounds = door.bounds
                start_point = (bounds[0], bounds[1])
                end_point = (bounds[2], bounds[3])
                self.spatial_analyzer.add_door(start_point, end_point)
        
        # Add windows to spatial analyzer
        for window in self.features["windows"]:
            if hasattr(window, 'bounds'):
                bounds = window.bounds
                start_point = (bounds[0], bounds[1])
                end_point = (bounds[2], bounds[3])
                self.spatial_analyzer.add_window(start_point, end_point)
        
        # Generate and return the spatial analysis report with architectural recommendations
        return self.spatial_analyzer.generate_overlap_report()
    
    def get_architectural_recommendations(self) -> str:
        """
        Get detailed architectural and civil engineering recommendations for fixing blueprint issues.
        This method provides professional suggestions for improving the layout.
        """
        if not self.ingested_file_path:
            return "Error: No blueprint file has been loaded. Please upload a blueprint first."
        
        if not self.features["rooms"] and not self.features["walls"]:
            return "Error: No features have been extracted. Please run feature extraction first."
        
        # Perform spatial analysis first
        analysis = self.spatial_analyzer.analyze_layout()
        room_overlaps = [i for i in analysis['issues'] if i['type'] == 'room_overlap']
        
        if not room_overlaps:
            return "✅ No room overlaps detected. The current layout is architecturally sound."
        
        # Generate detailed recommendations
        recommendations = self.spatial_analyzer._generate_architectural_recommendations(room_overlaps)
        
        report_lines = [
            "🏗️ ARCHITECTURAL & CIVIL ENGINEERING ANALYSIS",
            "=" * 50,
            "",
            f"📊 Analysis Summary:",
            f"   • Total room overlaps found: {len(room_overlaps)}",
            f"   • Severity breakdown: {analysis['severity_summary']['high']} high, "
            f"{analysis['severity_summary']['medium']} medium, {analysis['severity_summary']['low']} low",
            "",
            "🔍 Detailed Recommendations:"
        ]
        
        report_lines.extend(recommendations)
        
        # Add professional engineering considerations
        report_lines.extend([
            "",
            "⚙️ ENGINEERING CONSIDERATIONS:",
            "   • Structural Integrity: Ensure load-bearing walls are properly identified",
            "   • HVAC Systems: Consider ductwork and ventilation requirements",
            "   • Electrical Systems: Plan for adequate electrical outlets and lighting",
            "   • Plumbing: Ensure proper drainage and water supply routing",
            "   • Fire Safety: Verify compliance with fire safety codes and egress requirements",
            "",
            "📋 NEXT STEPS:",
            "   1. Review and prioritize recommendations based on project requirements",
            "   2. Consult with structural engineer for load-bearing wall modifications",
            "   3. Coordinate with MEP (Mechanical, Electrical, Plumbing) engineers",
            "   4. Update floor plan and recalculate areas",
            "   5. Submit revised plans for building code review",
            "",
            "💡 TIP: Consider using 3D modeling software to visualize the proposed changes"
        ])
        
        return "\n".join(report_lines)

class SpatialAnalyzer:
    """
    Analyzes spatial relationships and detects overlapping elements in blueprint layouts.
    This class helps prevent invalid layouts by identifying overlaps between rooms, walls, and other elements.
    """
    
    def __init__(self):
        self.rooms = []
        self.walls = []
        self.doors = []
        self.windows = []
    
    def add_room(self, name: str, x: float, y: float, width: float, height: float) -> None:
        """Add a room to the spatial analysis."""
        room_polygon = Polygon([
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height)
        ])
        self.rooms.append({
            'name': name,
            'polygon': room_polygon,
            'bounds': (x, y, width, height)
        })
    
    def add_wall(self, start_point: Tuple[float, float], end_point: Tuple[float, float]) -> None:
        """Add a wall line to the spatial analysis."""
        wall_line = LineString([start_point, end_point])
        self.walls.append({
            'line': wall_line,
            'start': start_point,
            'end': end_point
        })
    
    def add_door(self, start_point: Tuple[float, float], end_point: Tuple[float, float]) -> None:
        """Add a door line to the spatial analysis."""
        door_line = LineString([start_point, end_point])
        self.doors.append({
            'line': door_line,
            'start': start_point,
            'end': end_point
        })
    
    def add_window(self, start_point: Tuple[float, float], end_point: Tuple[float, float]) -> None:
        """Add a window line to the spatial analysis."""
        window_line = LineString([start_point, end_point])
        self.windows.append({
            'line': window_line,
            'start': start_point,
            'end': end_point
        })
    
    def detect_room_overlaps(self) -> List[Dict[str, Any]]:
        """Detect overlapping rooms and return detailed overlap information."""
        overlaps = []
        
        for i, room1 in enumerate(self.rooms):
            for j, room2 in enumerate(self.rooms[i+1:], i+1):
                if room1['polygon'].intersects(room2['polygon']):
                    intersection = room1['polygon'].intersection(room2['polygon'])
                    overlap_area = intersection.area
                    overlap_percentage = (overlap_area / min(room1['polygon'].area, room2['polygon'].area)) * 100
                    
                    # Only flag as overlap if there's actual area overlap (not just shared walls)
                    if overlap_percentage > 0.01:  # Ignore 0.0% overlaps (shared walls)
                        overlaps.append({
                            'type': 'room_overlap',
                            'room1': room1['name'],
                            'room2': room2['name'],
                            'overlap_area': overlap_area,
                            'overlap_percentage': overlap_percentage,
                            'intersection': intersection,
                            'severity': 'high'
                        })
        
        return overlaps
    
    def detect_wall_room_conflicts(self) -> List[Dict[str, Any]]:
        """Detect walls that intersect with room interiors inappropriately."""
        conflicts = []
        
        for wall in self.walls:
            for room in self.rooms:
                # Check if wall intersects with room interior
                if wall['line'].intersects(room['polygon']):
                    intersection = wall['line'].intersection(room['polygon'])
                    
                    # Check if this is a boundary wall (should be allowed) or interior wall (conflict)
                    wall_start = wall['start']
                    wall_end = wall['end']
                    room_bounds = room['polygon'].bounds  # (minx, miny, maxx, maxy)
                    
                    # A wall is a boundary wall if it's very close to the room boundary
                    tolerance = 1.0  # Increased tolerance for boundary detection
                    
                    is_boundary_wall = False
                    
                    # Check if wall is along room boundaries with more generous tolerance
                    # Left boundary
                    if (abs(wall_start[0] - room_bounds[0]) < tolerance and 
                        abs(wall_end[0] - room_bounds[0]) < tolerance):
                        is_boundary_wall = True
                    # Right boundary  
                    elif (abs(wall_start[0] - room_bounds[2]) < tolerance and 
                          abs(wall_end[0] - room_bounds[2]) < tolerance):
                        is_boundary_wall = True
                    # Bottom boundary
                    elif (abs(wall_start[1] - room_bounds[1]) < tolerance and 
                          abs(wall_end[1] - room_bounds[1]) < tolerance):
                        is_boundary_wall = True
                    # Top boundary
                    elif (abs(wall_start[1] - room_bounds[3]) < tolerance and 
                          abs(wall_end[1] - room_bounds[3]) < tolerance):
                        is_boundary_wall = True
                    
                    # Also check if wall is completely within the room (this is normal)
                    wall_centroid = wall['line'].centroid
                    if room['polygon'].contains(wall_centroid):
                        is_boundary_wall = True
                    
                    # Only flag as conflict if it's NOT a boundary wall and has significant intersection
                    # AND the wall is not part of the room's perimeter
                    if not is_boundary_wall and intersection.length > 0.1:
                        # Additional check: if wall is very close to room boundary, it's likely a boundary wall
                        wall_buffer = wall['line'].buffer(0.5)
                        if room['polygon'].boundary.intersects(wall_buffer):
                            is_boundary_wall = True
                        
                        if not is_boundary_wall:
                            conflicts.append({
                                'type': 'wall_room_conflict',
                                'wall': f"Wall from {wall['start']} to {wall['end']}",
                                'room': room['name'],
                                'intersection_length': intersection.length,
                                'severity': 'high' if intersection.length > 1.0 else 'medium'
                            })
        
        return conflicts
    
    def detect_room_proximity_issues(self) -> List[Dict[str, Any]]:
        """Detect rooms that are too close together or have insufficient spacing."""
        issues = []
        
        for i, room1 in enumerate(self.rooms):
            for j, room2 in enumerate(self.rooms[i+1:], i+1):
                # Calculate distance between room boundaries
                distance = room1['polygon'].distance(room2['polygon'])
                
                # If rooms are very close but not overlapping, it might be a design issue
                if distance < 0.5 and distance > 0:  # Less than 0.5 units apart
                    issues.append({
                        'type': 'room_proximity',
                        'room1': room1['name'],
                        'room2': room2['name'],
                        'distance': distance,
                        'severity': 'medium',
                        'description': f"Rooms are very close together ({distance:.2f} units apart)"
                    })
        
        return issues

    def detect_element_overlaps(self) -> List[Dict[str, Any]]:
        """Detect overlaps between different types of elements (walls, doors, windows)."""
        overlaps = []
        
        # Only check for room overlaps as requested - walls and doors are part of rooms and should not be flagged
        # This method now focuses only on room-to-room overlaps which are handled by detect_room_overlaps()
        
        # Note: Wall-wall overlaps and door placement checks have been removed as they are not needed
        # Walls are part of rooms and should not be flagged as conflicts
        # Doors are typically placed in walls and are part of the room structure
        
        return overlaps
    
    def analyze_layout(self) -> Dict[str, Any]:
        """Perform comprehensive spatial analysis of the layout."""
        room_overlaps = self.detect_room_overlaps()
        
        # Updated based on user feedback:
        # - Removed wall conflicts detection as walls are supposed to be part of rooms
        # - Removed element overlaps (wall-wall, door-wall) as these are normal architectural elements
        # - Focus only on room overlaps which are actual spatial problems
        # - Walls and doors are part of room structure and should not be flagged as conflicts
        
        all_issues = room_overlaps
        
        return {
            'total_issues': len(all_issues),
            'room_overlaps': len(room_overlaps),
            'wall_conflicts': 0,  # Removed - walls are supposed to be part of rooms
            'element_overlaps': 0,  # Removed - shared walls and doors in walls are normal
            'proximity_issues': 0,  # Removed - not a critical issue
            'issues': all_issues,
            'is_valid': len(all_issues) == 0,
            'severity_summary': {
                'high': len([i for i in all_issues if i['severity'] == 'high']),
                'medium': len([i for i in all_issues if i['severity'] == 'medium']),
                'low': len([i for i in all_issues if i['severity'] == 'low'])
            }
        }
    
    def generate_overlap_report(self) -> str:
        """Generate a human-readable report of all detected issues."""
        analysis = self.analyze_layout()
        
        if analysis['is_valid']:
            return "✅ Layout Analysis: No room overlaps detected. The layout is valid."
        
        report_lines = ["⚠️ Layout Analysis: Room overlaps detected:"]
        report_lines.append("")
        
        # Only check for room overlaps - walls and doors are normal architectural elements
        room_overlaps = [i for i in analysis['issues'] if i['type'] == 'room_overlap']
        
        if room_overlaps:
            report_lines.append("🚨 ROOM OVERLAPS:")
            for overlap in room_overlaps:
                report_lines.append(f"  • {overlap['room1']} overlaps with {overlap['room2']} "
                                  f"({overlap['overlap_percentage']:.1f}% overlap)")
        
        # Generate architectural recommendations for fixing overlaps
        if room_overlaps:
            recommendations = self._generate_architectural_recommendations(room_overlaps)
            report_lines.append("\n🏗️ ARCHITECTURAL RECOMMENDATIONS:")
            report_lines.extend(recommendations)
        
        report_lines.append(f"\n📊 Summary: {analysis['total_issues']} room overlap issues found "
                           f"({analysis['severity_summary']['high']} high, "
                           f"{analysis['severity_summary']['medium']} medium, "
                           f"{analysis['severity_summary']['low']} low severity)")
        
        return "\n".join(report_lines)
    
    def _generate_architectural_recommendations(self, room_overlaps: List[Dict[str, Any]]) -> List[str]:
        """
        Generate architectural and civil engineering recommendations for fixing room overlaps.
        This method provides professional suggestions based on the type and severity of overlaps.
        """
        recommendations = []
        
        for overlap in room_overlaps:
            room1_name = overlap['room1']
            room2_name = overlap['room2']
            overlap_percentage = overlap['overlap_percentage']
            overlap_area = overlap['overlap_area']
            
            recommendations.append(f"\n  📋 For {room1_name} ↔ {room2_name} ({overlap_percentage:.1f}% overlap):")
            
            # Categorize recommendations based on overlap severity
            if overlap_percentage > 50:
                # Major overlap - significant redesign needed
                recommendations.extend([
                    f"    • **CRITICAL**: This is a major overlap requiring significant redesign",
                    f"    • Consider completely separating these rooms with proper walls",
                    f"    • Evaluate if both rooms are necessary or if one can be eliminated",
                    f"    • Redesign the floor plan to allocate proper space for each room",
                    f"    • Ensure minimum clearances are maintained (typically 3-4 feet between rooms)"
                ])
            elif overlap_percentage > 25:
                # Moderate overlap - room adjustment needed
                recommendations.extend([
                    f"    • **MODERATE**: Adjust room boundaries to eliminate overlap",
                    f"    • Reduce the size of one or both rooms to create separation",
                    f"    • Consider adding a shared wall or partition between rooms",
                    f"    • Ensure each room maintains functional minimum dimensions",
                    f"    • Check if room functions are compatible for adjacent placement"
                ])
            else:
                # Minor overlap - fine-tuning needed
                recommendations.extend([
                    f"    • **MINOR**: Fine-tune room boundaries to resolve overlap",
                    f"    • Adjust room dimensions slightly to eliminate overlap",
                    f"    • Consider if rooms can share a common wall",
                    f"    • Verify that room functions are appropriate for adjacent placement"
                ])
            
            # Add specific recommendations based on room types
            room_type_recommendations = self._get_room_specific_recommendations(room1_name, room2_name)
            if room_type_recommendations:
                recommendations.extend(room_type_recommendations)
            
            # Add general architectural best practices
            recommendations.extend([
                f"    • Ensure proper circulation space around rooms",
                f"    • Maintain building code requirements for room sizes and clearances",
                f"    • Consider natural light and ventilation requirements",
                f"    • Verify structural integrity of proposed changes"
            ])
        
        # Add overall design recommendations
        recommendations.extend([
            f"\n  🎯 OVERALL DESIGN RECOMMENDATIONS:",
            f"    • Review the entire floor plan for optimal space utilization",
            f"    • Consider open-concept layouts where appropriate",
            f"    • Ensure logical flow between rooms and spaces",
            f"    • Verify compliance with local building codes and regulations",
            f"    • Consider future flexibility and adaptability of the space"
        ])
        
        return recommendations
    
    def _get_room_specific_recommendations(self, room1_name: str, room2_name: str) -> List[str]:
        """
        Generate room-specific recommendations based on the types of rooms involved.
        """
        recommendations = []
        
        # Convert room names to lowercase for easier matching
        room1_lower = room1_name.lower()
        room2_lower = room2_name.lower()
        
        # Kitchen-related recommendations
        if 'kitchen' in room1_lower or 'kitchen' in room2_lower:
            recommendations.extend([
                f"    • **Kitchen Considerations**:",
                f"      - Kitchens require proper ventilation and exhaust systems",
                f"      - Ensure adequate space for appliances and work triangles",
                f"      - Consider noise and odor separation from other rooms"
            ])
        
        # Bathroom-related recommendations
        if 'bath' in room1_lower or 'bath' in room2_lower or 'toilet' in room1_lower or 'toilet' in room2_lower:
            recommendations.extend([
                f"    • **Bathroom Considerations**:",
                f"      - Bathrooms require proper plumbing and ventilation",
                f"      - Ensure privacy and sound isolation",
                f"      - Consider accessibility requirements (ADA compliance)"
            ])
        
        # Bedroom-related recommendations
        if 'bed' in room1_lower or 'bed' in room2_lower:
            recommendations.extend([
                f"    • **Bedroom Considerations**:",
                f"      - Bedrooms require privacy and sound isolation",
                f"      - Ensure adequate natural light and ventilation",
                f"      - Consider minimum room size requirements for habitable spaces"
            ])
        
        # Living room/entertainment areas
        if any(term in room1_lower or term in room2_lower for term in ['living', 'family', 'entertainment', 'lounge']):
            recommendations.extend([
                f"    • **Living Space Considerations**:",
                f"      - Living areas should have good natural light and views",
                f"      - Consider traffic flow and furniture placement",
                f"      - Ensure adequate space for intended activities"
            ])
        
        # Office/work areas
        if any(term in room1_lower or term in room2_lower for term in ['office', 'study', 'work', 'desk']):
            recommendations.extend([
                f"    • **Work Space Considerations**:",
                f"      - Work areas need good lighting and minimal distractions",
                f"      - Consider acoustic separation from noisy areas",
                f"      - Ensure adequate electrical outlets and data connections"
            ])
        
        # Storage areas
        if any(term in room1_lower or term in room2_lower for term in ['storage', 'closet', 'pantry', 'wardrobe']):
            recommendations.extend([
                f"    • **Storage Considerations**:",
                f"      - Storage areas can often be reduced or reconfigured",
                f"      - Consider built-in storage solutions to save space",
                f"      - Ensure adequate access and organization"
            ])
        
        return recommendations

class DXFPlotCreator:
    """
    Creates a new DXF blueprint from a natural language prompt using an
    intermediate language model to extract plot dimensions and room details.
    """
    def __init__(self, filename: str, llm: ChatOpenAI) -> None:
        self.filename = filename
        self.llm = llm
        self.doc = ezdxf.new('R2000')
        self.msp = self.doc.modelspace()
        self.entities: List[Dict[str, Any]] = []
        self.width: Optional[float] = None
        self.height: Optional[float] = None
        self.spatial_analyzer = SpatialAnalyzer()
        self.create_layers()

    def create_layers(self) -> None:
        layers_config = {
            "A-DOOR": {"color": 7},
            "A-WALL": {},
            "AREA-ASSIGN": {},
            "A-FLOR": {},
            "Rooms-Information": {},
        }
        for layer_name, attrs in layers_config.items():
            if layer_name not in self.doc.layers:
                self.doc.layers.add(layer_name, **attrs)

    def parse_prompt(self, prompt: str) -> None:
        system_prompt = """Extract plot dimensions and room details from the architectural description.
        Return a JSON object with the following structure:
        {
            "plot": {"width": number, "height": number},
            "rooms": [
                {
                    "name": "room name",
                    "width": number,
                    "height": number,
                    "position": "north|south|east|west"
                }
            ]
        }
        """
        user_prompt = f"Parse this architectural description: {prompt}"
        try:
            response = self.llm.invoke(system_prompt + "\n\nUser: " + user_prompt + "\n\nAssistant: ")
            parsed_data = json.loads(response.content)
            self.width = parsed_data["plot"]["width"]
            self.height = parsed_data["plot"]["height"]
            self.entities = parsed_data["rooms"]
            logging.info(f"Parsed plot dimensions: width={self.width}, height={self.height}")
            logging.info(f"Parsed {len(self.entities)} room(s): {self.entities}")
        except Exception as e:
            logging.error(f"Failed to parse prompt: {e}", exc_info=True)
            raise ValueError(f"Failed to parse prompt: {str(e)}")

    def add_plot_lines(self) -> None:
        if self.width is None or self.height is None:
            raise ValueError("Plot dimensions not set. Call parse_prompt first.")
        points = [(0, 0), (self.width, 0), (self.width, self.height), (0, self.height)]
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]
            self.msp.add_line(start_point, end_point, dxfattribs={'layer': 'A-FLOR'})

    def add_rooms(self) -> None:
        if not self.entities or self.width is None or self.height is None:
            raise ValueError("Room entities or plot dimensions not set. Call parse_prompt first.")
        door_width_default = 2.0
        for entity in self.entities:
            base_x, base_y, door_side = self._calculate_room_position(entity)
            self._add_room_rectangle(entity, base_x, base_y)
            self._add_door(entity, base_x, base_y, door_side, door_width_default)
            self._add_room_text(entity, base_x, base_y)
            
            # Add to spatial analyzer for overlap detection
            self.spatial_analyzer.add_room(entity['name'], base_x, base_y, entity['width'], entity['height'])
            
            # Add room walls to spatial analyzer for door placement detection
            self._add_room_walls_to_analyzer(entity, base_x, base_y)

    def _calculate_room_position(self, entity: Dict[str, Any]) -> Tuple[float, float, str]:
        if entity['position'] == 'north':
            base_x = (self.width - entity['width']) / 2
            base_y = self.height - entity['height']
            door_side = 'south'
        elif entity['position'] == 'south':
            base_x = (self.width - entity['width']) / 2
            base_y = 0
            door_side = 'north'
        elif entity['position'] == 'east':
            base_x = self.width - entity['width']
            base_y = (self.height - entity['height']) / 2
            door_side = 'west'
        elif entity['position'] == 'west':
            base_x = 0
            base_y = (self.height - entity['height']) / 2
            door_side = 'east'
        else:
            base_x, base_y, door_side = 0, 0, 'south'
        return base_x, base_y, door_side

    def _add_room_rectangle(self, entity: Dict[str, Any], base_x: float, base_y: float) -> None:
        points = [
            (base_x, base_y),
            (base_x + entity['width'], base_y),
            (base_x + entity['width'], base_y + entity['height']),
            (base_x, base_y + entity['height']),
        ]
        self.msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'AREA-ASSIGN'})

    def _add_door(self, entity: Dict[str, Any], base_x: float, base_y: float, door_side: str, door_width_default: float) -> None:
        door_width = min(door_width_default, entity['width'] * 0.5, entity['height'] * 0.5)
        if door_side == 'south':
            d_start = (base_x + (entity['width'] - door_width) / 2, base_y)
            d_end = (base_x + (entity['width'] + door_width) / 2, base_y)
        elif door_side == 'north':
            d_start = (base_x + (entity['width'] - door_width) / 2, base_y + entity['height'])
            d_end = (base_x + (entity['width'] + door_width) / 2, base_y + entity['height'])
        elif door_side == 'west':
            d_start = (base_x, base_y + (entity['height'] - door_width) / 2)
            d_end = (base_x, base_y + (entity['height'] + door_width) / 2)
        elif door_side == 'east':
            d_start = (base_x + entity['width'], base_y + (entity['height'] - door_width) / 2)
            d_end = (base_x + entity['width'], base_y + (entity['height'] + door_width) / 2)
        else:
            d_start = d_end = (0, 0)
        self.msp.add_line(d_start, d_end, dxfattribs={'layer': 'A-DOOR', 'color': 1})
        
        # Add to spatial analyzer for overlap detection
        self.spatial_analyzer.add_door(d_start, d_end)

    def _add_room_walls_to_analyzer(self, entity: Dict[str, Any], base_x: float, base_y: float) -> None:
        """Add room walls to the spatial analyzer for door placement detection."""
        # Add the four walls of the room, avoiding duplicates
        walls_to_add = [
            # Bottom wall
            ((base_x, base_y), (base_x + entity['width'], base_y)),
            # Top wall
            ((base_x, base_y + entity['height']), (base_x + entity['width'], base_y + entity['height'])),
            # Left wall
            ((base_x, base_y), (base_x, base_y + entity['height'])),
            # Right wall
            ((base_x + entity['width'], base_y), (base_x + entity['width'], base_y + entity['height']))
        ]
        
        for wall_start, wall_end in walls_to_add:
            # Check if this wall already exists (to avoid duplicates)
            wall_exists = False
            for existing_wall in self.spatial_analyzer.walls:
                if (abs(existing_wall['start'][0] - wall_start[0]) < 0.001 and 
                    abs(existing_wall['start'][1] - wall_start[1]) < 0.001 and
                    abs(existing_wall['end'][0] - wall_end[0]) < 0.001 and 
                    abs(existing_wall['end'][1] - wall_end[1]) < 0.001):
                    wall_exists = True
                    break
            
            if not wall_exists:
                self.spatial_analyzer.add_wall(wall_start, wall_end)

    def _add_room_text(self, entity: Dict[str, Any], base_x: float, base_y: float) -> None:
        text_position = (base_x + entity['width'] / 2, base_y + entity['height'] / 2)
        mtext = self.msp.add_mtext(entity['name'], dxfattribs={'layer': 'Rooms-Information'})
        mtext.set_location(text_position, attachment_point=5)

    def analyze_spatial_layout(self) -> str:
        """Analyze the spatial layout for overlapping elements and return a report with architectural recommendations."""
        return self.spatial_analyzer.generate_overlap_report()
    
    def get_spatial_analysis(self) -> Dict[str, Any]:
        """Get detailed spatial analysis results."""
        return self.spatial_analyzer.analyze_layout()

    def create_dxf(self, prompt: str) -> str:
        try:
            self.parse_prompt(prompt)
            self.add_plot_lines()
            self.add_rooms()
            
            # Perform spatial analysis
            spatial_report = self.analyze_spatial_layout()
            
            self.doc.saveas(self.filename)
            
            # Return both the filename and spatial analysis
            return f"DXF plot created successfully: {self.filename}\n\n{spatial_report}"
        except Exception as e:
            logging.error(f"Error creating DXF: {e}", exc_info=True)
            raise ValueError(f"Failed to create DXF: {str(e)}")

def create_dxf_plot(user_prompt: str) -> str:
    """
    Create a DXF plot from a natural language prompt using a language model.
    Returns a status message indicating the location of the created file or an
    error description.
    """
    filename = "generated_plot_blueprint.dxf"
    try:
        llm = ChatOpenAI(temperature=0.0, model_name="gpt-3.5-turbo")
        plot_creator = DXFPlotCreator(filename, llm)
        created_file = plot_creator.create_dxf(user_prompt)
        return f"DXF plot created successfully: {created_file}"
    except Exception as e:
        logging.error(f"Error creating DXF plot: {e}", exc_info=True)
        return f"Error creating DXF plot: {e}"