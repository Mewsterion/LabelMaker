# LabelMaker

A simple local web application to generate shipping labels.

## Features

- **EasyPost Integration**: Generate official shipping labels using your EasyPost account.
- **Local PDF Generation**: Generate simple 4x6 shipping label PDFs locally without an API.

## Setup

1. **Install Python**: Ensure you have Python installed.
2. **Install Dependencies**:

    ```bash
    pip install flask flask-cors python-dotenv requests reportlab
    ```

## Configuration

To use the **EasyPost** feature, you must configure your API keys.

1. Create a file named `.env` in this directory.
2. Add your EasyPost credentials:

    ```env
    EASYPOST_API_KEY=your_api_key_here
    EASYPOST_CARRIER_ACCOUNT_ID=your_carrier_account_id_here
    ```

> **Note**: The "Local PDF" feature works without any configuration.

## Running the Server

1. Start the backend server:

    ```bash
    python label_server.py
    ```

2. Open your browser and navigate to:
    `http://localhost:5000`

## Usage

- **EasyPost Mode**: Select "EasyPost", enter address and weight, and click "Create Label". This will deduct postage from your account.
- **Local PDF Mode**: Select "Local PDF", enter address, and click "Create Label". This generates a PDF you can print immediately (no postage purchased).
