#!/usr/bin/env python3
"""
Simple test runner for the Blueprint Parser Creator Demo.

This script runs basic tests without requiring pytest installation.
Run with: python run_tests.py
"""

import sys
import os
from pathlib import Path

def run_basic_tests():
    """Run basic functionality tests."""
    print("🧪 Running Blueprint Parser Creator Demo Tests...")
    print("=" * 50)
    
    # Test 1: Import tests
    print("1. Testing imports...")
    try:
        import blueprint_actions
        import blueprint_utils
        import main
        print("   ✅ All modules imported successfully")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Action creation tests
    print("2. Testing action creation...")
    try:
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
        
        # Create mock analyzer for testing
        from unittest.mock import Mock
        mock_analyzer = Mock(spec=BlueprintAnalyzer)
        
        # Test action creation
        actions = [
            HandleFileInputAction(analyzer=mock_analyzer),
            ExtractFeaturesAction(analyzer=mock_analyzer),
            GetRoomAreaAction(analyzer=mock_analyzer),
            ModifyBlueprintAction(analyzer=mock_analyzer),
            GenerateReportAction(analyzer=mock_analyzer),
            SpatialAnalysisAction(analyzer=mock_analyzer),
            CreateDXFPlotAction(),
        ]
        
        print(f"   ✅ Created {len(actions)} actions successfully")
        
        # Verify action names
        expected_names = [
            "HandleFileInput", "ExtractFeatures", "GetRoomArea",
            "ModifyBlueprint", "GenerateReport", "SpatialAnalysis", "CreateDXFPlot"
        ]
        for action, expected_name in zip(actions, expected_names):
            assert action.name == expected_name, f"Action name mismatch: {action.name} != {expected_name}"
        
        print("   ✅ All action names verified")
        
    except Exception as e:
        print(f"   ❌ Action creation failed: {e}")
        return False
    
    # Test 3: Analyzer initialization
    print("3. Testing analyzer initialization...")
    try:
        analyzer = BlueprintAnalyzer()
        assert analyzer.ingested_file_path is None
        assert isinstance(analyzer.features, dict)
        assert "rooms" in analyzer.features
        assert "walls" in analyzer.features
        print("   ✅ Analyzer initialized successfully")
    except Exception as e:
        print(f"   ❌ Analyzer initialization failed: {e}")
        return False
    
    # Test 4: Environment variables
    print("4. Testing environment configuration...")
    try:
        env_sample_path = Path(__file__).parent / ".env-sample"
        assert env_sample_path.exists(), ".env-sample file should exist"
        
        with open(env_sample_path, 'r') as f:
            content = f.read()
            required_vars = ['OPENAI_API_KEY', 'CLOUDCONVERT_API_KEY']
            for var in required_vars:
                assert var in content, f"Missing environment variable: {var}"
        
        print("   ✅ Environment configuration verified")
    except Exception as e:
        print(f"   ❌ Environment configuration failed: {e}")
        return False
    
    # Test 5: File structure
    print("5. Testing file structure...")
    try:
        required_files = [
            'main.py', 'blueprint_actions.py', 'blueprint_utils.py',
            'blueprint_agent_config.yml', 'requirements.txt', 'README.md'
        ]
        
        for file_name in required_files:
            file_path = Path(__file__).parent / file_name
            assert file_path.exists(), f"Required file missing: {file_name}"
        
        print("   ✅ All required files present")
    except Exception as e:
        print(f"   ❌ File structure check failed: {e}")
        return False
    
    print("=" * 50)
    print("🎉 All tests passed! The demo is ready to use.")
    return True


def main():
    """Main test runner."""
    success = run_basic_tests()
    
    if success:
        print("\n📋 Next steps:")
        print("1. Copy .env-sample to .env and add your API keys")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the demo: streamlit run main.py")
        print("4. For comprehensive tests: python -m pytest test_blueprint_demo.py -v")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
