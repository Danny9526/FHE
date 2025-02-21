import tenseal as ts
import time
import ast
import magic

def txt_to_encrypte_data(file_path):    #讀序列化檔用
    with open(file_path, "r") as f:
     dict_temp = ast.literal_eval(f.read())
    return dict_temp

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

def binary_to_file(output_list, file_path):
    # 还原二进制数据为文件
    binary_data = bytes([byte for group in output_list for byte in group])
    print("2進制前20碼", binary_data[0:20])
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
    elif "xlsx" in file_type.lower():
        file_extension = "xlsx"
    else:
        file_extension = "csv"
        #file_extension = "unknown"
    # 为文件指定正确的扩展名
    file_path_with_extension = f"{file_path}.{file_extension}"
    print("檔名：", file_path_with_extension)
    # 将二进制数据写入文件
    with open(file_path_with_extension, 'wb') as file:
        file.write(binary_data)
    return file_path_with_extension

if __name__ == '__main__':
    # 紀錄起始時間
    start_time = time.time()

    dict_temp=txt_to_encrypte_data(r'test_3_密鑰.txt')#讀出
    context_secret=context_decrypt(dict_temp["context_secret"])
    print("context_secret", context_secret)
    dict_temp_result=txt_to_encrypte_data(r'high_encrypte_3_復原.txt')#讀出
    output_list=decrypte_data(context_secret, dict_temp_result)
    binary_to_file(output_list, 'restored_file')

    #=================圖片反序列化=============================
    # print(len(output_list[0]))
    # # 将 output_list 转换为 aaa x bbb 的数组
    # image_array = np.array(output_list).reshape((256, 256, 3))  #真彩色 x,y,3 灰階 x,y
    # # 将图像数组转换为图像对象
    # reconstructed_image = Image.fromarray(image_array.astype(np.uint8))
    # # 保存还原后的图像
    # reconstructed_image.show()  # 重建圖像
    #reconstructed_image.save('Couple_還原.tiff')
    #========================================================

    # 紀錄結束時間
    end_time = time.time()
    # 計算執行時間
    execution_time = end_time - start_time
    print("程式執行時間：", execution_time, "秒")