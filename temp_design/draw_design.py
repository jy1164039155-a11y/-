import os
from PIL import Image, ImageDraw, ImageFont

def draw_design_image1():
    img_path = "d:/评估报告工具/temp_design/image1.jpg"
    out_path = "d:/评估报告工具/temp_design/image1_design.jpg"
    
    if not os.path.exists(img_path):
        print("image1.jpg not found")
        return
        
    with Image.open(img_path) as img:
        # 转换为RGBA以便绘制半透明效果
        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        # 颜色定义
        color_new_canal = (0, 191, 255, 220)   # 亮蓝色 (新修灌渠)
        color_new_drain = (255, 99, 71, 220)   # 亮橙红 (新修排水沟)
        color_arrow = (255, 215, 0, 255)       # 金黄色 (水流方向)
        
        # Line width
        w = 4
        
        # 1. 顶部独立田块设计 (A区)
        # 从右侧现状灌渠引水，沿北侧边界到田块，再沿西侧边界布设灌渠
        # 右侧现状灌渠 x=400 附近。田块北边界 y=85 附近。田块西边界 x=165 附近。
        # 灌渠：(400, 85) -> (210, 85) -> (165, 85) -> (165, 150)
        draw.line([(400, 85), (165, 85), (165, 150)], fill=color_new_canal, width=w)
        # 排水：田块东侧(x=210)直接排入现状排水沟(x=210)，这里画一个排水指示箭头
        # 绘制一个红色排水短线或箭头
        draw.line([(205, 115), (215, 115)], fill=color_new_drain, width=w+2)
        
        # 2. 中部和南部田块群 (B区)
        # 现状排水沟在 x=208 附近。田块群西边界靠着它。
        # 现状灌渠在右侧 x=400 附近，以及底部 y=660 / y=685 附近。
        # 灌渠设计：
        # 从底部蓝色水闸(210, 660)引出新修灌渠，向右连到田块东边界(365, 660)，再沿东边界向上北上到(365, 260)
        draw.line([(210, 660), (365, 660), (365, 260)], fill=color_new_canal, width=w)
        
        # 在中部横向田埂引出二级灌渠
        # 比如 y=430, y=550 处的横向玫红边界
        draw.line([(365, 430), (280, 430)], fill=color_new_canal, width=w)
        draw.line([(365, 550), (260, 550)], fill=color_new_canal, width=w)
        
        # 排水沟设计：
        # 对于东侧部分的田块，需要横向修筑新修排水沟，向西排入现状排水沟(x=208)
        # 比如 y=350, y=490, y=600 处的横向边界
        draw.line([(360, 350), (208, 350)], fill=color_new_drain, width=w)
        draw.line([(360, 490), (208, 490)], fill=color_new_drain, width=w)
        draw.line([(360, 600), (208, 600)], fill=color_new_drain, width=w)
        
        # 绘制图例
        # 在左上角或合适空白处绘制图例背景
        # 图例区域: x: 10 to 180, y: 10 to 100
        legend_bg = Image.new("RGBA", img.size)
        leg_draw = ImageDraw.Draw(legend_bg)
        leg_draw.rectangle([10, 10, 190, 110], fill=(0, 0, 0, 180), outline=(255, 255, 255, 255), width=1)
        img = Image.alpha_composite(img, legend_bg)
        
        # 重新获取draw对象以在合成后的图像上写字和画图例线条
        draw = ImageDraw.Draw(img)
        # 画图例线
        draw.line([(20, 30), (60, 30)], fill=color_new_canal, width=w)
        draw.line([(20, 60), (60, 60)], fill=color_new_drain, width=w)
        draw.line([(20, 90), (60, 90)], fill=color_arrow, width=w)
        
        # 用默认字体写字（如果找不到系统字体，就用默认）
        try:
            font = ImageFont.truetype("msyh.ttc", 12) # 微软雅黑
            font_title = ImageFont.truetype("msyh.ttc", 14)
        except IOError:
            font = ImageFont.load_default()
            font_title = ImageFont.load_default()
            
        draw.text((70, 22), "新修灌渠 (引自现状灌渠)", fill=(255, 255, 255, 255), font=font)
        draw.text((70, 52), "新修排水沟 (排入现状排沟)", fill=(255, 255, 255, 255), font=font)
        draw.text((70, 82), "推荐水流方向 / 进出水口", fill=(255, 255, 255, 255), font=font)
        
        # 标注一些文字说明
        draw.text((220, 630), "分水枢纽", fill=(255, 255, 0, 255), font=font)
        draw.text((120, 160), "A区新修灌渠", fill=(0, 255, 255, 255), font=font)
        draw.text((270, 280), "B区外围主灌渠", fill=(0, 255, 255, 255), font=font)
        
        # 画一些指示水流的箭头（简单用小线段表示）
        # A区灌渠水流向南
        draw.line([(165, 120), (160, 115)], fill=color_arrow, width=2)
        draw.line([(165, 120), (170, 115)], fill=color_arrow, width=2)
        # B区主灌渠水流向北
        draw.line([(365, 350), (360, 355)], fill=color_arrow, width=2)
        draw.line([(365, 350), (370, 355)], fill=color_arrow, width=2)
        
        # 保存为RGB格式图片
        img.convert("RGB").save(out_path, "JPEG", quality=95)
        print(f"Saved: {out_path}")

def draw_design_image2():
    img_path = "d:/评估报告工具/temp_design/image2.jpg"
    out_path = "d:/评估报告工具/temp_design/image2_design.jpg"
    
    if not os.path.exists(img_path):
        print("image2.jpg not found")
        return
        
    with Image.open(img_path) as img:
        img = img.convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        color_new_canal = (0, 191, 255, 220)   # 亮蓝色 (新修灌渠)
        color_new_drain = (255, 99, 71, 220)   # 亮橙红 (新修排水沟)
        color_arrow = (255, 215, 0, 255)       # 金黄色 (水流方向/水口)
        
        w = 4
        
        # image2 坐标分析：
        # 顶部现状灌渠在 y=90 左右，横贯。
        # 左侧现状排水沟在 x=240 左右，纵贯。
        # 中间田块外围：
        # 北侧边界 y=160 左右。
        # 西侧边界 x=248 左右。
        # 纵向田埂1 x=295 左右，纵向田埂2 x=355 左右。
        # 东侧边界在 x=450 (顶部) 到 x=390 (中部) 再折向。
        
        # 设计方案：
        # 1. 沿北侧边界 y=160 修一条新修主灌渠，连接到现状灌渠(y=90)
        # 引水口在 x=295, y=90 处向下引水到 y=160，然后再向东西分流
        draw.line([(295, 90), (295, 160)], fill=color_new_canal, width=w)
        draw.line([(248, 160), (450, 160)], fill=color_new_canal, width=w)
        
        # 2. 纵向田埂1 (x=295) 设为新修灌渠 (灌溉左、中两田块)
        draw.line([(295, 160), (295, 335)], fill=color_new_canal, width=w)
        
        # 3. 东侧外边界 (x=450 -> x=390) 设为新修灌渠 (灌溉右田块)
        # 东侧外边界折线大致为 (450, 160) -> (450, 230) -> (395, 335)
        draw.line([(450, 160), (450, 230), (395, 335)], fill=color_new_canal, width=w)
        
        # 4. 西侧外边界 (x=248) 设为新修排水沟 (左田块排水，向西直排现状排沟)
        # 西侧外边界折线大致为 (248, 160) -> (248, 335)
        draw.line([(248, 160), (248, 335)], fill=color_new_drain, width=w)
        # 绘制排水口连通现状排沟的短线 (248 -> 240)
        draw.line([(248, 250), (238, 250)], fill=color_new_drain, width=w+2)
        
        # 5. 纵向田埂2 (x=355) 设为新修排水沟 (中、右两田块排水)
        # 它从 y=160 到 y=335。由于排水需要汇入现状排沟，
        # 我们让它在南端(y=335)向西折，沿着田块南侧外边界(y=335)横向修筑排水沟，连到西侧的现状排沟(x=240)
        # 折线：(355, 160) -> (355, 335) -> (240, 335)
        draw.line([(355, 160), (355, 335), (240, 335)], fill=color_new_drain, width=w)
        
        # 绘制图例
        legend_bg = Image.new("RGBA", img.size)
        leg_draw = ImageDraw.Draw(legend_bg)
        leg_draw.rectangle([10, 10, 190, 110], fill=(0, 0, 0, 180), outline=(255, 255, 255, 255), width=1)
        img = Image.alpha_composite(img, legend_bg)
        
        draw = ImageDraw.Draw(img)
        draw.line([(20, 30), (60, 30)], fill=color_new_canal, width=w)
        draw.line([(20, 60), (60, 60)], fill=color_new_drain, width=w)
        draw.line([(20, 90), (60, 90)], fill=color_arrow, width=w)
        
        try:
            font = ImageFont.truetype("msyh.ttc", 12)
            font_title = ImageFont.truetype("msyh.ttc", 14)
        except IOError:
            font = ImageFont.load_default()
            font_title = ImageFont.load_default()
            
        draw.text((70, 22), "新修灌渠 (引自北侧灌渠)", fill=(255, 255, 255, 255), font=font)
        draw.text((70, 52), "新修排水沟 (排入西侧排沟)", fill=(255, 255, 255, 255), font=font)
        draw.text((70, 82), "推荐水流方向 / 进出水口", fill=(255, 255, 255, 255), font=font)
        
        # 文字说明
        draw.text((305, 100), "引水渠", fill=(0, 255, 255, 255), font=font)
        draw.text((275, 200), "新修灌渠1", fill=(0, 255, 255, 255), font=font)
        draw.text((410, 220), "新修灌渠2", fill=(0, 255, 255, 255), font=font)
        draw.text((360, 200), "内部新修排沟", fill=(255, 128, 0, 255), font=font)
        draw.text((255, 345), "南部横向汇水排水沟", fill=(255, 128, 0, 255), font=font)
        
        # 画一些水流方向箭头
        # 纵向灌渠水流向南
        draw.line([(295, 220), (290, 215)], fill=color_arrow, width=2)
        draw.line([(295, 220), (300, 215)], fill=color_arrow, width=2)
        # 纵向排水沟水流向南
        draw.line([(355, 220), (350, 225)], fill=color_arrow, width=2)
        draw.line([(355, 220), (360, 225)], fill=color_arrow, width=2)
        # 横向排水沟水流向西
        draw.line([(270, 335), (275, 330)], fill=color_arrow, width=2)
        draw.line([(270, 335), (275, 340)], fill=color_arrow, width=2)
        
        img.convert("RGB").save(out_path, "JPEG", quality=95)
        print(f"Saved: {out_path}")

if __name__ == "__main__":
    draw_design_image1()
    draw_design_image2()
