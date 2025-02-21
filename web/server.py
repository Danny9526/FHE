import ast
import re
import numpy as np
import random
import time

def txt_to_encrypte_data(file_path):
    with open(file_path, "r") as f:
     dict_temp = ast.literal_eval(f.read())
    return dict_temp

def encrypte_data_to_txt(client_query_enc_x,file_path):
    with open(file_path, "w") as f:
       f.write(str(client_query_enc_x)) 

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

def plot_histogram(numbers, total_gif_binary_string): #畫直方圖並位移值 20bit + 010111010.....
    global secret_message_1, secret_message_2, first_part, second_part
    
    def find_peak_and_plot_histogram(pixels):   #找peak 畫直方圖 
        # 找到峰值、峰值數量 還有 直方圖x軸最大值、將峰值轉2進制
        max_value = np.max(pixels)
        # hist, bins = np.histogram(pixels, max_value+1, [0,max_value+1]) # 需要+1不然邊界會被吞掉
        # max_indices = np.argsort(hist)[-1:]
        # p = max_indices[0]
        # 使用 numpy.unique() 获取每个唯一值及其计数
        unique_values, counts = np.unique(pixels, return_counts=True)
        # 找到计数最多的值
        p = unique_values[np.argmax(counts)]
        count_p = np.max(counts)

        # # 繪製直方圖
        # plt.hist(pixels, bins=bins, edgecolor='black', alpha=0.5, label='pixels')
        # plt.ticklabel_format(style='plain') #讓x軸是實際數字呈現不是k、M、le6
        # plt.title('pdf_2')
        # plt.xlabel('Numbers Value')
        # plt.ylabel('Frequency')
        # plt.bar(bins[p], hist[p], width=1, align='edge', color='none', edgecolor='red')
        # plt.legend()    #圖例
        # plt.show()
        # plt.clf()   #清除當前圖像變為空白

        return p, count_p, max_value
    
    def shift_pixels(pixels, p, shift_value):   #位移直方圖
        # 複製像素值
        shifted_pixels = pixels.copy()
        # 將 p 右邊的像素值向右位移
        right_shift_indices = np.where(shifted_pixels > p)
        shifted_pixels[right_shift_indices] = shifted_pixels[right_shift_indices] + shift_value

        return shifted_pixels
    
    def generate_random_secret_message(pixels, p, binary_p, count):    #產生機密訊息 參數注意 binary_p為峰值二進制
        def change_pixels(pixels, indices, secret_message):    #根據secret_message位移原始直方圖
            # 確認索引位置數量與機密訊息長度相同
            if len(indices) != len(secret_message):
                print("Error: Length mismatch between indices and secret message.")
            else:
                # 將對應的像素值替換為機密訊息的值
                for i, index in enumerate(indices):
                    if secret_message[i] == '1':
                        pixels[index] = p + 1
            return pixels
        if binary_p == "":                      #例外處理 第一層跟第二層要藏的值不同!
            indices = np.where(pixels == p)[0]
            if count < len(total_gif_binary_string):
                secret_message = first_part
                pixels = change_pixels(pixels, indices, secret_message)
            else:
                # 亂數產生機密訊息(peak的值8bits + 生成剩下的bits)
                random_bits = ''.join(str(random.randint(0, 1)) for _ in range(count - len(total_gif_binary_string)))
                # 結合p的二進制表示和亂數bits
                secret_message = total_gif_binary_string + random_bits
                pixels = change_pixels(pixels, indices, secret_message)
        else:
            indices = np.where(pixels == p + 2)[0]
            if count < len(total_gif_binary_string):
                # 亂數產生機密訊息(peak的值8bits + 生成剩下的bits)
                random_bits = ''.join(str(random.randint(0, 1)) for _ in range(count - len(binary_p + second_part)))
                secret_message = binary_p + second_part +random_bits
                pixels = change_pixels(pixels, indices, secret_message)
            else:
                # 亂數產生機密訊息(peak的值8bits + 生成剩下的bits)
                random_bits = ''.join(str(random.randint(0, 1)) for _ in range(count - len(binary_p)))
                # 結合p的二進制表示和亂數bits
                secret_message = binary_p + random_bits
                pixels = change_pixels(pixels, indices, secret_message)
        return pixels, secret_message
    #原始直方圖
    pixels = np.array(numbers)
    p1, count_p1, max_value_1 = find_peak_and_plot_histogram(pixels)    #找出peak 並 畫直方圖
    binary_p1 = "{:08b}".format(p1)
    #count_p1 = np.count_nonzero(pixels == p1)
    #print("原始數字", pixels[:10], "原始長度", len(pixels))
    print("第一層峰值：", p1, "峰值二進位：", binary_p1, "第一層峰值的數量：", count_p1, "第一層x軸最大值", max_value_1)
    #第一層位移的直方圖
    pixels = shift_pixels(pixels, p1, 1)   #位移直方圖 即為數字變動 0 --> 1 1 --> 2
    #shifted_p, shifted_max_value_1 = find_peak_and_plot_histogram(first_shifted_pixels)   #畫直方圖  !!!shifted_p用不到!!!
    #print("第一層右移後數字", first_shifted_pixels[:30], "第一層x軸最大值", shifted_max_value_1)

    # 将字符串分为两部分，一部分长度为count，另一部分为剩余部分
    first_part = total_gif_binary_string[:count_p1]
    second_part = total_gif_binary_string[count_p1:]
    print("第一部分:", len(first_part), "第二部分:", len(second_part), "totla", len(first_part) + len(second_part))
    pixels, secret_message_1 = generate_random_secret_message(pixels, p1, "", count_p1) #參數注意 binary_p為峰值二進制
    #print("產生的 secret_message_1", secret_message_1[0:10])

    #第二層位移的直方圖
    p2, count_p2, max_value_2 = find_peak_and_plot_histogram(pixels)    #找出peak 並 畫直方圖
    #count_p2 = np.count_nonzero(pixels == p2)
    count_p2_right = np.count_nonzero(pixels == p2 + 1)   #紀錄第二層peak右側值的數量(!藏機密訊息用!)
    print("第二層峰值：", p2, "第二層峰值的數量：", count_p2, "第二層x軸最大值", max_value_2)
    pixels = shift_pixels(pixels, p2, 1)   #位移直方圖 即為數字變動 0 --> 1 1 --> 2
    #shifted_p2, shifted_max_value_2 = find_peak_and_plot_histogram(double_shifted_pixels)   #畫直方圖  !!!shifted_p2用不到!!!
    #print("第二層右移後數字", double_shifted_pixels[:30], "第二層x軸最大值", shifted_max_value_2)
    pixels, secret_message_2 = generate_random_secret_message(pixels, p2, binary_p1, count_p2_right)   #機密長度是峰值旁的值不是峰值!
    #print("產生的 secret_message_2", secret_message_2[0:10])    #前8bits是為第一層峰值p 不是第二層峰值p2!
    #print("替換後的數字：", double_shifted_pixels[:50])
    #ind_peak_and_plot_histogram(double_shifted_pixels)   #畫直方圖

    return pixels

def gif_to_binary(gif_filename):
    # 打開GIF文件並讀取二進制數據
    with open(gif_filename, 'rb') as gif_file:
        gif_binary_data = gif_file.read()
    # 將二進制數據轉換為0101二進制模式
    binary_string = ''.join(format(byte, '08b') for byte in gif_binary_data)
    return binary_string

def encrypte_data_to_txt(client_query,file_path):
    with open(file_path, "w") as f:
       f.write(str(client_query)) 

if __name__ == '__main__':
    # 紀錄起始時間
    start_time = time.time()

    dict_temp_1=txt_to_encrypte_data(r'high_encrypte_1.txt')# 讀出 dict_temp["data"][0]=>{"data": [b'\n\x02\xc8\x0e\x12\x81j^\xa1\x10, b'\n\x02\xc8\x0e\x12\xa5\xf6\x0f]}
    # 將字節串以可見的形式打印出來
    string_data = repr(dict_temp_1["data"])
    
    #GIF轉binary
    gif_binary_string = gif_to_binary(r'apple.gif')
    # 將len(gif_binary_string)轉換為25位的01二進制
    gif_bit_len_string = bin(len(gif_binary_string))[2:].zfill(25)
    total_gif_binary_string = gif_bit_len_string + gif_binary_string
    print(gif_binary_string[0:20], "gif長度", len(gif_binary_string), "25bit數字", gif_bit_len_string, "total", len(total_gif_binary_string))


    # 使用正則表達式匹配數字部分
    original_numbers = re.findall(r'\d+', string_data)  # 產生['02', '80', '12', '92', '14', '1', '10', '04', '01', '02']型式
    original_others = re.findall(r'\D+', string_data)  # 產生["[b'\\n\\x", '\\x', ' \\x', '\\xd', '\\xb', '\\x', '^\\xa', '\\x', '\\x', '\\x', '\\x', '\\x', '\\x', 'S\\x', '\\x', "']"]    
    record = count_zeros(original_numbers)    # 統計幾個數字前面有幾個0，dict做紀錄{} 記號※
    # # 使用Counter來計算每個資料的出現次數
    # data_counts = Counter(original_numbers)
    # encrypte_data_to_txt(data_counts, r'str數字統計.txt')
    # 將數字字串轉換為整數形式
    numbers = [int(num) for num in original_numbers]
    #data_counts = Counter(numbers)
    #encrypte_data_to_txt(data_counts, r'直方圖的數字統計.txt')
    new_numbers = plot_histogram(numbers, total_gif_binary_string) # 印出直方圖，並且藏入機密資訊
    str_new_numbers = [str(num) for num in new_numbers]
    # print("資料抓出字串：", original_numbers[0:15])
    # print("字串轉為整數：", numbers[0:30])
    # print("整數轉為字串：", str_new_numbers[0:15],len(str_new_numbers))
    for i, count in record.items():
        str_new_numbers[i] = '0' * count + str_new_numbers[i] #'※'會有問題!
    # print("把零補回列表：",str_new_numbers[0:15],len(str_new_numbers))
    # print("原始的字符串：", string_data[0:100],len(string_data))
    # 拼接回string_data
    str_new_numbers.append("")  # 接回數據時replaced_pixels長度少1，讓它們長度相同才不會少了 "']"
    string_data = ''.join([x + y for x, y in zip(original_others, str_new_numbers)])
    # print("拼接回的字符串", string_data[0:100], len(string_data))
    print("總藏入量為", len(secret_message_1) + len(secret_message_2), "bits")
    # 恢复原始数据
    #dict_temp_1["data"] = eval(string_data) # 將修改過的值恢復成數據
    dict_temp_1["data"] = string_data   #用字串型式儲存
    #dict_temp_1["secret_message"] = secret_message_1 # 比較機密正不正確用
    #dict_temp_1["secret_message_2"] = secret_message_2 # 比較機密正不正確用
    #encrypte_data_to_txt(dict_temp_1, r'藏入機密的序列化檔_3.txt')  # 寫入 遇到/x20會有變空白問題

    # 紀錄結束時間
    end_time = time.time()
    # 計算執行時間
    execution_time = end_time - start_time
    print("程式執行時間：", execution_time, "秒")
    # # 使用 most_common() 函數來取得前 10 個出現次數最高的元素
    # numbers_counter = Counter(numbers)# 列出各個數值的count
    # top_20 = numbers_counter.most_common(20)
    # print(top_20)