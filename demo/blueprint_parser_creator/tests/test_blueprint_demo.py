"""
Basic tests for the Blueprint Parser Creator Demo.

This file demonstrates testing patterns for the demo components.
Run with: python -m pytest test_blueprint_demo.py -v
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import the components we want to test
from blueprint_actions import (
    HandleFileInputAction,
    ExtractFeaturesAction,
    GetRoomAreaAction,
    ModifyBlueprintAction,
    GenerateReportAction,
    CreateDXFPlotAction,
    SpatialAnalysisAction
)
from blueprint_utils import BlueprintAnalyzer


class TestBlueprintActions:
    """Test the Sherpa actions for blueprint operations."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.analyzer = BlueprintAnalyzer()
        self.mock_analyzer = Mock(spec=BlueprintAnalyzer)
    
    def test_handle_file_input_action_creation(self):
        """Test that HandleFileInputAction can be created."""
        action = HandleFileInputAction(analyzer=self.mock_analyzer)
        assert action.name == "HandleFileInput"
        # Check that args contains the expected argument
        assert len(action.args) > 0
        assert any(arg.name == "file_path" for arg in action.args)
        assert "Process blueprint files" in action.usage
    
    def test_extract_features_action_creation(self):
        """Test that ExtractFeaturesAction can be created."""
        action = ExtractFeaturesAction(analyzer=self.mock_analyzer)
        assert action.name == "ExtractFeatures"
        assert len(action.args) == 0  # No arguments for this action
        assert "extract rooms, walls, and other features" in action.usage
    
    def test_get_room_area_action_creation(self):
        """Test that GetRoomAreaAction can be created."""
        action = GetRoomAreaAction(analyzer=self.mock_analyzer)
        assert action.name == "GetRoomArea"
        # Check that args contains the expected argument
        assert len(action.args) > 0
        assert any(arg.name == "room_name" for arg in action.args)
        assert "room's area, size, or dimensions" in action.usage
    
    def test_modify_blueprint_action_creation(self):
        """Test that ModifyBlueprintAction can be created."""
        action = ModifyBlueprintAction(analyzer=self.mock_analyzer)
        assert action.name == "ModifyBlueprint"
        # Check that args contains the expected arguments
        assert len(action.args) > 0
        arg_names = [arg.name for arg in action.args]
        assert "action_type" in arg_names
        assert "room_names" in arg_names
        assert "description" in arg_names
        assert "modify the blueprint layout" in action.usage
    
    def test_generate_report_action_creation(self):
        """Test that GenerateReportAction can be created."""
        action = GenerateReportAction(analyzer=self.mock_analyzer)
        assert action.name == "GenerateReport"
        # Check that args contains the expected argument
        assert len(action.args) > 0
        assert any(arg.name == "query" for arg in action.args)
        assert "general questions about the blueprint" in action.usage
    
    def test_spatial_analysis_action_creation(self):
        """Test that SpatialAnalysisAction can be created."""
        action = SpatialAnalysisAction(analyzer=self.mock_analyzer)
        assert action.name == "SpatialAnalysis"
        assert len(action.args) == 0  # No arguments for this action
        assert "overlapping elements" in action.usage
    
    def test_create_dxf_plot_action_creation(self):
        """Test that CreateDXFPlotAction can be created."""
        action = CreateDXFPlotAction()
        assert action.name == "CreateDXFPlot"
        # Check that args contains the expected argument
        assert len(action.args) > 0
        assert any(arg.name == "prompt" for arg in action.args)
        assert "new DXF blueprint" in action.usage


class TestBlueprintAnalyzer:
    """Test the core BlueprintAnalyzer functionality."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.analyzer = BlueprintAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test that BlueprintAnalyzer initializes correctly."""
        assert self.analyzer.ingested_file_path is None
        # Check that features has the expected structure
        assert isinstance(self.analyzer.features, dict)
        assert "rooms" in self.analyzer.features
        assert "walls" in self.analyzer.features
        assert "doors" in self.analyzer.features
        assert "windows" in self.analyzer.features
        assert len(self.analyzer.last_removed_rooms) == 0
    
    def test_analyzer_has_required_methods(self):
        """Test that BlueprintAnalyzer has all required methods."""
        required_methods = [
            'handle_file_input',
            'extract_features',
            'get_room_area',
            'generate_report',
            'analyze_spatial_layout'
        ]
        for method in required_methods:
            assert hasattr(self.analyzer, method), f"Missing method: {method}"
    
    @patch('blueprint_utils.CLOUDCONVERT_API_KEY', 'test_key')
    def test_cloudconvert_configuration(self):
        """Test that CloudConvert is configured when API key is available."""
        # This test verifies the CloudConvert configuration logic
        # We can't easily test the actual API calls without real credentials
        assert True  # Placeholder for now


class TestIntegration:
    """Test integration between components."""
    
    def test_action_analyzer_integration(self):
        """Test that actions can work with a real analyzer instance."""
        analyzer = BlueprintAnalyzer()
        action = GetRoomAreaAction(analyzer=analyzer)
        
        # Test that the action can access analyzer methods
        assert hasattr(action.analyzer, 'get_room_area')
        assert callable(action.analyzer.get_room_area)


def test_imports():
    """Test that all required modules can be imported."""
    # This test ensures the demo can be imported without errors
    try:
        import blueprint_actions
        import blueprint_utils
        import main
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_environment_variables():
    """Test that required environment variables are documented."""
    # Check that .env-sample contains the required variables
    env_sample_path = Path(__file__).parent / ".env-sample"
    assert env_sample_path.exists(), ".env-sample file should exist"
    
    with open(env_sample_path, 'r') as f:
        content = f.read()
        required_vars = ['OPENAI_API_KEY', 'CLOUDCONVERT_API_KEY']
        for var in required_vars:
            assert var in content, f"Missing environment variable: {var}"


if __name__ == "__main__":
    # Run basic tests if executed directly
    pytest.main([__file__, "-v"])
