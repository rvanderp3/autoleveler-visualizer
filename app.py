from flask import Flask, render_template, jsonify, request
import os
import glob
import uuid

app = Flask(__name__)
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Store uploaded files in memory with their original names
uploaded_files = {}

def parse_xyz_file(filepath):
    """Parse an XYZ file and return coordinates and heights."""
    points = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    z = float(parts[2])
                    points.append({'x': x, 'y': y, 'z': z})
                except ValueError:
                    continue
    return points

def get_xyz_files():
    """Get list of all .xyz files in the application directory."""
    pattern = os.path.join(BASE_DIR, '*.xyz')
    files = glob.glob(pattern)
    return [os.path.basename(f) for f in files]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/files')
def list_files():
    """Return list of available XYZ files."""
    # Combine local files and uploaded files
    local_files = get_xyz_files()
    upload_files = list(uploaded_files.keys())
    all_files = local_files + [f for f in upload_files if f not in local_files]
    return jsonify(all_files)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.xyz'):
        return jsonify({'error': 'Invalid file type. Only .xyz files are allowed'}), 400

    # Save file to uploads directory
    filename = file.filename
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Handle duplicate names by adding a suffix
    base, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(filepath) or filename in uploaded_files:
        filename = f"{base}_{counter}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        counter += 1

    file.save(filepath)
    uploaded_files[filename] = filepath

    return jsonify({'filename': filename, 'success': True})

def get_file_path(filename):
    """Get the full path for a file, checking both local and upload directories."""
    filename = os.path.basename(filename)

    # Check uploads first
    if filename in uploaded_files:
        return uploaded_files[filename]

    # Check uploads directory
    upload_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(upload_path):
        return upload_path

    # Check local directory
    local_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(local_path):
        return local_path

    return None

@app.route('/data')
def get_data():
    filename = request.args.get('file', 'mesh.xyz')
    filter_outliers = request.args.get('filter_outliers', 'false').lower() == 'true'

    # Sanitize filename to prevent directory traversal
    filename = os.path.basename(filename)
    if not filename.endswith('.xyz'):
        return jsonify({'error': 'Invalid file type'}), 400

    xyz_file = get_file_path(filename)
    if not xyz_file:
        return jsonify({'error': 'File not found'}), 404

    points = parse_xyz_file(xyz_file)

    total_points_before_filter = len(points)
    outliers_removed = 0

    # Filter outliers if requested
    if filter_outliers and len(points) > 1:
        z_values = [p['z'] for p in points]
        mean = sum(z_values) / len(z_values)
        variance = sum((z - mean) ** 2 for z in z_values) / len(z_values)
        std_dev = variance ** 0.5

        lower_bound = mean - std_dev
        upper_bound = mean + std_dev

        filtered_points = [
            p for p in points
            if lower_bound <= p['z'] <= upper_bound
        ]
        outliers_removed = len(points) - len(filtered_points)
        points = filtered_points

    if not points:
        return jsonify({'error': 'No points remaining after filtering'}), 400

    # Extract unique x and y values to determine grid dimensions
    x_values = sorted(set(p['x'] for p in points))
    y_values = sorted(set(p['y'] for p in points))

    # Create a 2D grid of z values
    z_grid = []
    point_map = {(p['x'], p['y']): p['z'] for p in points}

    for y in y_values:
        row = []
        for x in x_values:
            row.append(point_map.get((x, y), None))
        z_grid.append(row)

    return jsonify({
        'x': x_values,
        'y': y_values,
        'z': z_grid,
        'points': points,
        'stats': {
            'outliers_removed': outliers_removed,
            'total_before_filter': total_points_before_filter
        }
    })

@app.route('/compare')
def compare_files():
    """Compare two XYZ files and return the difference."""
    file1 = request.args.get('file1', '')
    file2 = request.args.get('file2', '')
    filter_outliers = request.args.get('filter_outliers', 'false').lower() == 'true'

    # Sanitize filenames
    file1 = os.path.basename(file1)
    file2 = os.path.basename(file2)

    if not file1.endswith('.xyz') or not file2.endswith('.xyz'):
        return jsonify({'error': 'Invalid file type'}), 400

    path1 = get_file_path(file1)
    path2 = get_file_path(file2)

    if not path1 or not path2:
        return jsonify({'error': 'File not found'}), 404

    points1 = parse_xyz_file(path1)
    points2 = parse_xyz_file(path2)

    # Create point maps
    map1 = {(p['x'], p['y']): p['z'] for p in points1}
    map2 = {(p['x'], p['y']): p['z'] for p in points2}

    # Find common coordinates
    coords1 = set(map1.keys())
    coords2 = set(map2.keys())
    common_coords = coords1 & coords2

    if not common_coords:
        return jsonify({'error': 'No matching coordinates between files'}), 400

    # Calculate differences
    differences = []
    for coord in common_coords:
        diff = map1[coord] - map2[coord]
        differences.append({'x': coord[0], 'y': coord[1], 'z': diff})

    total_points_before_filter = len(differences)
    outliers_removed = 0

    # Filter outliers if requested
    if filter_outliers and len(differences) > 1:
        diff_values = [d['z'] for d in differences]
        mean = sum(diff_values) / len(diff_values)
        variance = sum((d - mean) ** 2 for d in diff_values) / len(diff_values)
        std_dev = variance ** 0.5

        lower_bound = mean - std_dev
        upper_bound = mean + std_dev

        filtered_differences = [
            d for d in differences
            if lower_bound <= d['z'] <= upper_bound
        ]
        outliers_removed = len(differences) - len(filtered_differences)
        differences = filtered_differences

    if not differences:
        return jsonify({'error': 'No points remaining after filtering'}), 400

    # Extract grid dimensions
    x_values = sorted(set(d['x'] for d in differences))
    y_values = sorted(set(d['y'] for d in differences))

    # Create difference grid (use None for missing points after filtering)
    diff_map = {(d['x'], d['y']): d['z'] for d in differences}
    z_grid = []
    for y in y_values:
        row = []
        for x in x_values:
            row.append(diff_map.get((x, y), None))
        z_grid.append(row)

    # Calculate statistics
    diff_values = [d['z'] for d in differences]
    min_diff = min(diff_values)
    max_diff = max(diff_values)
    mean_diff = sum(diff_values) / len(diff_values)
    abs_diffs = [abs(d) for d in diff_values]
    mean_abs_diff = sum(abs_diffs) / len(abs_diffs)
    rms = (sum(d**2 for d in diff_values) / len(diff_values)) ** 0.5

    return jsonify({
        'x': x_values,
        'y': y_values,
        'z': z_grid,
        'points': differences,
        'stats': {
            'min': min_diff,
            'max': max_diff,
            'mean': mean_diff,
            'mean_abs': mean_abs_diff,
            'rms': rms,
            'total_points': len(differences),
            'matched_points': len(common_coords),
            'file1_points': len(points1),
            'file2_points': len(points2),
            'outliers_removed': outliers_removed,
            'total_before_filter': total_points_before_filter
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
