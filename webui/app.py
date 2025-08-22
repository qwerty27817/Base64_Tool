import os
import uuid
import shutil
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from base64_tool import encode_file, decode_file, generate_rsa_keys

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB限制
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'dat', 'b64', 'pem'}

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 脚本下载链接
SCRIPT_DOWNLOAD_URL = "https://github.com/qwerty27817/releases"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_unique_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

@app.route('/')
def index():
    return render_template('index.html', script_download_url=SCRIPT_DOWNLOAD_URL)

@app.route('/encode', methods=['POST'])
def encode():
    # 检查文件大小
    if 'file' not in request.files:
        flash('没有选择文件')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('不支持的文件类型')
        return redirect(url_for('index'))
    
    # 处理表单数据
    salt = request.form.get('salt', '')
    compress = 'compress' in request.form
    public_key = request.files.get('public_key')
    
    # 保存输入文件
    input_filename = get_unique_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    file.save(input_path)
    
    # 保存公钥（如果提供）
    public_key_path = None
    if public_key and public_key.filename != '':
        if not public_key.filename.endswith('.pem'):
            flash('公钥必须是PEM格式')
            return redirect(url_for('index'))
        
        public_key_filename = get_unique_filename(public_key.filename)
        public_key_path = os.path.join(app.config['UPLOAD_FOLDER'], public_key_filename)
        public_key.save(public_key_path)
    
    # 创建输出文件路径
    output_filename = f"encoded_{input_filename}.b64"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # 执行编码
    try:
        encode_file(
            input_path, 
            output_path,
            compress=compress,
            salt=salt if salt else None,
            public_key_file=public_key_path
        )
    except Exception as e:
        flash(f'编码失败: {str(e)}')
        return redirect(url_for('index'))
    
    # 返回结果文件
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"encoded_{file.filename}.b64"
    )

@app.route('/decode', methods=['POST'])
def decode():
    # 检查文件
    if 'file' not in request.files:
        flash('没有选择文件')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件')
        return redirect(url_for('index'))
    
    if not file.filename.endswith('.b64'):
        flash('解码文件必须是.b64格式')
        return redirect(url_for('index'))
    
    # 处理表单数据
    salt = request.form.get('salt', '')
    private_key = request.files.get('private_key')
    
    # 保存输入文件
    input_filename = get_unique_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
    file.save(input_path)
    
    # 保存私钥（如果提供）
    private_key_path = None
    if private_key and private_key.filename != '':
        if not private_key.filename.endswith('.pem'):
            flash('私钥必须是PEM格式')
            return redirect(url_for('index'))
        
        private_key_filename = get_unique_filename(private_key.filename)
        private_key_path = os.path.join(app.config['UPLOAD_FOLDER'], private_key_filename)
        private_key.save(private_key_path)
    
    # 创建输出文件路径
    output_filename = f"decoded_{input_filename}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
    
    # 执行解码
    try:
        decode_file(
            input_path, 
            output_path,
            salt=salt if salt else None,
            private_key_file=private_key_path
        )
    except Exception as e:
        flash(f'解码失败: {str(e)}')
        return redirect(url_for('index'))
    
    # 返回结果文件
    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"decoded_{file.filename.replace('.b64', '')}"
    )

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    key_size = int(request.form.get('key_size', 2048))
    
    # 创建临时目录
    temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"keys_{uuid.uuid4().hex}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 生成密钥
    public_path = os.path.join(temp_dir, "public.pem")
    private_path = os.path.join(temp_dir, "private.pem")
    
    generate_rsa_keys(
        key_size=key_size,
        public_key_file=public_path,
        private_key_file=private_path
    )
    
    # 创建ZIP文件
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f"rsa_keys_{uuid.uuid4().hex}.zip")
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
    
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    return send_file(
        f"{zip_path}",
        as_attachment=True,
        download_name="rsa_keys.zip"
    )

if __name__ == '__main__':
    app.run(debug=True)