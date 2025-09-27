"""
Sherpa action definitions for the blueprint analysis project.

Each class in this module subclasses ``BaseAction`` from the sherpa_ai library
and wraps a corresponding method or function from the core blueprint logic
implemented in ``blueprint_utils``.  These actions encapsulate specific
operations (file ingestion, feature extraction, room area computation,
modifications, report generation, spatial analysis and DXF plotting) so that a Sherpa agent
can invoke them during its reasoning process.

The actions are typed using Pydantic and expose a ``name``, ``args`` and
``usage`` attribute to describe their capabilities.  The ``execute`` method
contains the runtime logic and delegates to an underlying ``BlueprintAnalyzer``
instance or to a standalone utility function.
"""

from pydantic import ConfigDict
from sherpa_ai.actions.base import BaseAction
from blueprint_utils import BlueprintAnalyzer, create_dxf_plot
from typing import List
import logging


class HandleFileInputAction(BaseAction):
    """
    Action that handles blueprint file ingestion.  It accepts a file path
    (as a string) and converts the file to DXF if necessary.  The wrapped
    ``BlueprintAnalyzer`` instance maintains the path of the ingested file.
    """
    # Allow arbitrary types (BlueprintAnalyzer) on the model
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # External state: the analyzer that will ingest files and track state
    analyzer: BlueprintAnalyzer

    # The name exposed to the agent
    name: str = "HandleFileInput"

    # Arguments accepted by this action: a single file_path string
    args: dict = {"file_path": "string"}

    # A human readable description of this action
    usage: str = (
        "Process blueprint files (DXF, DWG, etc.). Provide a file path string in quotes. "
        "Returns a status message indicating whether the file was ingested or converted."
    )

    def execute(self, file_path: str) -> str:
        # Wrap the input in single quotes to satisfy the underlying implementation
        return self.analyzer.handle_file_input(f"'{file_path}'")


class ExtractFeaturesAction(BaseAction):
    """
    Action that extracts rooms, walls and other features from an ingested
    blueprint.  It must be called after ``HandleFileInputAction`` and will
    populate the ``features`` attribute on the shared ``BlueprintAnalyzer``.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    analyzer: BlueprintAnalyzer
    name: str = "ExtractFeatures"
    args: dict = {}
    usage: str = (
        "ONLY use this action once after file ingestion to extract rooms, walls, and other features. "
        "Do NOT use this action for queries about room areas, modifications, or reports. "
        "No input arguments are required. Returns a summary of the extracted features."
    )
    def execute(self) -> str:
        return self.analyzer.extract_features()


class GetRoomAreaAction(BaseAction):
    """
    Action that computes the area of a specific room.  The room name should
    match one of the rooms extracted by ``ExtractFeaturesAction``.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    analyzer: BlueprintAnalyzer
    name: str = "GetRoomArea"
    args: dict = {"room_name": "string"}
    usage: str = (
        "Use this action when the user asks about a specific room's area, size, or dimensions (e.g., 'kitchen area', 'bedroom size'). "
        "Provide the room name as a string. Returns the area in square units or a message if the room is not found."
    )
    def execute(self, room_name: str) -> str:
        # Log when GetRoomArea is called to help debug LLM decisions
        logging.info(f"GetRoomArea called with room_name: '{room_name}'")
        
        # Check if this room was just removed (by checking if it's not in the current rooms)
        available_rooms = list(self.analyzer.features.get("rooms", {}).keys())
        if room_name.lower() not in [room.lower() for room in available_rooms]:
            # Check if this room was recently removed
            if room_name.lower() in self.analyzer.last_removed_rooms:
                if available_rooms:
                    return f"Room '{room_name}' was successfully removed. Available rooms: {', '.join(available_rooms)}"
                else:
                    return f"Room '{room_name}' was successfully removed. No rooms remaining."
            else:
                # Room doesn't exist - provide helpful message without error
                if available_rooms:
                    return f"Room '{room_name}' has been removed or does not exist. Available rooms: {', '.join(available_rooms)}"
                else:
                    return f"Room '{room_name}' has been removed or does not exist. No rooms remaining."
        
        return self.analyzer.get_room_area(room_name)


class ModifyBlueprintAction(BaseAction):
    """
    Action that modifies the ingested blueprint. The LLM should parse the user's request
    and provide structured parameters for the modification.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    analyzer: BlueprintAnalyzer
    name: str = "ModifyBlueprint"
    args: dict = {
        "action_type": "string",  # "remove_room", "merge_rooms", "remove_walls", "remove_doors", "remove_windows"
        "room_names": "list",     # List of room names to modify (e.g., ["kitchen"] or ["bedroom", "bathroom"])
        "description": "string"   # Original user request for context and logging
    }
    usage: str = (
        "Use this action when the user wants to modify the blueprint layout. "
        "The LLM should parse the user's request and provide:\n"
        "- action_type: 'remove_room', 'merge_rooms', 'remove_walls', 'remove_doors', 'remove_windows'\n"
        "- room_names: list of room names involved in the operation\n"
        "- description: original user request for context\n\n"
        "Examples:\n"
        "- User: 'remove kitchen' → action_type: 'remove_room', room_names: ['kitchen']\n"
        "- User: 'merge bedroom and bathroom' → action_type: 'merge_rooms', room_names: ['bedroom', 'bathroom']\n"
        "- User: 'remove all walls' → action_type: 'remove_walls', room_names: []\n"
        "Returns a status message with the result of the modification."
    )
    def execute(self, action_type: str, room_names: List[str], description: str) -> str:
        # Log the parameters received from LLM
        logging.info(f"ModifyBlueprint called with: action_type='{action_type}', room_names={room_names}, description='{description}'")
        
        # Validate action type
        valid_actions = ["remove_room", "merge_rooms", "remove_walls", "remove_doors", "remove_windows"]
        if action_type not in valid_actions:
            logging.error(f"Invalid action_type '{action_type}' received from LLM")
            return f"Error: Invalid action_type '{action_type}'. Valid types: {', '.join(valid_actions)}"
        
        # Call the appropriate method based on action type
        try:
            if action_type == "remove_room":
                result = self.analyzer._remove_rooms(room_names, description)
            elif action_type == "merge_rooms":
                result = self.analyzer._merge_rooms(room_names, description)
            elif action_type == "remove_walls":
                result = self.analyzer._remove_walls(description)
            elif action_type == "remove_doors":
                result = self.analyzer._remove_doors(description)
            elif action_type == "remove_windows":
                result = self.analyzer._remove_windows(description)
            else:
                result = f"Error: Unhandled action type '{action_type}'"
            
            # Log the result for debugging
            logging.info(f"ModifyBlueprint {action_type} completed with result: {result}")
            
            # Check if the operation was successful and provide clear feedback
            if "Error" in result:
                logging.warning(f"ModifyBlueprint {action_type} returned error: {result}")
                return result
            else:
                # Operation succeeded - return the success message
                logging.info(f"ModifyBlueprint {action_type} completed successfully")
                return result
            
        except Exception as e:
            logging.error(f"Error executing ModifyBlueprint {action_type}: {e}")
            return f"Error executing {action_type}: {str(e)}"


class GenerateReportAction(BaseAction):
    """
    Action that generates a comprehensive report describing the blueprint. The
    report includes an executive summary, layout analysis and suggestions for
    improvement based on architectural best practices.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    analyzer: BlueprintAnalyzer
    name: str = "GenerateReport"
    args: dict = {"query": "string"}
    usage: str = (
        "Use this action for ANY general questions about the blueprint, including: "
        "- 'number of rooms', 'room count', 'how many rooms' "
        "- 'total area', 'total floor area', 'overall size' "
        "- 'room names', 'list of rooms', 'what rooms are there' "
        "- 'efficiency', 'layout analysis', 'design evaluation' "
        "- 'overview', 'summary', 'report', 'analysis' "
        "- ANY question that doesn't ask about a specific room's area "
        "Provide the user's query as input to generate a targeted report. "
        "This is the DEFAULT action for most blueprint questions."
    )
    def execute(self, query: str = "") -> str:
        return self.analyzer.generate_report(query)


class CreateDXFPlotAction(BaseAction):
    """
    Action that creates a brand new DXF blueprint from a natural language prompt.  The
    prompt should describe the plot dimensions and the rooms, including their
    sizes and positions.  The resulting DXF is saved to disk and the path is
    returned in the status message.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # This action does not depend on the analyzer; it calls a standalone utility
    name: str = "CreateDXFPlot"
    args: dict = {"prompt": "string"}
    usage: str = (
        "Create a new DXF blueprint from a natural language description. "
        "Example: 'Create a 50x50 plot with living room 20x15 at north'. "
        "Returns a status message with the path to the created DXF file."
    )
    def execute(self, prompt: str) -> str:
        return create_dxf_plot(prompt)


class SpatialAnalysisAction(BaseAction):
    """
    Action that performs spatial analysis on blueprints to detect overlapping elements,
    spatial conflicts, and provide suggestions for fixing layout issues.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    analyzer: BlueprintAnalyzer
    name: str = "SpatialAnalysis"
    args: dict = {}
    usage: str = (
        "Use this action when the user wants to analyze a blueprint for overlapping elements, "
        "spatial conflicts, or layout validation. This action will detect room overlaps, "
        "wall conflicts, door placement issues, and other spatial problems. "
        "No input arguments are required. Returns a detailed report of any detected issues "
        "with suggestions for fixing them."
    )
    def execute(self) -> str:
        if not self.analyzer.ingested_file_path:
            return "Error: No blueprint file has been loaded. Please upload a blueprint first."
        
        try:
            return self.analyzer.analyze_spatial_layout()
        except Exception as e:
            return f"Error performing spatial analysis: {str(e)}"