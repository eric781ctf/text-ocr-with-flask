import os
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, url_for, send_from_directory
from cnocr import CnOcr
import cv2
import numpy as np

app = Flask(__name__)

# 設定上傳資料夾
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

# 副檔名驗證函式
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 初始化 OCR 模型
ocr = CnOcr()

def draw_ocr_results(image_path, results, output_path):
    # 使用 OpenCV 載入影像並轉為 PIL 圖像
    cv_img = cv2.imread(image_path)
    img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)

    # 自訂字體路徑（系統中文字體）
    font_path = "C:\\Windows\\Fonts\\msjh.ttc"
    try:
        font = ImageFont.truetype(font_path, size=20)
    except:
        font = ImageFont.load_default()

    for r in results:
        box = r['position']
        text = r['text']

        x0, y0 = box[0]
        x1, y1 = box[1]
        x_min, x_max = sorted([x0, x1])
        y_min, y_max = sorted([y0, y1])

        draw.rectangle([(x_min, y_min), (x_max, y_max)], outline="lime", width=2)
        draw.text((x_min, y_min - 22), text, font=font, fill="blue")

    # 儲存成 OpenCV 圖片格式
    final_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_path, final_img)

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            results = ocr.ocr(filepath)

            output_filename = f'output_{filename}'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            draw_ocr_results(filepath, results, output_path)

            return render_template('upload.html',
                                   original_image=url_for('uploaded_file', filename=filename),
                                   result_image=url_for('uploaded_file', filename=output_filename),
                                   error=None)
        else:
            return render_template('upload.html', error="請上傳有效的圖片檔案（png/jpg/jpeg/bmp/gif）")

    return render_template('upload.html', error=None)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
