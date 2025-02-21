import tenseal as ts #需要import
import time
from PIL import Image
import numpy as np
import math
#import server

def create_ctx():
    # Setup TenSEAL context
    ctx = ts.context(
                ts.SCHEME_TYPE.CKKS,
                poly_modulus_degree = 8192,
                coeff_mod_bit_sizes = [60, 40, 40, 60], #60, 40, 40, 60 #40, 20, 40
                encryption_type = ts.ENCRYPTION_TYPE.ASYMMETRIC
            )
    ctx.global_scale = 2**40 #2**40
    ctx.generate_galois_keys()
    ctx.generate_relin_keys()
    return ctx

def file_to_binary(file_path):
    with open(file_path, 'rb') as file:
        binary_data = file.read()
        binary_string = ''.join(format(byte, '08b') for byte in binary_data)    #010101形式
        # 每8位一组转换为数字
        num_list = []
        for i in range(0, len(binary_string), 8):
            num = int(binary_string[i:i+8], 2)
            num_list.append(num)
        binary_groups = [list(map(int, num_list[i:i+4096])) for i in range(0, len(num_list), 4096)]
        return binary_groups

def context_save(context):
    context = context.serialize(save_public_key=True, save_secret_key=True, save_galois_keys=False, save_relin_keys=False)
    client_query = {
        "context_secret" : context     #金鑰檔案最大
    }#創一個dict
    return client_query

def data_to_txt(binary_groups, file_path):
    client_query = {
        "data" : binary_groups,
    }#創一個dict
    with open(file_path, "w") as f:
       f.write(str(client_query))

def image_to_grouped_pixel_values(image_path, group_size):
    # 打开图像  (轉換為灰度.convert('L'))
    image = Image.open(image_path)
    # 将图像转换为数值矩阵
    image_array = np.array(image)
    # 将图像的灰度像素值存储到一个列表中
    pixel_values = image_array.flatten().tolist()
    # 将像素值列表每 group_size 个值分组成子列表
    grouped_pixel_values = [pixel_values[i:i+group_size] for i in range(0, len(pixel_values), group_size)]
    image_len = len(grouped_pixel_values)

    return grouped_pixel_values, image_len

def encrypte_data(data_len, server_context, binary_groups): #server_context裡面已經沒有密鑰 被刪掉了
    enc_x_list = []
    for i in range(data_len):
        enc_x = ts.ckks_vector(server_context, binary_groups[i])#
        enc_x = enc_x.serialize()
        enc_x_list.append(enc_x)
    server_context = {
        "server_context" : server_context.serialize(),     #金鑰檔案最大
    }
    client_query = {
        "data_len" : data_len,
        "data" : enc_x_list,
    }#創一個dict
    
    return server_context, client_query

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s" % (s)

def encrypte_data_to_txt(client_query,file_path):
    with open(file_path, "w") as f:
       f.write(str(client_query)) 
#=================Client端===================================
if __name__ == '__main__':
    # 紀錄起始時間
    start_time = time.time()
    # CKKS context generation.
    context = create_ctx()
    # 记录第一个部分结束时间
    part1_end_time = time.time()
    sk = context.secret_key()
    context_secret=context_save(context)
    #encrypte_data_to_txt(context_secret,r'test_1_密鑰.txt')#寫入
    context.make_context_public()#刪除密鑰
    print("Is the context private?", ("Yes" if context.is_private() else "No"))
    print("Is the context public?", ("Yes" if context.is_public() else "No"))

    binary_groups_1 = file_to_binary(r'test_1.pdf')
    data_len = len(binary_groups_1)
    #print(type(binary_groups_1))
    #print(data_len)
    server_context, client_query = encrypte_data(data_len, context, binary_groups_1)  #參數 1.沒有密鑰context 2.陣列資料
    #encrypte_data_to_txt(server_context, r'test_1_公鑰.txt')
    #encrypte_data_to_txt(client_query, r'high_encrypte_1.txt')

    #=================圖片序列化=============================
    # image_path = 'Female.tiff' #Female.tiff Couple.tiff
    # grouped_pixel_values, image_len = image_to_grouped_pixel_values(image_path, 4096)   #參數2 多項式最高次方除2 ex.8192/2
    # print(grouped_pixel_values[0][0:15])
    # print(len(grouped_pixel_values[0]), len(grouped_pixel_values[1]))
    # print("總分組數:", image_len)
    # server_context, client_query=encrypte_data(image_len, context, grouped_pixel_values)
    # #encrypte_data_to_txt(server_context, r'test_4_公鑰.txt')
    # #encrypte_data_to_txt(client_query, r'high_encrypte_4.txt')#寫入
    #====================================================

    # 紀錄結束時間
    end_time = time.time()
    # 計算執行時間
    execution_time = end_time - start_time
    # 打印耗时
    print("程式執行時間：", execution_time, "秒")