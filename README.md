# Automated Data Analysis Agent

## Overview

This project implements an AI-powered automated data analysis agent designed to perform comprehensive exploratory data analysis (EDA) on CSV datasets. The agent follows a structured reasoning approach, breaking down the analysis process into four distinct phases: Retrieve, Plan, Analyze, and Respond.

## Type of Agent and Reasoning

### Agent Type
This is a **reasoning-based AI agent** that combines traditional data science workflows with large language model capabilities. Unlike purely statistical or machine learning-based approaches, this agent uses structured reasoning to systematically analyze datasets, making it more interpretable and reliable for data exploration tasks.

### Why This Agent Type?
The agent-based approach was chosen for several key reasons:

1. **Modular Reasoning**: Breaking analysis into distinct phases (Retrieve → Plan → Analyze → Respond) allows for better error handling, debugging, and human oversight.

2. **AI-Augmented Decision Making**: Uses Google Gemini AI for intelligent planning of data cleaning and EDA strategies, while maintaining control through structured execution.

3. **Reproducibility**: Structured approach ensures consistent analysis patterns across different datasets.

## System Architecture

The system follows a modular architecture organized into several key components:

```
data-analysis-agent/
├── agent/                    # Core reasoning phases
│   ├── retrieve.py          # Data loading and initial parsing
│   ├── plan.py              # AI-powered planning phase
│   ├── analyze.py           # EDA execution phase
│   └── respond.py           # Final report generation
├── cleaner/                 # Data preprocessing utilities
│   ├── auto_clean.py        # Automated data cleaning
│   ├── parse_date.py        # Date parsing functions
│   ├── convert_numeric.py   # Numeric conversion
│   └── explode.py           # Column splitting
├── explain/                 # AI-powered planning and reporting
│   ├── gemini.py            # Google Gemini integration
│   ├── data_prep.py         # Data cleaning plan generation
│   ├── eda_plan.py          # EDA plan generation
│   └── final_report.py      # Narrative report creation
├── adaptive_eda_executor/   # Chart generation and statistics
│   ├── adaptive_eda_executor.py  # Main EDA execution
│   └── utils.py             # Helper functions
├── reporter/                # Output generation
│   ├── generate_report.py   # JSON metadata report
│   ├── save_report.py       # Markdown report saving
│   └── utils.py             # Utility functions
└── sample_inputs/           # Example datasets
```

## Reasoning Process

The agent follows a four-phase structured reasoning process:

### 1. Retrieve Phase
- Loads CSV data using pandas
- Performs initial data parsing and validation
- Extracts basic metadata (columns, data types, missing values)
- Returns confidence score for data loading success

### 2. Plan Phase
- Uses Google Gemini AI to analyze dataset sample
- Generates data cleaning plan (explode columns, parse dates, convert numerics)
- Creates EDA plan with specific analysis types and target columns
- Returns structured plans with confidence scores

### 3. Analyze Phase
- Executes adaptive EDA based on the generated plan
- Generates visualizations using matplotlib and seaborn
- Computes summary statistics
- Supports multiple analysis types:
  - Univariate Analysis
  - Temporal Trend Analysis
  - Geographical Distribution Analysis
  - Categorical Distribution Analysis
  - Comparative Duration Analysis
  - Distribution Analysis
  - Product Category Impact Analysis
  - Demographic Distribution Analysis

### 4. Respond Phase
- Synthesizes all results into a comprehensive narrative report
- Uses AI to generate insights and recommendations
- Creates final Markdown report with embedded chart references
- Saves structured JSON output with metadata

## Tools and Libraries

### Core Dependencies
- **pandas** (2.3.3): Data manipulation and analysis
- **numpy** (2.3.3): Numerical computing
- **matplotlib** (3.10.7): Plotting and visualization
- **seaborn** (0.13.2): Statistical data visualization
- **scikit-learn** (1.7.2): Machine learning utilities
- **scipy** (1.16.2): Scientific computing

### AI Integration
- **google-genai** (1.43.0): Google Gemini AI integration
- **google-api-python-client** (2.184.0): Google API client

### Utilities
- **python-dotenv** (1.1.1): Environment variable management
- **tenacity** (9.1.2): Retry mechanisms
- **tabulate** (0.9.0): Table formatting
- **Pillow** (11.3.0): Image processing
- **joblib** (1.5.2): Parallel processing

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation
1. Clone the repository:
```bash
git clone <repository-url>
cd data-analysis-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration
1. Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your_google_gemini_api_key_here
```

## Usage

### Basic Usage
Run the analysis pipeline on a CSV file:

```bash
python agent.py --input sample_inputs/black_friday.csv
```

### With Custom Output Folder
Specify a custom output folder name:

```bash
python agent.py --input sample_inputs/netflix.csv --output my_analysis
```

### Output Structure
The agent creates a timestamped output folder in `sample_outputs/` containing:
- `FINAL_EDA_REPORT.md`: Comprehensive narrative report
- `metadata_summary.json`: Structured metadata and plans
- `structured_output.json`: Complete pipeline results
- `charts/`: Generated visualization files
- `eda_outputs/`: Additional analysis outputs

### Example Datasets
The `sample_inputs/` directory contains example datasets sourced from Kaggle:
- `black_friday.csv`: E-commerce purchase data
- `netflix.csv`: Streaming platform content data


