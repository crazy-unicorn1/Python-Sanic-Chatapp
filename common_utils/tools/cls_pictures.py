# -*- coding: utf-8 -*-
import os
from PIL import Image
from PIL import ImageFile


class PicturesCLS:

    @classmethod
    def rgb2hsv(cls, r, g, b):
        """
        RGB=>HSV,范围：0-180,0-255,0-255
        """
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        m = mx-mn
        if mx == mn:
            h = 0
        elif mx == r:
            if g >= b:
                h = ((g-b)/m)*60
            else:
                h = ((g-b)/m)*60 + 360
        elif mx == g:
            h = ((b-r)/m)*60 + 120
        elif mx == b:
            h = ((r-g)/m)*60 + 240
        if mx == 0:
            s = 0
        else:
            s = m/mx
        v = mx
        H = h / 2
        S = s * 255.0
        V = v * 255.0
        return H, S, V

    @classmethod
    def RGB_to_Hex(cls, rgb):
        """RGB格式颜色转换为16进制颜色格式"""
        RGB = rgb.split(',')
        color = '#'
        for i in RGB:
            num = int(i)
            # 将R、G、B分别转化为16进制拼接转换并大写  hex() 函数用于将10进制整数转换成16进制，以字符串形式表示
            color += str(hex(num))[-2:].replace('x', '0').upper()
        return color

    @classmethod
    def Hex_to_RGB(cls,hex):
        """16进制颜色格式颜色转换为RGB格式"""
        r = int(hex[1:3], 16)
        g = int(hex[3:5], 16)
        b = int(hex[5:7], 16)
        rgb = str(r) + ',' + str(g) + ',' + str(b)
        return rgb

    @classmethod
    def get_allRGB(cls):
        """获取所有的RGB颜色"""
        rgb = []
        for i in range(0, 256):
            for j in range(0, 256):
                for c in range(0, 256):
                    rgb.append(str(i) + ',' + str(j) + ',' + str(c))
        return rgb

    @classmethod
    def pic_size(cls, filename, b_width=760):
        """调整尺寸"""
        im = Image.open(filename)
        w, h = im.size
        if w < b_width and w > 500:
            return
        bl = b_width / w
        im_ss = im.resize((int(w * bl), int(h * bl)), Image.Resampling.LANCZOS)
        im_ss.save(filename)

    @classmethod
    def compress_image(cls, outfile, mb=300, quality=85, k=0.5):
        """不改变图片尺寸压缩到指定大小
        :param outfile: 压缩文件保存地址
        :param mb: 压缩目标，KB
        :param k: 每次调整的压缩比率
        :param quality: 初始压缩比率
        :return: 压缩文件地址，压缩文件大小
        """
        o_size = os.path.getsize(outfile) // 1024
        if o_size <= mb:
            return outfile

        ImageFile.LOAD_TRUNCATED_IMAGES = True
        while o_size > mb:
            im = Image.open(outfile)
            x, y = im.size
            out = im.resize((int(x * k), int(y * k)), Image.Resampling.LANCZOS)
            try:
                out.save(outfile, quality=quality)
            except Exception as e:
                print(e)
                break
            o_size = os.path.getsize(outfile) // 1024
        return outfile

    @classmethod
    def resize_images(cls, filein, width, height, fileout='', mtype='jpeg'):
        '''
        filein: 输入图片
        fileout: 输出图片
        width: 输出图片宽度
        height:输出图片高度
        type:输出图片类型（png, gif, jpeg...）
        '''
        img = Image.open(filein)
        new_img = img.resize((width, height), Image.Resampling.LANCZOS)
        if fileout:
            new_img.save(fileout, mtype)
        else:
            new_img.save(filein, mtype)
        return True

