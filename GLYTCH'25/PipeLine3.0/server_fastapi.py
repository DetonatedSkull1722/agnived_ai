import glob
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import traceback
import os
import json
from PIL import Image
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

# Import the landcover pipeline
from landcover.LandCover import AOIConfig as LandcoverAOIConfig, DownloadConfig, run_landcover_pipeline
# Import the vegetation pipeline
from vegetation.Vegetation_Classification_pipeline import AOIConfig as VegAOIConfig, run_bigearth_rdnet

# GoogleVR4 imports
import GoogleVR4.core as core
from GoogleVR4.ObjectIdentifier import run_object_detection

app = FastAPI(title="AgniVed Pipeline API", version="1.0.0")

# Plant model for classification
PLANT_MODEL_ID = "juppy44/plant-identification-2m-vit-b"
plant_processor = AutoImageProcessor.from_pretrained(PLANT_MODEL_ID)
plant_model = AutoModelForImageClassification.from_pretrained(PLANT_MODEL_ID)

# Pydantic models for request validation
class PanosRequest(BaseModel):
    lat: float
    lon: float
    count: int = 3
    area_of_interest: float = 100.0
    min_distance: float = 10.0

class DetectObjectsRequest(BaseModel):
    image_path: str
    labels: List[str] = ["tree", "bushes"]

class PanosDetectObjectsRequest(BaseModel):
    lat: float
    lon: float
    count: int = 3
    area_of_interest: float = 100.0
    min_distance: float = 10.0
    labels: List[str] = ["tree", "bushes"]

class ClassifyPlantRequest(BaseModel):
    image_path: str

class PanosDetectAndClassifyRequest(BaseModel):
    lat: float
    lon: float
    count: int = 3
    area_of_interest: float = 100.0
    min_distance: float = 10.0
    labels: List[str] = ["tree", "bushes"]

class LandcoverRequest(BaseModel):
    lon: float
    lat: float
    buffer_km: float = 3.0
    date_start: str = "2024-10-01"
    date_end: str = "2024-11-15"
    scale: int = 10
    cloud_cover_max: int = 20

class VegetationRequest(BaseModel):
    lon: float
    lat: float
    buffer_km: float = 3.0
    mask_path: Optional[str] = None

class LandcoverVegetationRequest(BaseModel):
    lon: float
    lat: float
    buffer_km: float = 3.0
    date_start: str = "2024-10-01"
    date_end: str = "2024-11-15"
    scale: int = 10
    cloud_cover_max: int = 20

class LandcoverVegetationPanosRequest(BaseModel):
    lon: float
    lat: float
    buffer_km: float = 3.1
    date_start: str = "2024-10-01"
    date_end: str = "2024-11-15"
    scale: int = 10
    cloud_cover_max: int = 20
    panos_lat: Optional[float] = None
    panos_lon: Optional[float] = None
    panos_count: int = 3
    panos_area_of_interest: float = 100.0
    panos_min_distance: float = 20.0
    panos_labels: List[str] = ["tree", "bushes"]

@app.get("/")
async def root():
    return {"message": "AgniVed Pipeline API - Use /docs for API documentation"}

@app.post('/panos')
async def panos_api(request: PanosRequest):
    result = core.find_panos_and_views(
        lat=request.lat,
        lon=request.lon,
        n=request.count,
        radius_m=request.area_of_interest,
        min_distance_m=request.min_distance
    )
    # Save result to out/panos_result.json
    out_dir = os.path.join(os.path.dirname(__file__), 'out')
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, 'panos_result.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    return result

@app.post('/detect_objects')
async def detect_objects_api(request: DetectObjectsRequest):
    result = run_object_detection(request.image_path, request.labels)
    return result

@app.post('/panos_detect_objects')
async def panos_detect_objects_api(request: PanosDetectObjectsRequest):
    # Step 1: Run panos search
    pano_result = core.find_panos_and_views(
        lat=request.lat,
        lon=request.lon,
        n=request.count,
        radius_m=request.area_of_interest,
        min_distance_m=request.min_distance
    )
    # Save pano result JSON
    out_dir = os.path.join(os.path.dirname(__file__), 'out')
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, 'panos_detect_objects_result.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(pano_result, f, indent=2)

    # Step 2: For each pano image, run object detection
    detected_objects = []
    for img in pano_result.get('images', []):
        if img.get('pano_downloaded'):
            pano_path = img.get('pano_path')
            if pano_path and os.path.exists(pano_path):
                detect_result = run_object_detection(pano_path, request.labels)
                detected_objects.append({
                    'pano_id': img.get('id'),
                    'pano_path': pano_path,
                    'object_detection': detect_result
                })
            else:
                detected_objects.append({
                    'pano_id': img.get('id'),
                    'pano_path': pano_path,
                    'object_detection': 'Pano image not found.'
                })
        else:
            detected_objects.append({
                'pano_id': img.get('id'),
                'pano_path': img.get('pano_path'),
                'object_detection': 'Pano not downloaded.'
            })

    # Step 3: Return combined result
    combined_result = {
        'pano_result': pano_result,
        'detected_objects': detected_objects
    }
    return combined_result

@app.post('/classify_plant')
async def classify_plant_api(request: ClassifyPlantRequest):
    if not request.image_path or not os.path.exists(request.image_path):
        raise HTTPException(status_code=400, detail="image_path not provided or file does not exist")
    try:
        image = Image.open(request.image_path)
        inputs = plant_processor(images=image, return_tensors="pt")
        with torch.no_grad():
            logits = plant_model(**inputs).logits
        pred = logits.softmax(dim=-1)[0]
        topk = torch.topk(pred, k=5)
        results = []
        for prob, idx in zip(topk.values, topk.indices):
            label = plant_model.config.id2label[idx.item()]
            results.append({"label": label, "probability": float(prob.item())})
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/panos_detect_and_classify')
async def panos_detect_and_classify_api(request: PanosDetectAndClassifyRequest):
    # Step 1: Run panos search and object detection
    pano_result = core.find_panos_and_views(
        lat=request.lat,
        lon=request.lon,
        n=request.count,
        radius_m=request.area_of_interest,
        min_distance_m=request.min_distance
    )
    out_dir = os.path.join(os.path.dirname(__file__), 'out')
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, 'panos_detect_and_classify_result.json')

    detected_objects = []
    classify_results = []

    for img in pano_result.get('images', []):
        if img.get('pano_downloaded'):
            pano_path = img.get('pano_path')
            if pano_path and os.path.exists(pano_path):
                detect_result = run_object_detection(pano_path, request.labels)
                detected_objects.append({
                    'pano_id': img.get('id'),
                    'pano_path': pano_path,
                    'object_detection': detect_result
                })

                # Step 2: For each detected crop, classify plant
                crop_dir = os.path.join(os.path.dirname(pano_path), '..', 'detected_crops')
                crop_dir = os.path.abspath(crop_dir)
                crop_images = glob.glob(os.path.join(crop_dir, '*.jpg'))
                crop_classifications = []
                for crop_img in crop_images:
                    try:
                        image = Image.open(crop_img)
                        inputs = plant_processor(images=image, return_tensors="pt")
                        with torch.no_grad():
                            logits = plant_model(**inputs).logits
                        pred = logits.softmax(dim=-1)[0]
                        topk = torch.topk(pred, k=5)
                        results = []
                        for prob, idx in zip(topk.values, topk.indices):
                            label = plant_model.config.id2label[idx.item()]
                            results.append({"label": label, "probability": float(prob.item())})
                        crop_classifications.append({
                            "crop_image": crop_img,
                            "classification": results
                        })
                    except Exception as e:
                        crop_classifications.append({
                            "crop_image": crop_img,
                            "error": str(e)
                        })
                classify_results.append({
                    'pano_id': img.get('id'),
                    'crop_classifications': crop_classifications
                })
            else:
                detected_objects.append({
                    'pano_id': img.get('id'),
                    'pano_path': pano_path,
                    'object_detection': 'Pano image not found.'
                })
        else:
            detected_objects.append({
                'pano_id': img.get('id'),
                'pano_path': img.get('pano_path'),
                'object_detection': 'Pano not downloaded.'
            })

    combined_result = {
        'pano_result': pano_result,
        'detected_objects': detected_objects,
        'classify_results': classify_results
    }
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(combined_result, f, indent=2)
    return combined_result

@app.post('/run_landcover')
async def run_landcover(request: LandcoverRequest):
    try:
        parent_dir = Path(__file__).resolve().parent
        results_dir = parent_dir / "LandcoverResults"
        aoi_cfg = LandcoverAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        dl_cfg = DownloadConfig(
            output_dir=results_dir,
            date_start=request.date_start,
            date_end=request.date_end,
            scale=request.scale,
            cloud_cover_max=request.cloud_cover_max,
        )
        outputs = run_landcover_pipeline(aoi_cfg, dl_cfg)
        return {k: str(v) for k, v in outputs.items()}
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e), 'trace': traceback.format_exc()})

@app.post('/run_vegetation')
async def run_vegetation(request: VegetationRequest):
    try:
        mask_path = request.mask_path
        if not mask_path:
            parent_dir = Path(__file__).resolve().parent
            mask_path = str(parent_dir / "LandcoverResults" / "vegetation_mask.tif")
        aoi_cfg = VegAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        res = run_bigearth_rdnet(aoi_cfg, veg_mask_path=Path(mask_path))
        result = {
            'aoi': vars(res.aoi) if hasattr(res.aoi, '__dict__') else str(res.aoi),
            'cube_path': str(res.cube_path),
            'viz_path': str(res.viz_path),
            'class_distribution': res.class_distribution,
            'tile_counts': res.tile_counts,
            'avg_confidence': res.avg_confidence,
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e), 'trace': traceback.format_exc()})

@app.post('/run_landcover_and_vegetation')
async def run_landcover_and_vegetation(request: LandcoverVegetationRequest):
    try:
        parent_dir = Path(__file__).resolve().parent
        results_dir = parent_dir / "LandcoverResults"
        # Landcover pipeline
        aoi_cfg = LandcoverAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        dl_cfg = DownloadConfig(
            output_dir=results_dir,
            date_start=request.date_start,
            date_end=request.date_end,
            scale=request.scale,
            cloud_cover_max=request.cloud_cover_max,
        )
        landcover_outputs = run_landcover_pipeline(aoi_cfg, dl_cfg)
        # Vegetation pipeline (use mask from landcover output)
        mask_path = landcover_outputs.get('vegetation_mask')
        veg_aoi_cfg = VegAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        veg_res = run_bigearth_rdnet(veg_aoi_cfg, veg_mask_path=Path(mask_path))
        veg_result = {
            'aoi': vars(veg_res.aoi) if hasattr(veg_res.aoi, '__dict__') else str(veg_res.aoi),
            'cube_path': str(veg_res.cube_path),
            'viz_path': str(veg_res.viz_path),
            'class_distribution': veg_res.class_distribution,
            'tile_counts': veg_res.tile_counts,
            'avg_confidence': veg_res.avg_confidence,
        }
        return {
            'landcover': {k: str(v) for k, v in landcover_outputs.items()},
            'vegetation': veg_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e), 'trace': traceback.format_exc()})

@app.post('/run_landcover_vegetation_and_panos')
async def run_landcover_vegetation_and_panos(request: LandcoverVegetationPanosRequest):
    try:
        # Landcover/vegetation: area_of_interest > 3km
        parent_dir = Path(__file__).resolve().parent
        results_dir = parent_dir / "LandcoverResults"
        aoi_cfg = LandcoverAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        dl_cfg = DownloadConfig(
            output_dir=results_dir,
            date_start=request.date_start,
            date_end=request.date_end,
            scale=request.scale,
            cloud_cover_max=request.cloud_cover_max,
        )
        landcover_outputs = run_landcover_pipeline(aoi_cfg, dl_cfg)
        mask_path = landcover_outputs.get('vegetation_mask')
        veg_aoi_cfg = VegAOIConfig(lon=request.lon, lat=request.lat, buffer_km=request.buffer_km)
        veg_res = run_bigearth_rdnet(veg_aoi_cfg, veg_mask_path=Path(mask_path))
        veg_result = {
            'aoi': vars(veg_res.aoi) if hasattr(veg_res.aoi, '__dict__') else str(veg_res.aoi),
            'cube_path': str(veg_res.cube_path),
            'viz_path': str(veg_res.viz_path),
            'class_distribution': veg_res.class_distribution,
            'tile_counts': veg_res.tile_counts,
            'avg_confidence': veg_res.avg_confidence,
        }
        # Panos detect & classify: area_of_interest < 150m
        panos_lat = request.panos_lat if request.panos_lat is not None else request.lat
        panos_lon = request.panos_lon if request.panos_lon is not None else request.lon
        pano_result = core.find_panos_and_views(
            lat=panos_lat,
            lon=panos_lon,
            n=request.panos_count,
            radius_m=request.panos_area_of_interest,
            min_distance_m=request.panos_min_distance
        )
        detected_objects = []
        classify_results = []
        for img in pano_result.get('images', []):
            if img.get('pano_downloaded'):
                pano_path = img.get('pano_path')
                if pano_path and os.path.exists(pano_path):
                    detect_result = run_object_detection(pano_path, request.panos_labels)
                    detected_objects.append({
                        'pano_id': img.get('id'),
                        'pano_path': pano_path,
                        'object_detection': detect_result
                    })
                    crop_dir = os.path.join(os.path.dirname(pano_path), '..', 'detected_crops')
                    crop_dir = os.path.abspath(crop_dir)
                    crop_images = glob.glob(os.path.join(crop_dir, '*.jpg'))
                    crop_classifications = []
                    for crop_img in crop_images:
                        try:
                            image = Image.open(crop_img)
                            inputs = plant_processor(images=image, return_tensors="pt")
                            with torch.no_grad():
                                logits = plant_model(**inputs).logits
                            pred = logits.softmax(dim=-1)[0]
                            topk = torch.topk(pred, k=5)
                            results = []
                            for prob, idx in zip(topk.values, topk.indices):
                                label = plant_model.config.id2label[idx.item()]
                                results.append({"label": label, "probability": float(prob.item())})
                            crop_classifications.append({
                                "crop_image": crop_img,
                                "classification": results
                            })
                        except Exception as e:
                            crop_classifications.append({
                                "crop_image": crop_img,
                                "error": str(e)
                            })
                    classify_results.append({
                        'pano_id': img.get('id'),
                        'crop_classifications': crop_classifications
                    })
                else:
                    detected_objects.append({
                        'pano_id': img.get('id'),
                        'pano_path': pano_path,
                        'object_detection': 'Pano image not found.'
                    })
            else:
                detected_objects.append({
                    'pano_id': img.get('id'),
                    'pano_path': img.get('pano_path'),
                    'object_detection': 'Pano not downloaded.'
                })
        panos_combined_result = {
            'pano_result': pano_result,
            'detected_objects': detected_objects,
            'classify_results': classify_results
        }
        result = {
            'landcover': {k: str(v) for k, v in landcover_outputs.items()},
            'vegetation': veg_result,
            'panos': panos_combined_result
        }
        # Save result to out/landcover_vegetation_and_panos_result.json
        out_dir = os.path.join(os.path.dirname(__file__), 'out')
        os.makedirs(out_dir, exist_ok=True)
        result_path = os.path.join(out_dir, 'landcover_vegetation_and_panos_result.json')
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e), 'trace': traceback.format_exc()})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
