# AutoLeveler Visualizer

A Flask-based web application for visualizing and comparing autoleveling probe data from [Universal Gcode Sender (UGS)](https://winder.github.io/ugs_website/).

## Overview

When using UGS's autoleveling feature for CNC routing, the software probes your workpiece surface and generates an XYZ height map. This tool helps you:

- Visualize the probe data to understand surface irregularities
- Compare probe results before and after surfacing operations
- Identify problem areas or outliers in your measurements
- Verify your wasteboard or workpiece flatness

## Features

- **Single File View**: Visualize height data from a single probe file
- **Compare Files**: Compare two probe files and display the difference map
- **File Upload**: Browse and upload XYZ files from anywhere on your computer
- **Multiple Visualization Types**:
  - 3D Surface plot
  - 2D Heatmap
  - Contour map
- **Outlier Filtering**: Remove statistical outliers (points outside 1 standard deviation) to focus on representative surface data
- **Statistics Display**: View min, max, range, RMS, and other metrics
- **Multiple Color Scales**: Viridis, Jet, Hot, Earth, and more

## Requirements

- Python 3.10+
- Flask

## Installation

1. Install Python from https://www.python.org/downloads/

2. Install Flask:
   ```bash
   pip install flask
   ```

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Open http://localhost:5000 in your browser

3. Either:
   - Place `.xyz` files in the application directory and select from the dropdown
   - Click "Browse..." to upload files from anywhere on your computer

## UGS Autoleveling Workflow

1. In UGS, set up your probe grid under **Tools > AutoLeveler**
2. Run the probe routine to scan your surface
3. Export/save the probe data as an XYZ file
4. Load the file in AutoLeveler Visualizer to analyze

## XYZ File Format

The application expects space-separated XYZ files as exported by UGS:
```
0.0 0.0 -0.76
0.0 100.0 -0.82
100.0 0.0 -1.03
...
```

Each line contains: `X_position Y_position Z_height`

## Controls

### Single File Mode
- **File**: Select which XYZ file to view, or click "Browse..." to upload
- **Color Scale**: Choose the color mapping
- **View Type**: Switch between 3D Surface, 2D Heatmap, or Contour
- **Filter Outliers**: Remove points outside 1 standard deviation

### Compare Files Mode
- **File 1 / File 2**: Select two files to compare (e.g., before/after surfacing)
- **Color Scale**: Red-Blue diverging scale recommended for differences
- **View Type**: Switch between visualization types
- **Filter Outliers**: Remove difference outliers caused by probe errors or debris

## Statistics

### Single File
- Min/Max Height
- Height Range
- Total Points
- Outliers Removed (when filtering)

### Comparison
- Min/Max Difference
- Mean Difference
- Mean Absolute Difference
- RMS (Root Mean Square)
- Matched Points
- Outliers Removed (when filtering)

## Sample Data

The `samples/` folder contains real probe data from a spoilboard at various phases of the leveling process. Use these files to explore the application's features or as a reference for the expected data format.

## Use Cases

- **Wasteboard Flatness**: Probe your wasteboard and visualize high/low spots before surfacing
- **Before/After Comparison**: Compare probe data before and after a surfacing operation to verify improvement
- **Material Inspection**: Check workpiece flatness before machining
- **Troubleshooting**: Identify probe errors or measurement issues
