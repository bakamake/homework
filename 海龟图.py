import turtle as t

t.title('自动轨迹绘制')
t.setup(800, 600, 0, 0)
t.pencolor("red")
t.pensize(5)
# 重要：如果你txt里是255这种整数颜色，必须加这句，否则画第一笔就报错
t.colormode(255) 

# --- 优化后的数据读取 ---
datals = []
try:
    with open("data.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for index, line in enumerate(lines):
        line = line.strip() # 去除换行符和首尾空格
        
        # 如果是空行，直接跳过
        if not line:
            continue
            
        try:
            # 这里的逻辑是：分割 -> 转数值 -> 存入列表
            # 过滤掉分割后可能产生的空字符（防止如 "1,2,3," 这种情况）
            parts = [x for x in line.split(",") if x.strip() != '']
            row_data = list(map(eval, parts))
            datals.append(row_data)
        except Exception as e:
            print(f"第 {index+1} 行数据格式有误，已跳过: {line}")
            print(f"错误原因: {e}")

except FileNotFoundError:
    print("错误：找不到 data.txt 文件")

# 打印一下读到的数据，确认是否正确
print(f"成功读取 {len(datals)} 行数据")
# print(datals) # 如果需要可以把这行注释打开看看具体数据

# --- 自动绘制 ---
for i in range(len(datals)):
    # 支持6个值
    if len(datals[i]) < 6:
        print(f"第 {i+1} 条指令数据不足6个，跳过")
        continue

    # 这里注意：如果你的txt里颜色是小数(0.5)，上面不要开colormode(255)
    # 如果是整数(255)，必须开
    t.pencolor(datals[i][3], datals[i][4], datals[i][5])
    t.fd(datals[i][0])
    if datals[i][1]:
        t.right(datals[i][2])
    else:
        t.left(datals[i][2])

t.done()
exit()

# 顺序	对应代码索引	参数含义	逻辑说明
# 第1个	datals[i][0]	前进距离	画笔向前移动的像素值（例如 100）。
# 第2个	datals[i][1]	转向判断   0 代表左转 (Left)     1 代表右转 (Right)       (注：其实非0值都会被视为右转，但通常用1)
# 第3个	datals[i][2]	转向角度  转弯的角度度数（例如 90 代表直角）。
# 第4个	datals[i][3]	红色 (R)	颜色的红色通道值。
# 第5个	datals[i][4]	绿色 (G)	颜色的绿色通道值。
# 第6个	datals[i][5]	蓝色 (B)	颜色的蓝色通道值。