# -*- coding: UTF-8 -*- #
'''
@filename : SDGSAT_TIS_processing.py
@author: Zha Fukang
@time : 2024-08-01
'''
import math
import os
import re
import numpy as np
from osgeo import gdal, gdalconst
import xml.etree.ElementTree as ET

# 获取定标文件中的定标参数
def Get_QualifyValue_And_Calibration(xml_file_path):
    # 解析xml文件
    with open(xml_file_path, 'r', encoding='gbk') as file:
        tree = ET.ElementTree(ET.fromstring(file.read()))
    # 获取XML文件的根元素
    root = tree.getroot()

    # QualifyValue参数位于根元素的第18个子元素的第14个子元素下的前四个子元素
    RADIANCE_GAIN_BAND_1 = float(root[0][2][3][0].text)
    RADIANCE_BIAS_BAND_1 = float(root[0][2][3][1].text)
    RADIANCE_GAIN_BAND_2 = float(root[0][2][3][2].text)
    RADIANCE_BIAS_BAND_2 = float(root[0][2][3][3].text)
    RADIANCE_GAIN_BAND_3 = float(root[0][2][3][4].text)
    RADIANCE_BIAS_BAND_3 = float(root[0][2][3][5].text)

    # 将字符串转换为浮点数列表
    numbers_str = root[0][2][1].text
    bandcenter_list = [float(num) for num in numbers_str.split(',')]

    # 将不同极化方式的QualifyValue存储到列表中
    RADIANCEValue = [RADIANCE_GAIN_BAND_1, RADIANCE_BIAS_BAND_1, RADIANCE_GAIN_BAND_2, RADIANCE_BIAS_BAND_2, RADIANCE_GAIN_BAND_3, RADIANCE_BIAS_BAND_3]

    return RADIANCEValue, bandcenter_list

# 辐射定标
def calculate_radiance(dn, band):
    RADIANCEValue, bandcenter_list = Get_QualifyValue_And_Calibration(calib_file)
    if band == 1:
        rad_band1 = dn * RADIANCEValue[0] + RADIANCEValue[1]
        return rad_band1
    elif band == 2:
        rad_band2 = dn * RADIANCEValue[2] + RADIANCEValue[3]
        return rad_band2
    elif band == 3:
        rad_band3 = dn * RADIANCEValue[4] + RADIANCEValue[5]
        return rad_band3
    else:
        raise ValueError("Invalid band number")

# 辐射亮度转亮度温度
def radiance_to_temperature(band, rad):
    h = 6.626e-34
    c = 2.9979e8
    k = 1.3806e-23
    lambda_B1 = 9.35
    lambda_B2 = 10.73
    lambda_B3 = 11.72
    if band == 1:
        tem_band1 = (((h*c*1e6)/(k*lambda_B1))/(np.log((h*c**2*2e24)/(rad*lambda_B1**5)+1)))-273.15
        return tem_band1
    elif band == 2:
        tem_band2 = (((h*c*1e6)/(k*lambda_B2))/(np.log((h*c**2*2e24)/(rad*lambda_B2**5)+1)))-273.15
        return tem_band2
    elif band == 3:
        tem_band3 = (((h*c*1e6)/(k*lambda_B3))/(np.log((h*c**2*2e24)/(rad*lambda_B3**5)+1)))-273.15
        return tem_band3
    else:
        raise ValueError("Invalid band number")

# 结果输出
def process_bands(dataset, num_bands, path, folder, projection, geoTransform):
    for i in range(1, num_bands+1):
        # 读取波段数据
        radiance_band = calculate_radiance(dataset.GetRasterBand(i).ReadAsArray(), i)
        Temperature_band = radiance_to_temperature(i, radiance_band)
        # 创建输出文件名
        output_filename = path + f'{folder}/{folder}_band{i}.tif'
        print('正在处理：', output_filename)
        # 创建输出文件
        driver = gdal.GetDriverByName('GTiff')
        output_dataset = driver.Create(output_filename, width, height, 1, gdalconst.GDT_Float32)
        # 设置地理信息
        output_dataset.SetProjection(projection)
        output_dataset.SetGeoTransform(geoTransform)
        # 写入辐射亮度数据
        output_dataset.WriteArray(Temperature_band)


# 文件路径
path = "F:/Data/SDGSAT_TIS/"
# 获取目录下的所有文件和文件夹
files_and_folders = os.listdir(path)
folders = [item for item in files_and_folders if os.path.isdir(os.path.join(path, item))]
for folder in folders:
    # 获取影像和定标文件的路径
    tiff_file = path + f'{folder}/{folder}.tiff'
    calib_file = path + f'{folder}/{folder}.calib.xml'

    # 打开需要处理的影像
    dataset = gdal.Open(tiff_file)

    # 获取影像宽度和高度
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    num_bands = dataset.RasterCount
    # 获取投影坐标系，这里调用的是方法，加括号
    projection = dataset.GetProjection()
    # Geotransform是从图像坐标空间（行、列）到地理参考坐标空间（投影或地理坐标）的仿射变换。比如你想求图中一个像素（150行，160列）的坐标，就可以用这个计算
    geoTransform = dataset.GetGeoTransform()
    process_bands(dataset, num_bands, path, folder, projection, geoTransform)

print('已经全部处理完成')
