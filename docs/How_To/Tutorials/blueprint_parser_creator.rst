Create a Blueprint Parser Creator with Sherpa
============================================

In this tutorial we will create a comprehensive blueprint analysis and modification tool using Sherpa. The blueprint parser creator will be able to upload blueprint files (DXF, DWG, PDF, etc.), extract architectural features, analyze layouts, and modify blueprints using natural language commands through an intelligent Sherpa agent.

Overview
--------

The blueprint parser creator demonstrates Sherpa's advanced capabilities for multi-action orchestration and intelligent decision-making. The main components are:

1. ``main.py``: Streamlit web application that integrates Sherpa agent with user interface
2. ``blueprint_actions.py``: Sherpa action definitions wrapping core blueprint logic
3. ``blueprint_utils.py``: Core business logic for blueprint processing, DXF handling, and geometric calculations
4. ``blueprint_agent_config.yml``: YAML configuration for Sherpa agent with detailed action selection rules

The demo showcases seven Sherpa actions working together for blueprint operations including file handling, feature extraction, room analysis, modifications, reporting, spatial analysis, and DXF creation.

Install Dependencies
-------------------

Step 1. Install Python 3.9+ and create a project folder:

.. code-block:: bash

   cd <your development directory>
   mkdir sherpa_blueprint_parser
   cd sherpa_blueprint_parser

Step 2. Install Sherpa and dependencies:

.. code-block:: bash

   poetry install
   pip install -r requirements.txt

Step 3. Download files from the `demo/blueprint_parser_creator <https://github.com/Aggregate-Intellect/sherpa/tree/main/demo/blueprint_parser_creator>`_ directory.

Step 4. Set up environment variables:

.. code-block:: bash

   cp .env-sample .env
   # Add your OpenAI and CloudConvert API keys to .env

How to Use
----------

Step 1. Start the Streamlit application:

.. code-block:: bash

   streamlit run main.py

The application will open in your browser at ``http://localhost:8501``.

Step 2. Choose your operation:
   - **Upload & Analyze Blueprint**: Upload existing blueprints and ask questions or request modifications
   - **Create New Blueprint**: Describe a brand new layout to generate a DXF file

Step 3. For existing blueprints:
   - Upload your blueprint file (supports DXF, DWG, PDF, and many other formats)
   - The system will automatically convert and extract features from your blueprint
   - Ask questions like "What is the area of the kitchen?" or "Remove the bedroom"

Step 4. For new blueprints:
   - Describe your desired layout in natural language
   - Example: "Create a 50x30 plot with living room (20x15) in the north, kitchen (15x12) in the east"
   - Download the generated DXF file

Testing and Features
--------------------

Test the demo before running:

.. code-block:: bash

   # Quick test
   python tests/run_tests.py
   
   # Comprehensive testing
    python -m pytest tests/test_blueprint_demo.py::TestBlueprintActions -v
    python -m pytest tests/test_blueprint_demo.py::TestBlueprintAnalyzer -v

Key Features Demonstrated
-------------------------

1. **Multi-Action Orchestration**: Sherpa coordinates multiple specialized actions to solve complex problems
2. **Intelligent Decision Making**: LLM-powered action selection using Sherpa's ReactPolicy
3. **State Management**: Shared BlueprintAnalyzer instance maintains context across actions
4. **Natural Language Interface**: Users can ask complex questions like "merge the living room and dining room"
5. **Professional Architecture**: Clean separation between Sherpa actions and core business logic
6. **Comprehensive Testing**: Full test suite demonstrating testing patterns for Sherpa applications

Example Queries
---------------

- "What is the area of the kitchen?" → Uses GetRoomArea action
- "Analyze the layout efficiency" → Uses GenerateReport action
- "Remove the bedroom" → Uses ModifyBlueprint action
- "Check for overlapping elements" → Uses SpatialAnalysis action
- "Create a 50x30 plot with living room (20x15) in the north" → Uses CreateDXFPlot action

Technical Details
-----------------

The demo demonstrates key Sherpa patterns including action design, configuration-driven setup, shared state management, error handling, and comprehensive testing.

**Supported Formats**: Input (AI, CDR, CGM, DWG, EMF, EPS, PDF, PS, SK, SVG, VSD, WMF) auto-converted to DXF. Output: DXF format.

Troubleshooting
---------------

Common issues include "Features already extracted" (normal), "Room not found" (check sidebar names), file conversion errors (verify API keys), and import errors (check dependencies). Check console logs for detailed error messages.

Revisions and Added Features
----------------------------

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Date
    - Description
  * - 03-Sep-2024
    - Initial release with comprehensive blueprint analysis and modification capabilities
