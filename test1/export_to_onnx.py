import os
import sys
import shutil
from pathlib import Path

# 将自定义的 ultralytics 路径加入到 sys.path，保证兼容已有自定义网络结构（如：mbv3, eca等）
REPO_ROOT = Path(r"D:\cyd\Desktop\yolo_web-main")
CUSTOM_UL_ROOT = REPO_ROOT / "training" / "ultralytics_custom"
if str(CUSTOM_UL_ROOT) not in sys.path:
    sys.path.insert(0, str(CUSTOM_UL_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# 导入 YOLO
from ultralytics import YOLO

def main():
    # 打印提示并获取用户输入
    model_path_str = input("请输入模型路径：").strip()
    
    if not model_path_str:
        print("[错误] 模型路径不能为空")
        return
        
    # 去除可能包含的头尾引号
    if model_path_str.startswith('"') and model_path_str.endswith('"'):
        model_path_str = model_path_str[1:-1]
    if model_path_str.startswith("'") and model_path_str.endswith("'"):
        model_path_str = model_path_str[1:-1]
        
    model_path = Path(model_path_str)
    if not model_path.exists():
        print(f"[错误] 找不到该模型文件：{model_path}")
        return
        
    # 定义输出目录
    output_dir = Path(r"D:\cyd\Desktop\yolo_web-main\test1\results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"[*] 正在加载模型: {model_path} ...")
        model = YOLO(str(model_path))
        
        print("[*] 正在导出为 ONNX 格式...")
        # 导出为 onnx，会自动保存在原始 pt 文件的同级目录下
        exported_path = model.export(format="onnx")
        
        if exported_path and Path(exported_path).exists():
            dest_path = output_dir / Path(exported_path).name
            
            # 如果目标路径已有同名文件，先删除防止移动报错
            if dest_path.exists():
                dest_path.unlink()
                
            print(f"[*] 移动导出的文件从 {exported_path} 到 {dest_path} ...")
            shutil.move(str(exported_path), str(dest_path))
            print(f"==============\n[成功] 导出成功！ONNX 文件已保存在:\n{dest_path}\n==============")
        else:
            print("[错误] 导出失败，未能找到生成的ONNX文件。")
            
    except Exception as e:
        print(f"[错误] 导出过程中发生异常: {e}")

if __name__ == "__main__":
    main()
