import tenseal as ts
import time
import ast
import re
import numpy as np
import magic #一定要這樣打 "pip install python-magic-bin"

def txt_to_encrypte_data(file_path):    #讀序列化檔用
    with open(file_path, "r") as f:
     dict_temp = ast.literal_eval(f.read())
    return dict_temp

def count_zeros(numbers):   # 統計幾個數字前面有幾個0，dict做紀錄{}
    record = {}
    for i, num in enumerate(numbers):
        if num.startswith('0') and num != '0': # 把開頭為0 和 不單純為'0'抓出來
            count = 0
            for char in num:
                if char == '0':
                    count += 1
                else:
                    break
            if count != len(num):   # 長度一樣的代表都是0組成 ex"000"
                record[i] = count
            else:
                record[i] = count - 1
    return record

def plot_histogram(numbers): #畫直方圖並位移值(還原動作)
    global secret_message_1_restoration, secret_message_2_restoration
    def secret_message_restoration(pixels, p, value):   #value根據要處理的位置做調整
        # 機密訊息
        secret_message = ""
        indices = np.where((pixels == p + 1) | (pixels == p + value))[0]
        # 遍歷每個像素值 將峰值旁的值還回原本地方 並將機密訊息取出
        for i,index in enumerate(indices):
            if pixels[index] == p + 1:
                secret_message += "1"
                pixels[index] = p + value
            else:
                secret_message += "0"
        return pixels, secret_message
    
    def shift_pixels(pixels, p, shift_value):   #位移直方圖
        # 複製像素值
        shifted_pixels = pixels.copy()
        # 將 p 右邊的像素值向右位移
        right_shift_indices = np.where(shifted_pixels > p)
        shifted_pixels[right_shift_indices] = shifted_pixels[right_shift_indices] + shift_value

        return shifted_pixels
    
    pixels = np.array(numbers)
    # # 找到峰值、峰值數量 還有 直方圖x軸最大值
    max_value_2 = np.max(pixels)
    # hist, bins = np.histogram(pixels, max_value_2 + 1, [0, max_value_2 + 1]) #從byte轉過來所以0~255
    # max_indices = np.argsort(hist)[-1:]
    # p2 = max_indices[0]
    # count_p2 = np.count_nonzero(pixels == p2)

    # 使用 numpy.unique() 获取每个唯一值及其计数
    unique_values, counts = np.unique(pixels, return_counts=True)
    # 找到计数最多的值
    p2 = unique_values[np.argmax(counts)]
    count_p2 = np.max(counts)
    
    #print("原始數字", pixels)
    print("第二層峰值：", p2, "第二層峰值的數量：", count_p2, "第二層x軸最大值", max_value_2)

    # 複製像素值 進行 "第二層" 還原回 "第一層"
    pixels, secret_message_2_restoration = secret_message_restoration(pixels, p2, 2)    #須注意最後一個參數，根據要還的位置調整
    print("位移後的像素值：(已將機密訊息2取出)", pixels[:15])
    print("第二層的機密訊息", secret_message_2_restoration[0:8])
    # 對 p2 周圍的像素值進行位移 (推回去)
    pixels = shift_pixels(pixels, p2, -1)   #位移直方圖 即為數字變動 0 --> 1 1 --> 2
    print("第二層像素值還原", pixels[0:15])
    # 將峰值p取出 即為前8bits 並將其轉為10進制
    binary_p = secret_message_2_restoration[:8]
    p = int(binary_p, 2)
    print("第一層峰值：", p)

    #第一層的還原
    pixels = pixels.copy()
    pixels, secret_message_1_restoration = secret_message_restoration(pixels, p, 0)    #須注意最後一個參數，根據要還的位置調整
    print("位移後的像素值：(已將機密訊息1取出)", pixels[:15])
    print("第一層的機密訊息", secret_message_1_restoration[0:20])
    # 對 p 周圍的像素值進行位移 (推回去)
    pixels = shift_pixels(pixels, p, -1)   #位移直方圖 即為數字變動 0 --> 1 1 --> 2
    print("第一層像素值還原", pixels[0:15])

    return pixels, secret_message_1_restoration, secret_message_2_restoration

def context_decrypt(context):   #將私鑰反序列化 例如:<tenseal.enc_context.Context object at 0x00000263247D3610>
    context = ts.context_from(context)
    return context

def decrypte_data(context_secret, dict_temp_result):    #將加密的序列化檔，反序列化並解密，得到明文
    output_list=[]
    data_len=dict_temp_result["data_len"]
    for i in range(data_len):
        output=ts.ckks_vector_from(context_secret, dict_temp_result["data"][i]).decrypt()
        output_int = [int(round(x)) for x in output]
        output_list.append(output_int)
    return output_list

def restore_gif_from_binary(numbers_restoration, secret_message_1, secret_message_2, file_path):
    # 使用 numpy.unique() 获取每个唯一值及其计数
    unique_values, counts = np.unique(numbers_restoration, return_counts=True)
    # 找到计数最多的值
    most_common_value = unique_values[np.argmax(counts)]
    count_p1 = np.max(counts)
    # print("peak 1:", most_common_value)
    # print("peak1 Count:", count_p1)
    # 将前25位二进制数据转换为十进制数值
    gif_len_int = int(secret_message_1[:25], 2)
    print("gif_len_int", gif_len_int)
    if gif_len_int + 25 >  count_p1:    #+25是因為前25bit是紀錄整個gif轉成2進制有多大(例如:725944個0或1組成)
        # 获取从第25位后到指定长度的二进制数据
        binary_string = secret_message_1[25:25 + count_p1] + secret_message_2[8:8 + (gif_len_int + 25 - count_p1)]
    else:    
        # 获取从第25位后到指定长度的二进制数据
        binary_string = secret_message_1[25:25 + gif_len_int]
    # 将0101二进制字符串转换回二进制数据
    binary_data = bytes(int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8))

    # 使用python-magic库来识别文件类型
    mime = magic.Magic()
    file_type = mime.from_buffer(binary_data)

    # 根据文件类型确定文件扩展名
    if "pdf" in file_type.lower():
        file_extension = "pdf"
    elif "txt" in file_type.lower():
        file_extension = "txt"
    elif "jpeg" in file_type.lower() or "jpg" in file_type.lower():
        file_extension = "jpg"
    elif "png" in file_type.lower():
        file_extension = "png"
    elif "tiff" in file_type.lower():
        file_extension = "tiff"
    elif "gif" in file_type.lower():
        file_extension = "gif"
    else:
        file_extension = "unknown"

    # 为文件指定正确的扩展名
    file_path_with_extension = f"{file_path}.{file_extension}"
    # 将二进制数据写入新的文件
    with open(file_path_with_extension, 'wb') as file:
        file.write(binary_data)
    return file_path_with_extension

def binary_to_pdf(output_list, file_path):  #轉回2進制並還原成原始PDF
    # 将二进制数据还原为字符串
    binary_string = ''.join(format(num, '08b') for group in output_list for num in group)
    # 将二进制字符串转换回字节数据
    byte_data = bytes(int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8))
    # 将字节数据写入新的 PDF 文件
    with open(file_path, 'wb') as file:
        file.write(byte_data)

def encrypte_data_to_txt(client_query,file_path):
    with open(file_path, "w") as f:
       f.write(str(client_query))

if __name__ == '__main__':
    # 紀錄起始時間
    start_time = time.time()
    # dict_temp=txt_to_encrypte_data(r'pdf_2_密鑰.txt')#讀出
    # context_secret=context_decrypt(dict_temp["context"])
    # print("context_secret", context_secret)
    # dict_temp_result=txt_to_encrypte_data(r'high_encrypte_2.txt')#讀出
    # output_list=decrypte_data(context_secret, dict_temp_result)
    #binary_to_pdf(output_list, 'restored_pdf.pdf')

    #==========================測試區=====================================
    dict_temp_1=txt_to_encrypte_data(r'藏入機密的序列化檔_3.txt')# 讀出 dict_temp["data"][0]=>{"data": [b'\n\x02\xc8\x0e\x12\x81j^\xa1\x10, b'\n\x02\xc8\x0e\x12\xa5\xf6\x0f]}
    print("list長度：",len(dict_temp_1["data"]))
    # 將字節串以可見的形式打印出來
    string_data = str(dict_temp_1["data"])
    # 使用正則表達式匹配數字部分
    original_numbers = re.findall(r'\d+', string_data)  # 產生['02', '80', '12', '92', '14', '1', '10', '04', '01', '02']型式
    original_others = re.findall(r'\D+', string_data)  # 產生["[b'\\n\\x", '\\x', ' \\x', '\\xd', '\\xb', '\\x', '^\\xa', '\\x', '\\x', '\\x', '\\x', '\\x', '\\x', 'S\\x', '\\x', "']"]
    record = count_zeros(original_numbers)    # 統計幾個數字前面有幾個0，dict做紀錄{} 記號※
    # 將數字字串轉換為整數形式
    numbers = [int(num) for num in original_numbers]
    numbers_restoration = plot_histogram(numbers) # 印出直方圖
    str_numbers_restoration = [str(num) for num in numbers_restoration]
    print(str_numbers_restoration[0:15])
    #secret_message = dict_temp_1["secret_message"]
    #secret_message_2 = dict_temp_1["secret_message_2"]
    # 還原後的機密訊息和原本機密訊息比較
    #print("機密訊息：",secret_message)
    # #print("還原後的機密訊息：", secret_message_restoration)
    # if secret_message == secret_message_1_restoration and secret_message_2 == secret_message_2_restoration:
    #     print("兩組機密訊息相同")
    # else:
    #     print("兩組機密訊息不同!!")
    for i, count in record.items():
        str_numbers_restoration[i] = '0' * count + str_numbers_restoration[i] #'※'會有問題!
    print(str_numbers_restoration[0:15])
    # 拼接回string_data
    str_numbers_restoration.append("")  # 接回數據時replaced_pixels長度少1，讓它們長度相同才不會少了 "']"
    string_data = ''.join([x + y for x, y in zip(original_others, str_numbers_restoration)])
    print("拼接回的字符串:", string_data[0:100], len(string_data))
    # 恢复原始数据
    dict_temp_1["data"] = eval(string_data) # 將修改過的值恢復成數據
    # 移除 "replacement_positions" "secret_message" 字段
    #del dict_temp_1["secret_message"]
    #del dict_temp_1["secret_message_2"]
    print("dict_temp_1 中的键：", dict_temp_1.keys())
    #encrypte_data_to_txt(dict_temp_1, r'high_encrypte_3_復原.txt')  # 寫入

    #=====================================================================
    # 紀錄結束時間
    end_time = time.time()
    # 計算執行時間
    execution_time = end_time - start_time
    print("程式執行時間：", execution_time, "秒")