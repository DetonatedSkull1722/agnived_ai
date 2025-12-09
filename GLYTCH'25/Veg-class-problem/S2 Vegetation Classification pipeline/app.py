from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import torch
import traceback

from Vegetation_Classification_pipeline import (
    AOIConfig,
    BigEarthConfig,
    run_bigearth_rdnet,
)

app = Flask(__name__)
CORS(app)

# Global device configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@app.route('/classify', methods=['POST'])
def classify():
    """
    Single API endpoint to run vegetation classification.
    
    Expected JSON body:
    {
        "lon": 77.303778,
        "lat": 28.560278,
        "buffer_km": 3.0,
        "mask_path": "D:\\path\\to\\vegetation_mask.tif"  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        if 'lon' not in data or 'lat' not in data:
            return jsonify({"error": "Missing required fields: lon, lat"}), 400
        
        # Create AOI configuration
        cfg = AOIConfig(
            lon=float(data['lon']),
            lat=float(data['lat']),
            buffer_km=float(data.get('buffer_km', 3.0))
        )
        
        # Handle mask path if provided
        mask_path = None
        if 'mask_path' in data and data['mask_path']:
            mask_path = Path(data['mask_path'])
            if not mask_path.exists():
                return jsonify({"error": f"Mask file not found: {mask_path}"}), 400
        
        # Run the classification
        print(f"Running classification for: lon={cfg.lon}, lat={cfg.lat}, buffer_km={cfg.buffer_km}")
        res = run_bigearth_rdnet(cfg, veg_mask_path=mask_path, device=device)
        
        # Prepare response matching the original output format
        result = {
            "status": "success",
            "aoi": {
                "lon": res.aoi.lon,
                "lat": res.aoi.lat,
                "buffer_km": res.aoi.buffer_km
            },
            "cube_path": str(res.cube_path),
            "viz_path": str(res.viz_path),
            "class_distribution": res.class_distribution,
            "tile_counts": res.tile_counts,
            "avg_confidence": res.avg_confidence,
            "tiles_shape": res.tiles_shape
        }
        
        # Print output similar to original script
        print("AOI:", res.aoi)
        print("Cube:", res.cube_path)
        print("Viz:", res.viz_path)
        print("Classes:")
        for k, v in sorted(res.class_distribution.items(), key=lambda kv: kv[1], reverse=True):
            print(f"  {k:<65} {v:5.1f}% ({res.tile_counts[k]} tiles)")
        print(f"Average confidence: {res.avg_confidence:.1%}")
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except RuntimeError as e:
        return jsonify({"error": f"Runtime error: {str(e)}"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == '__main__':
    print(f"Starting Vegetation Classification Flask API...")
    print(f"Device: {device}")
    app.run(host='0.0.0.0', port=5000, debug=True)
