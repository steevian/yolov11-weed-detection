from ultralytics import YOLO

# 加载你的新模型
model = YOLO("weights/weed_best.pt")
# 测试一张杂草图片
results = model("1.jpg", conf=0.2)
# 打印检测结果
print(results[0].boxes)