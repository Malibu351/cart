import cv2
import numpy as np
from numpy.linalg import norm
import sys
import os
import json
import copy
import matplotlib.pyplot as plt

SZ = 20  # 训练图片长宽
MAX_WIDTH = 1000 # 原始图片最大宽度
Min_Area = 2000  # 车牌区域允许最小面积
PROVINCE_START = 1000

# 读取图片函数
def imreadex(filename):
    return cv2.imdecode(np.fromfile(filename, dtype=np.uint8), cv2.IMREAD_COLOR)
# imdecode将数据转换成可执行的图片格式（imencode功能相反）
# 按照8bit类型读入文件，RGB三色读取

# 坐标点取正函数
def point_limit(point):
    if point[0] < 0:
        point[0] = 0
    if point[1] < 0:
        point[1] = 0
    #将点所有的横纵坐标都变为非负

# 根据设定的阈值和图片直方图，找出波峰，用于分隔字符
def find_waves(threshold, histogram):
    #threshold是一个值，histogram是数组
    up_point = -1  # 上升点(满足波峰条件的左起始点）
    is_peak = False
    if histogram[0] > threshold:
        up_point = 0 #如果第一个点满足条件，认为其为波峰开始点
        is_peak = True
    # 若histogram第一项比阈值大，上升点设置为0，认为是波峰
    wave_peaks = []
    for i, x in enumerate(histogram):
        # enumerate把histogram变为索引序列，可获得索引和值（i是索引，x是值）
        if is_peak and x < threshold:
            #若某点是波峰，且值小于阈值
            if i - up_point > 2:
                is_peak = False #如果一个波峰持续了2以上的长度，就记录
                wave_peaks.append((up_point, i))
        elif not is_peak and x >= threshold:
            #如果不是波峰
            is_peak = True
            up_point = i
    if is_peak and up_point != -1 and i - up_point > 4:
        wave_peaks.append((up_point, i))#最后一个点若满足上条件也记录
    # print(wave_peaks)
    return wave_peaks
    #wave_peaks是波峰的持续段

# 根据找出的波峰，分隔图片，从而得到逐个字符图片
def seperate_card(img, waves):
    part_cards = []
    # cv2.imshow('img',img)
    # cv2.waitKey(0)
    for wave in waves:
        part_cards.append(img[:, wave[0]:wave[1]])
        # cv2.imshow('',img[:, wave[0]:wave[1]])
        # cv2.waitKey(0)
    return part_cards
    #输出逐个字符图片的信息

# 来自opencv的sample，用于svm训练
def deskew(img):
    m = cv2.moments(img)#图像的矩
    if abs(m['mu02']) < 1e-2:
        return img.copy()
    skew = m['mu11'] / m['mu02']
    M = np.float32([[1, skew, -0.5 * SZ * skew], [0, 1, 0]])
    img = cv2.warpAffine(img, M, (SZ, SZ), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR)
    return img

# 来自opencv的sample，用于svm训练
def preprocess_hog(digits):
    samples = []
    for img in digits:
        gx = cv2.Sobel(img, cv2.CV_32F, 1, 0)
        gy = cv2.Sobel(img, cv2.CV_32F, 0, 1)
        mag, ang = cv2.cartToPolar(gx, gy)
        bin_n = 16
        bin = np.int32(bin_n * ang / (2 * np.pi))
        bin_cells = bin[:10, :10], bin[10:, :10], bin[:10, 10:], bin[10:, 10:]
        mag_cells = mag[:10, :10], mag[10:, :10], mag[:10, 10:], mag[10:, 10:]
        hists = [np.bincount(b.ravel(), m.ravel(), bin_n) for b, m in zip(bin_cells, mag_cells)]
        hist = np.hstack(hists)

        eps = 1e-7
        hist /= hist.sum() + eps
        hist = np.sqrt(hist)
        hist /= norm(hist) + eps

        samples.append(hist)
    return np.float32(samples)

# 省份列举
provinces = [
    "zh_cuan", "川",
    "zh_e", "鄂",
    "zh_gan", "赣",
    "zh_gan1", "甘",
    "zh_gui", "贵",
    "zh_gui1", "桂",
    "zh_hei", "黑",
    "zh_hu", "沪",
    "zh_ji", "冀",
    "zh_jin", "津",
    "zh_jing", "京",
    "zh_jl", "吉",
    "zh_liao", "辽",
    "zh_lu", "鲁",
    "zh_meng", "蒙",
    "zh_min", "闽",
    "zh_ning", "宁",
    "zh_qing", "靑",
    "zh_qiong", "琼",
    "zh_shan", "陕",
    "zh_su", "苏",
    "zh_sx", "晋",
    "zh_wan", "皖",
    "zh_xiang", "湘",
    "zh_xin", "新",
    "zh_yu", "豫",
    "zh_yu1", "渝",
    "zh_yue", "粤",
    "zh_yun", "云",
    "zh_zang", "藏",
    "zh_zhe", "浙"
]

class StatModel(object):
    def load(self, fn):
        self.model = self.model.load(fn)

    def save(self, fn):
        self.model.save(fn)


class SVM(StatModel):
    def __init__(self, C=1, gamma=0.5):
        self.model = cv2.ml.SVM_create()
        self.model.setGamma(gamma)
        self.model.setC(C)
        self.model.setKernel(cv2.ml.SVM_RBF)
        self.model.setType(cv2.ml.SVM_C_SVC)

    # 训练svm
    def train(self, samples, responses):
        self.model.train(samples, cv2.ml.ROW_SAMPLE, responses)

    # 字符识别
    def predict(self, samples):
        r = self.model.predict(samples)
        return r[1].ravel()

#车牌识别类
class CardPredictor:
    def __init__(self):
        # 车牌识别的部分参数保存在js中，便于根据图片分辨率做调整
        f = open('config.js')
        j = json.load(f)
        # json.loads()用于将str类型的数据转成dict（字典）
        for c in j["config"]:
            if c["open"]:
                self.cfg = c.copy()
                break
        else:
            raise RuntimeError('没有设置有效配置参数')

    def __del__(self):
        self.save_traindata()

    def train_svm(self):
        # 识别英文字母和数字
        self.model = SVM(C=1, gamma=0.5)
        # 识别中文
        self.modelchinese = SVM(C=1, gamma=0.5)
        if os.path.exists("svm.dat"):
            self.model.load("svm.dat")
        else:
            chars_train = []
            chars_label = []

            for root, dirs, files in os.walk("train\\chars2"):
                if len(os.path.basename(root)) > 1:
                    continue
                root_int = ord(os.path.basename(root))
                for filename in files:
                    filepath = os.path.join(root, filename)
                    digit_img = cv2.imread(filepath)
                    digit_img = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
                    chars_train.append(digit_img)
                    # chars_label.append(1)
                    chars_label.append(root_int)

            chars_train = list(map(deskew, chars_train))
            chars_train = preprocess_hog(chars_train)
            # chars_train = chars_train.reshape(-1, 20, 20).astype(np.float32)
            chars_label = np.array(chars_label)
            print(chars_train.shape)
            self.model.train(chars_train, chars_label)
        if os.path.exists("svmchinese.dat"):
            self.modelchinese.load("svmchinese.dat")
        else:
            chars_train = []
            chars_label = []
            for root, dirs, files in os.walk("train\\charsChinese"):
                if not os.path.basename(root).startswith("zh_"):
                    continue
                pinyin = os.path.basename(root)
                index = provinces.index(pinyin) + PROVINCE_START + 1  # 1是拼音对应的汉字
                for filename in files:
                    filepath = os.path.join(root, filename)
                    digit_img = cv2.imread(filepath)
                    digit_img = cv2.cvtColor(digit_img, cv2.COLOR_BGR2GRAY)
                    chars_train.append(digit_img)
                    # chars_label.append(1)
                    chars_label.append(index)
            chars_train = list(map(deskew, chars_train))
            chars_train = preprocess_hog(chars_train)
            # chars_train = chars_train.reshape(-1, 20, 20).astype(np.float32)
            chars_label = np.array(chars_label)
            print(chars_train.shape)
            self.modelchinese.train(chars_train, chars_label)

    def save_traindata(self):
        if not os.path.exists("svm.dat"):
            self.model.save("svm.dat")
        if not os.path.exists("svmchinese.dat"):
            self.modelchinese.save("svmchinese.dat")

    #根据输入参数缩小矩形范围
    def accurate_place(self, card_img_hsv, limit1, limit2, color):
        row_num, col_num = card_img_hsv.shape[:2]
        xl = col_num
        xr = 0
        yh = 0
        yl = row_num
        # col_num_limit = self.cfg["col_num_limit"]
        row_num_limit = self.cfg["row_num_limit"]
        col_num_limit = col_num * 0.8 if color != "green" else col_num * 0.5  # 绿色有渐变
        for i in range(row_num):
            count = 0
            for j in range(col_num):
                H = card_img_hsv.item(i, j, 0)
                S = card_img_hsv.item(i, j, 1)
                V = card_img_hsv.item(i, j, 2)
                if limit1 < H <= limit2 and 34 < S and 46 < V:
                    count += 1
            if count > col_num_limit:
                if yl > i:
                    yl = i
                if yh < i:
                    yh = i
        for j in range(col_num):
            count = 0
            for i in range(row_num):
                H = card_img_hsv.item(i, j, 0)
                S = card_img_hsv.item(i, j, 1)
                V = card_img_hsv.item(i, j, 2)
                if limit1 < H <= limit2 and 34 < S and 46 < V:
                    count += 1
            if count > row_num - row_num_limit:
                if xl > j:
                    xl = j
                if xr < j:
                    xr = j
        return xl, xr, yh, yl
        #根据热力图中的值进行判断，返回矩阵大小

    def predict(self, car_pic):
        if type(car_pic) == type(""):
            img = imreadex(car_pic)
        else:
            img = car_pic
        pic_hight, pic_width = img.shape[:2]#图片的大小

        if pic_width > MAX_WIDTH:
            resize_rate = MAX_WIDTH / pic_width
            img = cv2.resize(img, (MAX_WIDTH, int(pic_hight * resize_rate)), interpolation=cv2.INTER_AREA)
            #图片过大时进行缩小，采用像素区域关系进行重采样

        blur = self.cfg["blur"]
        # 高斯去噪
        if blur > 0:
            img = cv2.GaussianBlur(img, (blur, blur), 0)  # 通过高斯滤波器，对图片分辨率进行调整
        oldimg = img
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#将图片转换成灰度图像
        # equ = cv2.equalizeHist(img)#进行直方图均衡化,进行增亮
        # plt.hist(equ.ravel(), 256)
        # plt.show()#绘制均衡后的直方图
        # img = np.hstack((img, equ)) #水平方向平铺
        # cv2.imshow('img',img)
        # cv2.waitKey(0)

        # 去掉图像中不会是车牌的区域
        kernel = np.ones((20, 20), np.uint8)
        img_opening = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        #开运算，先腐蚀后膨胀，去除小黑点，平滑较大物体的边界，纤细处分离物体，但是不改变面积
        img_opening = cv2.addWeighted(img, 1, img_opening, -1, 0);
        #叠加，原图和开运算后的图叠加
        # cv2.imshow('',img_opening)
        # cv2.waitKey(0)

        # 找到图像边缘
        ret, img_thresh = cv2.threshold(img_opening, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        #根据阈值将图片变为黑白
        img_edge = cv2.Canny(img_thresh, 100, 200)#图片边缘检测
        # 使用开运算和闭运算让图像边缘成为一个整体
        kernel = np.ones((self.cfg["morphologyr"], self.cfg["morphologyc"]), np.uint8)
        img_edge1 = cv2.morphologyEx(img_edge, cv2.MORPH_CLOSE, kernel)#闭运算排除小黑洞
        img_edge2 = cv2.morphologyEx(img_edge1, cv2.MORPH_OPEN, kernel)
        # cv2.imshow('',img_edge2)
        # cv2.waitKey(0)

        # 查找图像边缘整体形成的矩形区域，可能有很多，车牌就在其中一个矩形区域中
        try:
            contours, hierarchy = cv2.findContours(img_edge2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            #返回轮廓和每个轮廓的属性
            # hierarchy的4个参数分别表示后一个轮廓、前一个轮廓、父轮廓、内嵌轮廓的索引编号
        except ValueError:
            image, contours, hierarchy = cv2.findContours(img_edge2, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(img_edge2, contours, 2, (0, 0, 255), 3)
        # cv2.imshow("img", img_edge2)
        # cv2.waitKey(2000) #←查看轮廓
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > Min_Area]#只取比最小面积大的轮廓

        global lks
        lks=len(contours)
        # print('len(contours)', len(contours))

        # 一一排除不是车牌的矩形区域
        car_contours = []
        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            #根据轮廓求出矩形，并且返回矩形的参数，此时x轴逆时针旋转遇到的第一个边为宽，另一条边为高
            area_width, area_height = rect[1]#返回矩形的长和宽
            if area_width < area_height:
                area_width, area_height = area_height, area_width
            wh_ratio = area_width / area_height
            # print(wh_ratio)
            # 要求矩形区域长宽比在2到5.5之间，2到5.5是车牌的长宽比，其余的矩形排除
            if wh_ratio > 2 and wh_ratio < 5.5:
                car_contours.append(rect)
                box = cv2.boxPoints(rect)#获取矩阵四个顶点的坐标
                box = np.int0(box)#就是np.int64，把数据类型转化为int

                # picshow=copy.deepcopy(oldimg)
                # picshow = cv2.drawContours(picshow, [box], 0, (0, 0, 255), 2)
                # cv2.imshow("edge4", picshow)
                # cv2.waitKey(0)

        # print(rect)
        global cpjx
        cpjx=len(car_contours)

        card_imgs = []
        # 矩形区域可能是倾斜的矩形，需要矫正，以便使用颜色定位
        for rect in car_contours:
            #rect[2]是矩阵的旋转角度,用的角度制°
            if rect[2] > -5 and rect[2] < 5:
                global isHor
                isHor = True
            if rect[2] > -1 and rect[2] < 1:  # 创造角度，使得左、高、右、低拿到正确的值
                angle = 1
            else:
                angle = rect[2]
            #rect = (rect[0], (rect[1][0] + 5, rect[1][1] + 5), angle)
            #加5会导致车牌边缘的白框算入，影响左右两字符的判断
            #print(rect[1])
            rect = (rect[0], (rect[1][0] +2, rect[1][1] +3), angle) #可调节
            # 扩大矩形的范围，避免车牌边缘被排除

            box = cv2.boxPoints(rect)
            heigth_point = right_point = [0, 0]
            left_point = low_point = [pic_width, pic_hight]
            #图片坐标是右上角(0,0)，往右往下取正

            #遍历四个点，分别给矩阵四角的点起名（左 高 右 低）
            for point in box:
                # print(point)
                if left_point[0] > point[0]:
                    left_point = point
                if low_point[1] > point[1]:
                    low_point = point
                if heigth_point[1] < point[1]:
                    heigth_point = point
                if right_point[0] < point[0]:
                    right_point = point

            if left_point[1] <= right_point[1]:  # 正角度
                new_right_point = [right_point[0], heigth_point[1]]
                pts2 = np.float32([left_point, heigth_point, new_right_point])  # 字符只是高度需要改变
                pts1 = np.float32([left_point, heigth_point, right_point])
                M = cv2.getAffineTransform(pts1, pts2)
                #根据三个点求出仿射变换矩阵M
                dst = cv2.warpAffine(oldimg, M, (pic_width, pic_hight))
                #对原图中的矩形进行仿射变换得到水平的矩阵
                point_limit(new_right_point)
                point_limit(heigth_point)
                point_limit(left_point)
                card_img = dst[int(left_point[1]):int(heigth_point[1]), int(left_point[0]):int(new_right_point[0])]
                card_imgs.append(card_img)
                # cv2.imshow("card", card_img)
                # cv2.waitKey(3000)
            elif left_point[1] > right_point[1]:  # 负角度

                new_left_point = [left_point[0], heigth_point[1]]
                pts2 = np.float32([new_left_point, heigth_point, right_point])  # 字符只是高度需要改变
                pts1 = np.float32([left_point, heigth_point, right_point])
                M = cv2.getAffineTransform(pts1, pts2)
                dst = cv2.warpAffine(oldimg, M, (pic_width, pic_hight))
                point_limit(right_point)
                point_limit(heigth_point)
                point_limit(new_left_point)
                card_img = dst[int(right_point[1]):int(heigth_point[1]), int(new_left_point[0]):int(right_point[0])]
                card_imgs.append(card_img)
                # cv2.imshow("card", card_img)
                # cv2.waitKey(3000)

        # 开始使用颜色定位，排除不是车牌的矩形，目前只识别蓝、绿、黄车牌
        colors = []
        for card_index, card_img in enumerate(card_imgs):
            green = yello = blue = black = white = 0
            card_img_hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
            #图转换为RGB以及H色彩S饱和度V亮度

            # 有转换失败的可能，原因来自于上面矫正矩形出错
            if card_img_hsv is None:
                continue
            row_num, col_num = card_img_hsv.shape[:2]
            card_img_count = row_num * col_num
            #card_img_count像素

            for i in range(row_num):
                for j in range(col_num):
                    H = card_img_hsv.item(i, j, 0)
                    S = card_img_hsv.item(i, j, 1)
                    V = card_img_hsv.item(i, j, 2)
                    if 11 < H <= 34 and S > 34:  # 图片分辨率调整
                        yello += 1
                    elif 35 < H <= 99 and S > 34:  # 图片分辨率调整
                        green += 1
                    elif 99 < H <= 124 and S > 34:  # 图片分辨率调整
                        blue += 1

                    if 0 < H < 180 and 0 < S < 255 and 0 < V < 46:
                        black += 1
                    elif 0 < H < 180 and 0 < S < 43 and 221 < V < 225:
                        white += 1
                    #根据每一个像素点的色彩信息，判断颜色

            color = "no"#先将颜色认定为 无
            col='未入库或非车牌颜色'

            limit1 = limit2 = 0
            if yello * 2 >= card_img_count:
                color = "yello"
                col='黄色'
                limit1 = 11
                limit2 = 34  # 有的图片有色偏，偏绿
            elif green * 2 >= card_img_count:
                color = "green"
                col='绿色'
                limit1 = 35
                limit2 = 99
            elif blue * 2 >= card_img_count:
                color = "blue"
                col = '蓝色'
                limit1 = 100
                limit2 = 124  # 有的图片有色偏，偏紫
            elif black + white >= card_img_count * 0.7:  # TODO
                color = "bw"
                col = '黑白'
            # print(color)
            colors.append(color)

            global colmore
            colmore.append([col,blue, green, yello, black, white, card_img_count])

            # print(blue, green, yello, black, white, card_img_count)
            # cv2.imshow("color", card_img)
            # cv2.waitKey(0)
            if limit1 == 0:
                continue
            # 以上为确定车牌颜色
            # 以下为根据车牌颜色再定位，缩小边缘非车牌边界
            # cv2.imshow('',card_img_hsv)
            # cv2.waitKey(3000)
            xl, xr, yh, yl = self.accurate_place(card_img_hsv, limit1, limit2, color)
            if yl == yh and xl == xr:
                continue
            need_accurate = False
            if yl >= yh:
                yl = 0
                yh = row_num
                need_accurate = True
            if xl >= xr:
                xl = 0
                xr = col_num
                need_accurate = True
            card_imgs[card_index] = card_img[yl:yh, xl:xr] if color != "green" or yl < (yh - yl) // 4 else card_img[
                                                                                                           yl - (
                                                                                                                       yh - yl) // 4:yh,
                                                                                                           xl:xr]

            if need_accurate:  # 可能x或y方向未缩小，需要再试一次
                card_img = card_imgs[card_index]
                card_img_hsv = cv2.cvtColor(card_img, cv2.COLOR_BGR2HSV)
                xl, xr, yh, yl = self.accurate_place(card_img_hsv, limit1, limit2, color)
                if yl == yh and xl == xr:
                    continue
                if yl >= yh:
                    yl = 0
                    yh = row_num
                if xl >= xr:
                    xl = 0
                    xr = col_num
            card_imgs[card_index] = card_img[yl:yh, xl:xr] if color != "green" or yl < (yh - yl) // 4 else card_img[
                                                                                                           yl - (
                                                                                                                       yh - yl) // 4:yh,
                                                                                                           xl:xr]
            # cv2.imshow('',card_img_hsv)
            # cv2.waitKey(3000)
        # 以上为车牌定位
        # 以下为识别车牌中的字符
        predict_result = []
        roi = None
        card_color = None
        for i, color in enumerate(colors):
            if color in ("blue", "yello", "green"):
                card_img = card_imgs[i]
                gray_img = cv2.cvtColor(card_img, cv2.COLOR_BGR2GRAY)
                # 黄、绿车牌字符比背景暗、与蓝车牌刚好相反，所以黄、绿车牌需要反向
                if color == "green" or color == "yello":
                    gray_img = cv2.bitwise_not(gray_img)
                ret, gray_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                # 查找水平直方图波峰
                x_histogram = np.sum(gray_img, axis=1)
                x_min = np.min(x_histogram)
                x_average = np.sum(x_histogram) / x_histogram.shape[0]
                x_threshold = (x_min + x_average) / 2
                #寻找波峰
                wave_peaks = find_waves(x_threshold, x_histogram)
                # print(wave_peaks)
                # print(len(wave_peaks))
                global errorwrong
                if len(wave_peaks) == 0:
                    print("peak less 0:")
                    errorwrong+=1
                    continue
                # 认为水平方向，最大的波峰为车牌区域
                wave = max(wave_peaks, key=lambda x: x[1] - x[0])

                #调整一下波峰范围，使得倾斜的矩形拥有完整汉字
                if isHor:
                    wave=list(wave)
                    wave[1]=wave[1]+5 if wave[1]+5<=area_width else area_width #可调节
                    wave[0]=wave[0]-3 if wave[0]-3>=0 else 0
                    wave=tuple(wave)

                gray_img = gray_img[wave[0]:wave[1]]
                cv2.imshow('',gray_img)
                # 查找垂直直方图波峰
                row_num, col_num = gray_img.shape[:2]
                # 去掉车牌上下边缘1个像素，避免白边影响阈值判断
                gray_img = gray_img[1:row_num - 1]
                y_histogram = np.sum(gray_img, axis=0)
                y_min = np.min(y_histogram)
                y_average = np.sum(y_histogram) / y_histogram.shape[0]
                y_threshold = (y_min + y_average) / 5  # U和0要求阈值偏小，否则U和0会被分成两半

                wave_peaks = find_waves(y_threshold, y_histogram)

                # print(wave_peaks)
                # print(len(wave_peaks))

                # for wave in wave_peaks:
                #	cv2.line(card_img, pt1=(wave[0], 5), pt2=(wave[1], 5), color=(0, 0, 255), thickness=2)
                # 车牌字符数应大于6
                if len(wave_peaks) <= 6:
                    print("peak less 1:", len(wave_peaks))
                    errorwrong += 1
                    continue

                wave = max(wave_peaks, key=lambda x: x[1] - x[0])
                max_wave_dis = wave[1] - wave[0]
                # 判断是否是左侧车牌边缘
                if wave_peaks[0][1] - wave_peaks[0][0] < max_wave_dis / 3 and wave_peaks[0][0] == 0:
                    wave_peaks.pop(0)

                # 组合分离汉字
                cur_dis = 0
                for i, wave in enumerate(wave_peaks):
                    if wave[1] - wave[0] + cur_dis > max_wave_dis * 0.6:
                        break
                    else:
                        cur_dis += wave[1] - wave[0]
                if i > 0:
                    wave = (wave_peaks[0][0], wave_peaks[i][1])
                    wave_peaks = wave_peaks[i + 1:]
                    wave_peaks.insert(0, wave)

                # 去除车牌上的分隔点
                point = wave_peaks[2]
                if point[1] - point[0] < max_wave_dis / 3:
                    point_img = gray_img[:, point[0]:point[1]]
                    if np.mean(point_img) < 255 / 5:
                        wave_peaks.pop(2)

                if len(wave_peaks) <= 6:
                    print("peak less 2:", len(wave_peaks))
                    errorwrong += 1
                    continue
                # cv2.imshow('',gray_img)
                # cv2.waitKey(3000)
                part_cards = seperate_card(gray_img, wave_peaks)
                for i, part_card in enumerate(part_cards):
                    # 可能是固定车牌的铆钉
                    # cv2.imshow('',part_card)
                    # cv2.waitKey(3000)
                    if np.mean(part_card) < 255 / 5:
                        print("a point")
                        continue
                    part_card_old = part_card
                    w = abs(part_card.shape[1] - SZ) // 2

                    part_card = cv2.copyMakeBorder(part_card, 0, 0, w, w, cv2.BORDER_CONSTANT, value=[0, 0, 0])
                    part_card = cv2.resize(part_card, (SZ, SZ), interpolation=cv2.INTER_AREA)

                    # part_card = deskew(part_card)
                    part_card = preprocess_hog([part_card])
                    if i == 0:
                        resp = self.modelchinese.predict(part_card)
                        charactor = provinces[int(resp[0]) - PROVINCE_START]
                    else:
                        resp = self.model.predict(part_card)
                        charactor = chr(resp[0])
                    # 判断最后一个数是否是车牌边缘，假设车牌边缘被认为是1
                    if charactor == "1" and i == len(part_cards) - 1:
                        if part_card_old.shape[0] / part_card_old.shape[1] >= 7:  # 1太细，认为是边缘
                            continue
                    predict_result.append(charactor)
                roi = card_img
                card_color = color
                break
        return predict_result, roi, card_color  # 识别到的字符、定位的车牌图像、车牌颜色

def getPhotoname(file_trance):
    for root,dirs,files in os.walk(file_trance):
        files=[f for f in files if not f[0]=='.']
        #删去隐藏文件
        return files
#返回文件夹内非文件夹的文件名

errorwrong=0#载入但是波峰不匹配
lks=''#识别轮廓数
cpjx=''#可能是车牌的矩形
colmore=[]#矩阵内颜色统计
isHor=False#判断车牌是否水平
if __name__ == '__main__':
    correct=[]
    c = CardPredictor()
    c.train_svm()
    #有3个文件夹包含图片sample是用于报告示范图片，cars是筛选出的正确识别的图片
    #netcars是从网络上寻找的训练集以及自己拍摄的一些照片（也包含老师给的图片）
    photoname=getPhotoname('cars')
    # print(photoname)
    totalnum=0#图片总数
    correctnum=0#正确识别
    errorload=0#无法载入
    errornotmatch=0#识别错误
    dic={'blue':'蓝色','yello':'黄色','green':'绿色','bw':'黑白','None':'未识别或车牌颜色不在库中'}
    for i in photoname:
        totalnum+=1
        # r, roi, color = c.predict(r'./netcars/' + i)
        try:
            print('-----------------\n',i)
            r, roi, color = c.predict(r'./cars/'+i)
            cart = ''
            for j, item in enumerate(r):
                if j == 2:
                    cart = cart + '·'
                cart = cart + item

            if cart[0:2] + cart[3:] == i[0:7]:
                correctnum += 1
                correct.append(i)
            else:
                errornotmatch+=1

            print("【车牌号】:", cart)
            print('【车牌颜色】：', dic.get(color, "None"))
            print('识别过程：')
            print('【识别轮廓数】：', lks)
            print('【可能是车牌的矩形数】：', cpjx)
            print('【矩阵内颜色信息】\n信息依次为 蓝 绿 黄 黑 白 像素大小')
            for l, item in enumerate(colmore):
                print('[矩阵', l + 1, ']:', item[0], item[1:])
            colmore=[]
        except:
            errorload+=1

    print('\n\n====识别结束====')
    print('共有',totalnum,'张图片')
    print(totalnum-errorload-errorwrong,'张合适图片中','有',correctnum,
          '张识别正确','  ',format(correctnum/(totalnum-errorload-errorwrong),'.2%'))
    print('有',errorwrong,'张图片波峰有误')
    print('有',errornotmatch,'张图片识别错误')
    print('有',errorload,'张图片无法读取')