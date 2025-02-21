import shutil
from flask import Flask, request, send_from_directory, render_template #需要import
import os
import server
import server_reduction
import client
import client_decrypte
import re

app = Flask(__name__)
#app.config['SECRET_KEY']='hard to guess string'
# 設定上傳檔案的最大大小為 50 MB
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024
# 設定上傳檔案的路徑與下載檔案的路徑
app.config['UPLOAD_FOLDER'] = r'C:\python\FHE專題\專題(比賽版)\上傳點'   #記得改成自己的路徑
app.config['DOWNLOAD_FOLDER'] = r'C:\python\FHE專題\專題(比賽版)\下載點' #記得改成自己的路徑
ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'tiff'])

# 定义一个清空文件夹的函数
def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"无法删除文件 {file_path}: {e}")

# 在应用程序启动时清空文件夹的数据
upload_folder = app.config['UPLOAD_FOLDER']
download_folder = app.config['DOWNLOAD_FOLDER']
clear_folder(upload_folder)
clear_folder(download_folder)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        #print(request.files)
        # 檢查是否有上傳檔案
        if 'file' not in request.files:
            return render_template('index.html', success_message='請選擇檔案！')
        files = request.files.getlist('file')
        print("files",files)
        # 檢查檔案是否為空
        if files[0].filename == '':
            return render_template('index.html', success_message='檔案不能為空！')
        # 檢查檔案大小
        if files[0].content_length > app.config['MAX_CONTENT_LENGTH']:
                return render_template('index.html', success_message='檔案大小超過限制！')
        # 將檔案存到 C:\ 目錄下
        files[0].save(os.path.join(app.config['UPLOAD_FOLDER'], files[0].filename))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], files[0].filename)
        #-----------------私鑰產生與儲存-------------
        context = client.create_ctx()
        context_secret = client.context_save(context)
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'context_secret.txt')
        client.encrypte_data_to_txt(context_secret, download_file_path)
        context.make_context_public()#刪除密鑰
        #-------------------------------------------

        #-----------------產生序列化檔案-------------
        binary_groups_1 = client.file_to_binary(file_path)
        data_len = len(binary_groups_1)
        server_context, client_query = client.encrypte_data(data_len, context, binary_groups_1)  #參數 1.沒有密鑰context 2.陣列資料
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'encrypte_txt_1.txt')
        client.encrypte_data_to_txt(client_query, download_file_path)
        # 在返回到index.html前触发JavaScript以显示alert，上传成功后，返回一个指示成功上传的消息
        return render_template('index.html', success_message='上傳成功！')
    else:
        return render_template('index.html', success_message='上傳失敗！')

@app.route('/download_secret')
def download_secret():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'context_secret.txt', as_attachment=True) #打包單一檔案
@app.route('/download_txt')
def download_txt():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'encrypte_txt_1.txt', as_attachment=True) #打包單一檔案
@app.route('/download_hiding_txt')
def download_hiding_txt():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'hiding_txt.txt', as_attachment=True) #打包單一檔案
@app.route('/download_secret_data')
def download_secret_data():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True) #打包單一檔案
@app.route('/download_txt_reduction')
def download_txt_reduction():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], 'encrypte_txt_1_re.txt', as_attachment=True) #打包單一檔案
@app.route('/download_file')
def download_file():
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True) #打包單一檔案

@app.route('/hiding', methods=['GET', 'POST'])
def hiding():
    if request.method == 'POST':
        #print(request.files)
        # 檢查是否有上傳檔案
        if 'file' not in request.files:
            return render_template('index.html', success_message='請選擇檔案！')
        files = request.files.getlist('file')
        print("files",files)
        file_path_list = []
        for i, file in enumerate(files):
            # 檢查檔案是否為空
            if file.filename == '':
                return render_template('index.html', success_message='檔案不能為空！')
            # 檢查檔案大小
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                return render_template('index.html', success_message='檔案大小超過限制！')
            # 將檔案存到 C:\ 目錄下
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file_path_list.append(file_path)
        dict_temp_1 = server.txt_to_encrypte_data(file_path_list[0])
        gif_binary_string = server.gif_to_binary(file_path_list[1]) #01101001100110100110型態 有數十萬個0或1
        gif_bit_len_string = bin(len(gif_binary_string))[2:].zfill(25)  #將前面的gif2進制長度(725944)轉成2進制(010111...)並且為25bit
        total_gif_binary_string = gif_bit_len_string + gif_binary_string
        print("gif長度", len(gif_binary_string), "25bit數字", gif_bit_len_string, "total", len(total_gif_binary_string))
        # 將字節串以可見的形式打印出來
        string_data = repr(dict_temp_1["data"])
        # 使用正則表達式匹配數字部分
        original_numbers = re.findall(r'\d+', string_data)  # 產生['02', '80', '12', '92', '14', '1', '10', '04', '01', '02']型式
        original_others = re.findall(r'\D+', string_data)  # 產生["[b'\\n\\x", '\\x', ' \\x', '\\xd', '\\xb', '\\x', '^\\xa', '\\x', '\\x', '\\x', '\\x', '\\x', '\\x', 'S\\x', '\\x', "']"]    
        record = server.count_zeros(original_numbers)    # 統計幾個數字前面有幾個0，dict做紀錄{} 記號※
        # 將數字字串轉換為整數形式
        numbers = [int(num) for num in original_numbers]
        new_numbers = server.plot_histogram(numbers, total_gif_binary_string) # 印出直方圖，並且藏入機密資訊
        str_new_numbers = [str(num) for num in new_numbers]
        for i, count in record.items():
            str_new_numbers[i] = '0' * count + str_new_numbers[i] #'※'會有問題!
        # 拼接回string_data
        str_new_numbers.append("")  # 接回數據時replaced_pixels長度少1，讓它們長度相同才不會少了 "']"
        string_data = ''.join([x + y for x, y in zip(original_others, str_new_numbers)])
        # print("拼接回的字符串", string_data[0:100], len(string_data))
        # 恢复原始数据
        dict_temp_1["data"] = string_data   #用字串型式儲存
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'hiding_txt.txt')
        client.encrypte_data_to_txt(dict_temp_1, download_file_path)
        # 在返回到index.html前触发JavaScript以显示alert，上传成功后，返回一个指示成功上传的消息
        return render_template('index.html', success_message='上傳成功！')
    else:
        return render_template('index.html', success_message='上傳失敗！')

@app.route('/hiding_reduction', methods=['GET', 'POST'])
def hiding_reduction():
    global filename
    if request.method == 'POST':
        #print(request.files)
        # 檢查是否有上傳檔案
        if 'file' not in request.files:
            return render_template('index.html', success_message='請選擇檔案！')
        files = request.files.getlist('file')
        print("files",files)
        # 檢查檔案是否為空
        if files[0].filename == '':
            return render_template('index.html', success_message='檔案不能為空！')
        # 檢查檔案大小
        if files[0].content_length > app.config['MAX_CONTENT_LENGTH']:
                return render_template('index.html', success_message='檔案大小超過限制！')
        # 將檔案存到 C:\ 目錄下
        files[0].save(os.path.join(app.config['UPLOAD_FOLDER'], files[0].filename))
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], files[0].filename)
        dict_temp_1 = server_reduction.txt_to_encrypte_data(file_path)
        string_data = str(dict_temp_1["data"])
        # 使用正則表達式匹配數字部分
        original_numbers = re.findall(r'\d+', string_data)  # 產生['02', '80', '12', '92', '14', '1', '10', '04', '01', '02']型式
        original_others = re.findall(r'\D+', string_data)  # 產生["[b'\\n\\x", '\\x', ' \\x', '\\xd', '\\xb', '\\x', '^\\xa', '\\x', '\\x', '\\x', '\\x', '\\x', '\\x', 'S\\x', '\\x', "']"]
        record = server_reduction.count_zeros(original_numbers)    # 統計幾個數字前面有幾個0，dict做紀錄{} 記號※
        # 將數字字串轉換為整數形式
        numbers = [int(num) for num in original_numbers]
        #------------------Secret data還原-----------------------
        numbers_restoration, secret_message_1_restoration, secret_message_2_restoration = server_reduction.plot_histogram(numbers) # 印出直方圖
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'secret_data')
        file_path_with_extension = server_reduction.restore_gif_from_binary(numbers_restoration, secret_message_1_restoration, secret_message_2_restoration, download_file_path)
        # Extract the filename from the full path
        filename = os.path.basename(file_path_with_extension)
        #------------------------------------------------
        str_numbers_restoration = [str(num) for num in numbers_restoration]
        for i, count in record.items():
            str_numbers_restoration[i] = '0' * count + str_numbers_restoration[i] #'※'會有問題!
        # 拼接回string_data
        str_numbers_restoration.append("")  # 接回數據時replaced_pixels長度少1，讓它們長度相同才不會少了 "']"
        string_data = ''.join([x + y for x, y in zip(original_others, str_numbers_restoration)])
        # 恢复原始数据
        dict_temp_1["data"] = eval(string_data) # 將修改過的值恢復成數據
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'encrypte_txt_1_re.txt')
        client.encrypte_data_to_txt(dict_temp_1, download_file_path)
    # 在返回到index.html前触发JavaScript以显示alert，上传成功后，返回一个指示成功上传的消息
        return render_template('index.html', success_message='上傳成功！')
    else:
        return render_template('index.html', success_message='上傳失敗！')

@app.route('/decrypte', methods=['GET', 'POST'])
def decrypte():
    global filename
    if request.method == 'POST':
        #print(request.files)
        # 檢查是否有上傳檔案
        if 'file' not in request.files:
            return render_template('index.html', success_message='請選擇檔案！')
        files = request.files.getlist('file')
        print("files",files)
        file_path_list = []
        for i, file in enumerate(files):
            # 檢查檔案是否為空
            if file.filename == '':
                return render_template('index.html', success_message='檔案不能為空！')
            # 檢查檔案大小
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                return render_template('index.html', success_message='檔案大小超過限制！')
            # 將檔案存到 C:\ 目錄下
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file_path_list.append(file_path)
        dict_temp=client_decrypte.txt_to_encrypte_data(file_path_list[1])#讀出
        context_secret = client_decrypte.context_decrypt(dict_temp["context_secret"])
        dict_temp_result = client_decrypte.txt_to_encrypte_data(file_path_list[0])#讀出
        output_list = client_decrypte.decrypte_data(context_secret, dict_temp_result)
        download_file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], 'restored_file')
        file_path_with_extension = client_decrypte.binary_to_file(output_list, download_file_path)
        # Extract the filename from the full path
        filename = os.path.basename(file_path_with_extension)
        # 在返回到index.html前触发JavaScript以显示alert，上传成功后，返回一个指示成功上传的消息
        return render_template('index.html', success_message='上傳成功！')
    else:
        return render_template('index.html', success_message='上傳失敗！')

if __name__ == '__main__':
    app.run(debug=True)