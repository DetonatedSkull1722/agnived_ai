import requests

response = requests.post('http://localhost:5000/classify', json={
    "lon": 77.303778,
    "lat": 28.560278,
    "buffer_km": 3.0,
    "mask_path": r"E:\6thSem\GLYTCH'25\Veg-class-problem\Final_Res_DW\vegetation_mask.tif"
})

print(response.json())