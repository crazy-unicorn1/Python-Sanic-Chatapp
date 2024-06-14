# -*- coding: utf8 -*-
import time
import qrcode
from PIL import Image


class QrcodeApiCLS(object):

    def qrcode_gen(self, code_data, save_name, version=1, box_size=10, border=4):
        """
        :param version: 值为1~40的整数，控制二维码的大小（最小值是1，是个12×12的矩阵）。 如果想让程序自动确定，将值设置为 None 并使用 fit 参数即可。
        :param box_size: 控制二维码中每个小格子包含的像素数。
        :param border: 控制边框（二维码与图片边界的距离）包含的格子数（默认为4，是相关标准规定的最小值）
        :param code_data: 生成二维码的内容
        :param save_name: 生成二维码后的文件名
        error_correction: 控制纠错水平，范围是ERROR_CORRECT_L (L、M、Q、H)，从左到右依次升高
        """
        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        try:
            qr.add_data(code_data)
            qr.make()
            img = qr.make_image()
            # img.save(save_name)
            img.show()
        except Exception as e:
            print(e)

    def tool_detail_view_post(self):
        pass

