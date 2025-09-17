"""
Streamlit application that integrates a Sherpa agent for blueprint analysis.

This application uses the Sherpa agent defined in ``blueprint_agent_config.yml``
to ingest DXF files, extract features, compute room areas, modify blueprints,
generate reports, perform spatial analysis, and even create new blueprints from natural language
descriptions.  The core blueprint logic is implemented in reusable
components in ``blueprint_utils.py``, and the Sherpa actions wrapping those
functions live in ``blueprint_actions.py``.  Here we wire everything
together inside a Streamlit app.

Users can upload existing blueprints and ask questions or request modifications, or
describe a brand new layout to generate a DXF file.  Under the hood, a
Sherpa QAAgent orchestrates calls to the available actions.  Each call
returns a message string which the UI displays back to the user.

Note: Running this application requires the ``sherpa_ai`` package to be
installed in your environment along with the dependencies used in
``blueprint_utils`` (e.g., ``cloudconvert``, ``ezdxf``, etc.).  The
CloudConvert API key must be set via environment variable.  The OpenAI
API key should also be set for the language models to function.
"""

from __future__ import annotations

import logging
import os
# import re  # No longer needed - removed regex-based methods
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from pydantic import ConfigDict

# Core blueprint logic and Sherpa action definitions
from blueprint_utils import BlueprintAnalyzer
from blueprint_actions import (
    HandleFileInputAction,
    ExtractFeaturesAction,
    GetRoomAreaAction,
    ModifyBlueprintAction,
    GenerateReportAction,
    CreateDXFPlotAction,
    SpatialAnalysisAction
)

# Sherpa imports – these come from the sherpa_ai library
from sherpa_ai.memory.shared_memory import SharedMemory
from sherpa_ai.config.task_config import AgentConfig
from sherpa_ai.agents.qa_agent import QAAgent

# LangChain's ChatOpenAI model as the LLM for the Sherpa agent.
from langchain_community.chat_models import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables (OpenAI and CloudConvert keys)
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLOUDCONVERT_API_KEY = os.getenv("CLOUDCONVERT_API_KEY")
if not CLOUDCONVERT_API_KEY:
    raise ValueError("CLOUDCONVERT_API_KEY is not set.")


def create_sherpa_agent(analyzer: Optional[BlueprintAnalyzer] = None) -> Tuple[QAAgent, BlueprintAnalyzer]:
    """Instantiate a Sherpa QAAgent along with the shared BlueprintAnalyzer.

    This helper mirrors the YAML configuration defined in
    ``blueprint_agent_config.yml`` but constructs the objects in Python.

    Args:
        analyzer: Optional existing ``BlueprintAnalyzer`` to share state.

    Returns:
        Tuple of (agent, analyzer)
    """
    if analyzer is None:
        analyzer = BlueprintAnalyzer()

    # Create the underlying LLM.  We use the OpenAI chat model with a
    # deterministic temperature to ensure reproducible responses when planning
    # which actions to call.  The API key should be set in the environment.
    llm = ChatOpenAI(
        temperature=0.0,
        model_name="gpt-3.5-turbo",
    )

    # Shared memory stores the task objective and shared information between
    # multiple agents.  In this single‑agent scenario it still records the
    # objective for clarity.
    shared_memory = SharedMemory(objective="Analyse and modify building blueprints")

    # Agent configuration controls high‑level behaviour such as verbosity and
    # whether to use a task agent.  We stick with defaults.
    agent_config = AgentConfig()

    # Instantiate each action with the shared analyzer where appropriate.
    actions = [
            HandleFileInputAction(analyzer=analyzer),
            ExtractFeaturesAction(analyzer=analyzer),
            GetRoomAreaAction(analyzer=analyzer),
            ModifyBlueprintAction(analyzer=analyzer),
            GenerateReportAction(analyzer=analyzer),
            SpatialAnalysisAction(analyzer=analyzer),
            CreateDXFPlotAction(),
        ]

    # Compose the QA agent.  The description explains its capabilities in
    # natural language so that the planning logic knows how to use each action.
    agent = QAAgent(
        llm=llm,
        shared_memory=shared_memory,
        name="Blueprint Sherpa",
        description=(
            "You are a blueprint analysis and modification assistant. You have access to these actions:\n"
            "- GetRoomArea: Use when user asks about room area/size (e.g., 'kitchen area', 'bedroom size')\n"
            "- ModifyBlueprint: Use when user wants to modify layout (remove rooms, merge rooms, remove walls/doors/windows)\n"
            "- GenerateReport: Use when user asks for analysis, reports, or general blueprint information\n"
            "- SpatialAnalysis: Use when user asks about overlapping elements or layout validation\n"
            "- CreateDXFPlot: Use when user wants to create a new blueprint from description\n"
            "- ExtractFeatures: Use once after file ingestion to extract rooms and walls\n"
            "- HandleFileInput: Use when processing a new file\n"
            "\nSimple rules:\n"
            "- For room removal: Use ModifyBlueprint\n"
            "- For room area questions: Use GetRoomArea\n"
            "- For analysis/reports: Use GenerateReport\n"
            "- For overlap detection: Use SpatialAnalysis"
        ),
        agent_config=agent_config,
        num_runs=1,  # Changed from 3 to 1 to prevent duplicate operations
    )
    
    # Manually set the actions in the agent's belief to ensure they are used
    agent.belief.set_actions(actions)

    return agent, analyzer


def get_modified_dxf_bytes(ingested_file_path: str) -> Optional[bytes]:
    """Retrieve the bytes of a DXF file if it exists.

    Args:
        ingested_file_path: Path to the DXF file

    Returns:
        The file's bytes or ``None`` if the file does not exist
    """
    if ingested_file_path and Path(ingested_file_path).exists():
        with open(ingested_file_path, "rb") as f:
            return f.read()
    return None


def main() -> None:
    """Entry point for the Streamlit application."""
    # Configure the page
    st.set_page_config(
        page_title="Blueprint Analysis Tool",
        page_icon="🏗️",
        layout="wide",
    )

    # Apply custom styling
    _apply_custom_css()

    # Build the sidebar and record the current view in session state
    _create_sidebar()
    user_choice = st.session_state.get("user_choice", "Upload & Analyze Blueprint")

    if user_choice == "Upload & Analyze Blueprint":
        _handle_upload_and_analyze()
    else:
        _handle_create_blueprint()


def _apply_custom_css() -> None:
    """Inject CSS styling into the Streamlit app."""
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            margin-bottom: 2rem;
        }
        .section-header {
            color: #0D47A1;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }
        .info-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #F5F9FF;
            border: 1px solid #90CAF9;
            color: #1976D2;
            margin-bottom: 1rem;
        }
        .success-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #F1F8F1;
            border: 1px solid #81C784;
            color: #2E7D32;
            margin-bottom: 1rem;
        }
        .warning-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #FFF3E0;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _create_sidebar() -> None:
    """Render the sidebar with operation selection and instructions."""
    with st.sidebar:
        st.markdown("### Blueprint Analysis Tools")
        user_choice = st.radio(
            "Choose Operation",
            ["Upload & Analyze Blueprint", "Create New Blueprint"],
            index=0,
        )
        st.session_state.user_choice = user_choice
        st.markdown(
            """
            Available operations:
            - Upload and analyze an existing blueprint
            - Create a new blueprint from a description
            """
        )


def _handle_upload_and_analyze() -> None:
    """Handle the upload and analysis flow for existing blueprints."""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(
            '<h2 class="section-header">Upload Blueprint</h2>',
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Choose a blueprint file",
            type=[
                "dxf",
                "ai",
                "cdr",
                "cgm",
                "dwg",
                "emf",
                "eps",
                "pdf",
                "ps",
                "sk",
                "sk1",
                "svg",
                "svgz",
                "vsd",
                "wmf",
            ],
        )
    if uploaded_file is not None:
        _process_uploaded_file(uploaded_file)


def _process_uploaded_file(uploaded_file) -> None:
    """Ingest and analyze a user‑uploaded blueprint using the Sherpa agent.

    This function saves the uploaded file to a temporary location, creates a new
    ``BlueprintAnalyzer`` and Sherpa agent, and uses the agent to call the
    ``HandleFileInput`` and ``ExtractFeatures`` actions.  The resulting
    features and summary are stored in the session state for use in
    subsequent queries.

    Args:
        uploaded_file: The file uploaded via Streamlit
    """
    try:
        # Determine if this is a new file upload to avoid reprocessing on reruns
        if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
            # Clear previous session state variables related to analysis
            for var in ["analyzer", "agent", "features", "current_file", "temp_path"]:
                if var in st.session_state:
                    del st.session_state[var]

            # Save the uploaded file to a temporary location on disk
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name

            # Create a new analyzer and Sherpa agent
            agent, analyzer = create_sherpa_agent()
            st.session_state.agent = agent
            st.session_state.analyzer = analyzer

            # Use Sherpa to ingest the file
            with st.spinner("Processing blueprint..."):
                # Handle file input via agent.  The action expects a quoted path.
                agent.shared_memory.add("task", "human", content=f"HandleFileInput '{temp_path}'")
                # Set the current task from the latest task in shared memory
                tasks = agent.shared_memory.get_by_type("task")
                if tasks:
                    agent.belief.set_current_task(tasks[-1].content)
                result = agent.run()
                file_response = result.content
                if "Error" in file_response:
                    st.error(file_response)
                    return

                # Extract features via agent.  No additional input required.
                agent.shared_memory.add("task", "human", content="ExtractFeatures")
                # Set the current task from the latest task in shared memory
                tasks = agent.shared_memory.get_by_type("task")
                if tasks:
                    agent.belief.set_current_task(tasks[-1].content)
                result = agent.run()
                feature_response = result.content

                # Store features and summarise for display
                st.session_state.features = analyzer.features
                st.session_state.current_file = uploaded_file.name
                st.session_state.temp_path = temp_path

                st.success("File processed and features extracted successfully!")
                # Display summary information returned by the extractor
                if feature_response:
                    st.info(feature_response)

        # Show the analysis interface regardless of whether this is a new upload
        _display_analysis_interface()

    except Exception as e:
        logging.error(f"Error processing blueprint: {e}", exc_info=True)
        st.error(f"Error processing blueprint: {str(e)}")


def _display_analysis_interface() -> None:
    """Render the interface for asking questions and modifying the blueprint."""
    st.markdown("### Blueprint Analysis Assistant")
    # Provide expandable context and example queries
    with st.expander("📊 Available Blueprint Information", expanded=False):
        st.markdown(
            f"""
            - Total Rooms: {len(st.session_state.features.get('rooms', {}))}
            - Room Names: {', '.join(st.session_state.features.get('rooms', {}).keys())}
            - Available Features: {', '.join(k for k, v in st.session_state.features.items() if v)}
            """
        )

    with st.expander("💡 Example Queries", expanded=False):
        st.markdown(
            """
            **Room Information & Analysis:**
            - What is the area of the kitchen?
            - Generate a report of all room sizes
            - What is the total floor area?
            - Analyze the layout efficiency
            - Check for overlapping elements

            **Layout Modifications:**
            - Remove room 'bedroom'
            - Remove all walls
            - Merge the living room and dining room
            """
        )

    # Input box for user queries
    user_query = st.text_area(
        "What would you like to know or modify about the blueprint?",
        placeholder="e.g., What is the area of the kitchen? or Merge the living room and dining room",
        height=100,
    )

    if st.button("Analyze", type="primary"):
        _process_analysis_query(user_query)


def _process_analysis_query(user_query: str) -> None:
    """Send a natural language query to the Sherpa agent and display the result."""
    if not user_query:
        st.warning("Please enter a query first.")
        return

    if "agent" not in st.session_state:
        st.error("Error: No blueprint has been processed yet. Please upload a file first.")
        return

    with st.spinner("Analyzing..."):
        try:
            agent: QAAgent = st.session_state.agent
            analyzer: BlueprintAnalyzer = st.session_state.analyzer

            # Send the query to the Sherpa agent.  The agent will decide which
            # actions to call based on the natural language input and return
            # the synthesized output.
            # Send the query to the Sherpa agent.  The agent will decide which
            # actions to call based on the natural language input and return
            # the synthesized output.
            # Add context about available actions to help the agent choose correctly
            task_with_context = f"""User query: {user_query}

Available actions:
- GetRoomArea: ONLY for SPECIFIC room area questions (e.g., 'kitchen area', 'bedroom size')
  DO NOT use for: 'number of rooms', 'total area', 'room count', 'list rooms'

- GenerateReport: DEFAULT action for MOST blueprint questions including:
  * 'number of rooms', 'room count', 'how many rooms'
  * 'total area', 'total floor area', 'overall size'  
  * 'room names', 'list of rooms', 'what rooms are there'
  * 'overview', 'summary', 'analysis', 'report'
  * ANY general question that doesn't ask about a specific room's area

- ModifyBlueprint: for layout modifications - IMPORTANT: Use structured parameters and recognize synonyms:
  * For room removal (recognize: remove/delete/get rid of/eliminate/take out/clear/erase):
    - action_type: "remove_room"
    - room_names: ["room_name"]
    - Examples: "delete kitchen", "get rid of bedroom", "eliminate bathroom"
  
  * For room merging (recognize: merge/combine/join/unite/connect/link):
    - action_type: "merge_rooms"
    - room_names: ["room1", "room2"]
    - Examples: "combine kitchen and dining", "join bedroom with bathroom"
  
  * For removing all walls/doors/windows (recognize: remove/delete/get rid of/eliminate/clear):
    - action_type: "remove_walls" or "remove_doors" or "remove_windows"
    - room_names: []
    - Examples: "delete walls", "get rid of doors", "clear windows"

- SpatialAnalysis: for overlap detection, spatial conflicts, and layout validation
- ExtractFeatures: only for initial feature extraction

CRITICAL: For "number of rooms" or similar general questions, use GenerateReport, NOT GetRoomArea!

Choose the appropriate action based on the user's request. If using GenerateReport, pass the user's query as the 'query' argument."""
            agent.shared_memory.add("task", "human", content=task_with_context)
            # Set the current task from the latest task in shared memory
            tasks = agent.shared_memory.get_by_type("task")
            if tasks:
                agent.belief.set_current_task(tasks[-1].content)
            result = agent.run()
            response = result.content

            # Display the response in a formatted box
            st.markdown("### Analysis Results")
            st.markdown(
                f"""
                <div style='background-color:rgb(96, 101, 111); padding: 20px; border-radius: 10px;'>
                {response}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Update session state features if the query likely modified the blueprint
            if any(keyword in user_query.lower() for keyword in ["merge", "remove", "modify"]):
                st.session_state.features = analyzer.features

        except Exception as e:
            logging.error(f"Analysis error: {e}", exc_info=True)
            st.error(f"Analysis error: {str(e)}")


def _handle_create_blueprint() -> None:
    """Render the interface for creating a new blueprint from a description."""
    st.markdown('<h2 class="section-header">Create New Blueprint</h2>', unsafe_allow_html=True)
    with st.expander("📝 Instructions & Examples", expanded=True):
        st.markdown(
            """
            Describe your blueprint layout in natural language. Include:
            - Plot dimensions (e.g., 50x30)
            - Room sizes and positions (north, south, east, west)
            - Door locations (optional)

            Example:
            ```
            Create a 50x30 plot with:
            - Living room (20x15) in the north
            - Kitchen (15x12) in the east
            - Bedroom (18x12) in the west
            ```
            """
        )

    dxf_prompt = st.text_area(
        "Describe your blueprint layout",
        height=150,
        placeholder="Enter your blueprint description here...",
    )
    if st.button("🎨 Create Blueprint", type="primary"):
        _create_new_blueprint(dxf_prompt)


def _create_new_blueprint(dxf_prompt: str) -> None:
    """Use the Sherpa agent to create a DXF blueprint from a natural language prompt."""
    if not dxf_prompt:
        st.warning("⚠️ Please enter a blueprint description first.")
        return

    # For creating a new blueprint we don't rely on an existing analyzer; we
    # instantiate a fresh agent with a new analyzer.  This ensures that
    # modifications to the current blueprint don't interfere with the new one.
    agent, _ = create_sherpa_agent()
    with st.spinner("Creating blueprint..."):
        try:
            # Send the natural language prompt to the agent.  The agent should
            # call the CreateDXFPlotAction and return a status message.
            agent.shared_memory.add("task", "human", content=dxf_prompt)
            # Set the current task from the latest task in shared memory
            tasks = agent.shared_memory.get_by_type("task")
            if tasks:
                agent.belief.set_current_task(tasks[-1].content)
            result = agent.run()
            response = result.content
            if not isinstance(response, str):
                st.error("Unexpected response from the agent.")
                return

            # Display the agent's message to the user
            if "successfully" in response.lower():
                st.success(response)
            else:
                st.info(response)

            # Attempt to locate the generated DXF file and provide a download link
            # The CreateDXFPlotAction writes to 'generated_plot_blueprint.dxf' by default.
            file_name = "generated_plot_blueprint.dxf"
            if Path(file_name).exists():
                with open(file_name, "rb") as f:
                    dxf_bytes = f.read()
                st.download_button(
                    label="Download DXF Blueprint",
                    data=dxf_bytes,
                    file_name=file_name,
                    mime="application/x-dxf",
                )
        except Exception as e:
            logging.error(f"Error creating blueprint: {e}", exc_info=True)
            st.error(f"Error creating blueprint: {str(e)}")


if __name__ == "__main__":
    main()