# Blueprint Parser Creator Demo

A Streamlit application that integrates a Sherpa AI agent for intelligent blueprint analysis and modification. This demo allows users to upload blueprint files (DXF, DWG, etc.), extract features, ask questions, and modify layouts using natural language.

## Features

- **File Upload & Conversion**: Upload blueprint files in various formats (DXF, DWG, PDF, etc.) with automatic conversion to DXF
- **Intelligent Analysis**: Ask natural language questions about your blueprint
- **Feature Extraction**: Automatically extract rooms, walls, doors, and other architectural elements
- **Layout Modifications**: Modify blueprints using natural language commands
- **Comprehensive Reports**: Generate detailed analysis reports
- **Spatial Analysis**: Detect overlapping elements and spatial conflicts
- **New Blueprint Creation**: Create new blueprints from natural language descriptions with automatic overlap detection

## Prerequisites

### Required Environment Variables

You need to set up the following environment variables:

1. **Copy the sample environment file**:
   ```bash
   cp .env-sample .env
   ```

2. **Edit the .env file** and replace the placeholder values with your actual API keys:
   ```bash
   # Edit .env file
   nano .env
   ```

   The `.env` file should contain:
   ```bash
   # OpenAI API Key - Required for language model functionality
   # Get your key from: https://platform.openai.com/api-keys
   OPENAI_API_KEY=your_openai_api_key_here

   # CloudConvert API Key - Required for file format conversion
   # Get your key from: https://cloudconvert.com/api
   CLOUDCONVERT_API_KEY=your_cloudconvert_api_key_here
   ```

   Or set environment variables directly:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export CLOUDCONVERT_API_KEY="your-cloudconvert-api-key"
   ```

### Installation

1. **Clone or download** the project files to your local machine

2. **Navigate to the project directory**:
   ```bash
   cd demo/blueprint_parser_creator
   ```

3. **Install all required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install streamlit langchain-community pydantic ezdxf shapely cloudconvert python-dotenv sherpa-ai
   ```

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Copy sample environment file
   cp .env-sample .env
   # Edit .env file and add your actual API keys
   nano .env
   ```

3. **Start the application**:
   ```bash
   streamlit run main.py
   ```

4. **Open your browser** at `http://localhost:8501`

## Usage

### Starting the Application

```bash
cd demo/blueprint_parser_creator
streamlit run main.py
```

The application will open in your browser at `http://localhost:8501`.

### Uploading a Blueprint

1. Click "Upload & Analyze Blueprint" in the sidebar
2. Upload your blueprint file (supports DXF, DWG, PDF, and many other formats)
3. The system will automatically convert and extract features from your blueprint

### Asking Questions

Once your blueprint is uploaded, you can ask questions like:

#### Room Information & Analysis
- "What is the area of the kitchen?"
- "Generate a report of all room sizes"
- "What is the total floor area?"
- "Analyze the layout efficiency"
- "Check for overlapping elements"

#### Layout Modifications
- "Remove room bedroom"
- "Remove all walls"
- "Merge the living room and dining room"

### Creating New Blueprints

1. Click "Create New Blueprint" in the sidebar
2. Describe your desired layout in natural language, for example:
   ```
   Create a 50x30 plot with:
   - Living room (20x15) in the north
   - Kitchen (15x12) in the east
   - Bedroom (18x12) in the west
   ```
3. The system will generate a DXF file that you can download

## Supported File Formats

### Input Formats (Auto-converted to DXF)
- **Vector formats**: AI, CDR, CGM, DWG, EMF, EPS, SK, SK1, SVG, SVGZ, VSD, WMF
- **Document formats**: PDF, PS
- **Native format**: DXF (no conversion needed)

### Output Format
- **DXF**: AutoCAD Drawing Exchange Format

## Architecture

### Core Components

1. **BlueprintAnalyzer**: Main class that handles file processing, feature extraction, and modifications
2. **BlueprintFeatureExtractor**: Extracts rooms, walls, doors, and other features from DXF files
3. **Sherpa AI Agent**: Intelligent agent that understands natural language queries and selects appropriate actions
4. **Streamlit UI**: User-friendly web interface

### Actions Available to the Agent

- **HandleFileInput**: Process uploaded blueprint files
- **ExtractFeatures**: Extract rooms, walls, doors, windows, and other features
- **GetRoomArea**: Calculate area of specific rooms
- **ModifyBlueprint**: Modify layout (merge rooms, remove walls/doors/windows, etc.)
- **GenerateReport**: Generate analysis reports
- **SpatialAnalysis**: Detect overlapping elements and spatial conflicts
- **CreateDXFPlot**: Create new blueprints from descriptions with automatic overlap detection

## Example Queries and Responses

### Room Area Query
**User**: "What is the area of the kitchen?"
**Agent**: Uses `GetRoomArea` action
**Response**: "The area of 'kitchen' is 150.00 square units."

### Layout Analysis
**User**: "Analyze the layout efficiency"
**Agent**: Uses `GenerateReport` action with comprehensive analysis
**Response**: Detailed report with executive summary, layout analysis, space utilization, and improvement suggestions

### Layout Modification
**User**: "Remove the bedroom"
**Agent**: Uses `ModifyBlueprint` action
**Response**: "Room(s) bedroom removed from the blueprint."

### Spatial Analysis
**User**: "Check for overlapping elements"
**Agent**: Uses `SpatialAnalysis` action
**Response**: "⚠️ Layout Analysis: Overlapping elements detected:
🚨 ROOM OVERLAPS:
  • living room overlaps with bedroom (50.0% overlap)
  • living room overlaps with kitchen (50.0% overlap)
🚨 WALL-ROOM CONFLICTS:
  • Wall from (12, 15) to (18, 15) conflicts with bedroom
📊 Summary: 3 issues found (3 high, 0 medium, 0 low severity)"

## Troubleshooting

### Common Issues

1. **"Features have already been extracted"**
   - This is normal after initial feature extraction
   - The agent will use other actions for subsequent queries

2. **"Room not found"**
   - Check the available room names in the sidebar
   - Use exact room names as shown

3. **File conversion errors**
   - Ensure your CloudConvert API key is valid
   - Check that the file format is supported

4. **Import errors**
   - Make sure all dependencies are installed
   - Verify environment variables are set

### Debugging

The application includes comprehensive logging. Check the console output for detailed error messages and debugging information.

## API Keys Setup

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account and add billing information
3. Generate an API key
4. Set the environment variable: `export OPENAI_API_KEY="your-key"`

### CloudConvert API Key
1. Go to [CloudConvert](https://cloudconvert.com/)
2. Create an account
3. Go to API section and generate an API key
4. Set the environment variable: `export CLOUDCONVERT_API_KEY="your-key"`

## Technical Details

### Feature Extraction Process
1. **File Conversion**: Non-DXF files are converted using CloudConvert API
2. **Layer Analysis**: The system analyzes DXF layers to identify architectural elements
3. **Entity Mapping**: Maps DXF entities to features (walls, rooms, doors, etc.)
4. **Room Matching**: Matches text labels with polygon boundaries to identify room names
5. **Feature Storage**: Stores extracted features for analysis and modification

### Agent Decision Making
The Sherpa AI agent uses a ReactPolicy to select appropriate actions based on:
- User query content and intent
- Available actions and their descriptions
- Current blueprint state
- Previous action history

### Report Generation
Reports are generated using OpenAI's language models with prompts tailored to:
- Room size analysis
- Layout efficiency evaluation
- Total area calculations
- Comprehensive architectural analysis

## Testing

The demo includes comprehensive tests to ensure everything works correctly.

### Quick Test
Run the simple test runner:
```bash
python tests/run_tests.py
```

### Comprehensive Tests
For detailed testing with pytest:
```bash
# Install test dependencies
pip install pytest pytest-mock

# Run all tests
python -m pytest tests/test_blueprint_demo.py -v

# Run specific test categories
python -m pytest tests/test_blueprint_demo.py::TestBlueprintActions -v
python -m pytest tests/test_blueprint_demo.py::TestBlueprintAnalyzer -v
```

### Test Coverage
The tests cover:
- Action creation and configuration
- Analyzer initialization and methods
- Import validation
- Environment configuration
- File structure verification

## Contributing

To contribute to this demo:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This demo is part of the Sherpa AI project. Please refer to the main project license for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the console logs for error messages
3. Open an issue in the project repository
4. Ensure all prerequisites are properly configured
