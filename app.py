# screen_recorder.py (Headless Version)
import cv2
import numpy as np
import mss
import time

# ==============================================================================
#                             配置区域
# ==============================================================================
# 输出文件名 (AVI格式)
OUTPUT_FILENAME = "recording_headless.avi"

# 录制的帧率 (FPS)
FPS = 20.0
# ==============================================================================

def main():
    print("无头录屏程序已启动。")
    print(f"输出文件: {OUTPUT_FILENAME}")
    print(f"录制帧率: {FPS}")
    print("\n将在3秒后开始录制... 您可以切换到需要录制的窗口。")
    time.sleep(3)
    print("录制开始！请在此窗口中按下 Ctrl+C 来停止录制。")

    try:
        with mss.mss() as sct:
            # 获取主显示器的尺寸
            monitor = sct.monitors[1]
            width = monitor["width"]
            height = monitor["height"]
            
            # 定义视频编码器并创建VideoWriter对象
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, (width, height))

            while True:
                # 抓取屏幕图像
                img = sct.grab(monitor)
                
                # 将图像转换为OpenCV可以处理的NumPy数组
                frame = np.array(img)
                
                # 转换颜色空间 BGRA -> BGR
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # 将帧写入视频文件
                out.write(frame_bgr)
                
    except KeyboardInterrupt:
        # 允许通过 Ctrl+C 停止
        print("\n检测到键盘中断(Ctrl+C)，正在停止录制...")
    finally:
        # 释放所有资源
        print("正在保存文件...")
        if 'out' in locals() and out.isOpened():
            out.release()
        print(f"录屏已保存为: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    main()