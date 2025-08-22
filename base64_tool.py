import base64
import zlib
import argparse
import concurrent.futures
import os
import threading
import sys
import datetime

# 尝试导入加密模块
CRYPTO_AVAILABLE = True
try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.Random import get_random_bytes
except ImportError:
    CRYPTO_AVAILABLE = False

# 设置块大小
CHUNK_SIZE = 3 * 1024 * 1024  # 3MB
LENGTH_PREFIX_SIZE = 8        # 长度前缀固定 8 字节

def get_version():
    """获取程序版本号 - 修复路径问题"""
    try:
        # 获取当前脚本所在的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(script_dir, "ver.txt")
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception as e:
        print(f"读取版本文件时出错: {str(e)}")
    return "未知版本"

def print_full_header():
    """打印完整的程序头信息"""
    version = get_version()
    current_year = datetime.datetime.now().year
    print(f"Base64编解码程序 版本 {version}")
    print("本软件及其附属部分未经许可不得篡改")
    print(f"版权没有 QWERTY27817 {current_year} ,No Right Reserved")
    print("软件使用AI生成,AI真的太好用了你们知道吗\n")

def print_version_line():
    """打印一行版本信息"""
    version = get_version()
    print(f"Base64编解码程序 版本 {version}")

def add_salt(data, salt):
    """为数据添加盐值"""
    if not salt:
        return data
    salt_bytes = salt.encode('utf-8')
    return salt_bytes + b'SALT_DELIMITER' + data

def remove_salt(data, salt):
    """从数据中移除盐值"""
    if not salt:
        return data

    salt_bytes = salt.encode('utf-8')
    delimiter = b'SALT_DELIMITER'
    salt_header = salt_bytes + delimiter

    if data.startswith(salt_header):
        return data[len(salt_header):]
    else:
        index = data.find(delimiter)
        if index != -1:
            return data[index + len(delimiter):]
        return data

def rsa_encrypt(data, public_key_file):
    """使用RSA公钥加密数据"""
    if not public_key_file:
        return data

    if not CRYPTO_AVAILABLE:
        print("错误: PyCryptodome模块未安装，无法使用加密功能")
        print("请使用以下命令安装: pip install pycryptodome")
        sys.exit(1)

    try:
        with open(public_key_file, 'rb') as f:
            public_key = RSA.import_key(f.read())
        cipher = PKCS1_OAEP.new(public_key)

        session_key = get_random_bytes(32)
        compressed = zlib.compress(data)
        encrypted_data = session_key + compressed

        encrypted_session_key = cipher.encrypt(session_key)
        return encrypted_session_key + encrypted_data
    except Exception as e:
        print(f"RSA加密失败: {str(e)}")
        return data

def rsa_decrypt(data, private_key_file):
    """使用RSA私钥解密数据"""
    if not private_key_file:
        return data

    if not CRYPTO_AVAILABLE:
        print("错误: PyCryptodome模块未安装，无法使用解密功能")
        print("请使用以下命令安装: pip install pycryptodome")
        sys.exit(1)

    try:
        with open(private_key_file, 'rb') as f:
            private_key = RSA.import_key(f.read())
        cipher = PKCS1_OAEP.new(private_key)

        rsa_key_size = private_key.size_in_bytes()
        encrypted_session_key = data[:rsa_key_size]
        ciphertext = data[rsa_key_size:]

        session_key = cipher.decrypt(encrypted_session_key)
        compressed = ciphertext[len(session_key):]
        return zlib.decompress(compressed)
    except Exception as e:
        print(f"RSA解密失败: {str(e)}")
        return data

def encode_chunk(chunk, compress=False, salt=None, public_key_file=None):
    """编码单个数据块，返回带长度前缀的Base64字节串"""
    try:
        if salt:
            chunk = add_salt(chunk, salt)
        if compress:
            chunk = zlib.compress(chunk)
        if public_key_file:
            chunk = rsa_encrypt(chunk, public_key_file)

        encoded = base64.b64encode(chunk)
        length_str = f"{len(encoded):08d}".encode()
        return length_str + encoded
    except Exception as e:
        print(f"编码块时出错: {str(e)}")
        return None

def decode_chunk(chunk, salt=None, private_key_file=None):
    """解码单个Base64块（已去除长度前缀）"""
    try:
        data = base64.b64decode(chunk)

        if private_key_file:
            data = rsa_decrypt(data, private_key_file)

        try:
            data = zlib.decompress(data)
        except:
            pass

        if salt:
            data = remove_salt(data, salt)

        return data
    except Exception as e:
        print(f"解码块时出错: {str(e)}")
        return None

def encode_file(input_path, output_path, compress=False, threads=None, salt=None, public_key_file=None):
    """编码文件（带长度前缀）"""
    if threads is None:
        threads = os.cpu_count() or 4

    print(f"使用 {threads} 个线程进行编码...")
    if salt:
        print(f"加盐处理: {salt}")
    if public_key_file:
        print(f"使用RSA公钥加密: {public_key_file}")

    try:
        file_size = os.path.getsize(input_path)
        processed = 0
        lock = threading.Lock()

        with open(input_path, 'rb') as f_in, \
             open(output_path, 'wb') as f_out, \
             concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:

            futures = []
            while True:
                chunk = f_in.read(CHUNK_SIZE)
                if not chunk:
                    break
                future = executor.submit(
                    encode_chunk,
                    chunk,
                    compress,
                    salt,
                    public_key_file
                )
                futures.append((future, len(chunk)))

                with lock:
                    processed += len(chunk)
                    percent = (processed / file_size) * 100
                    print(f"\r进度: {percent:.1f}%", end='', flush=True)

            for future, _ in futures:
                encoded_chunk = future.result()
                if encoded_chunk:
                    f_out.write(encoded_chunk)

        print(f"\n文件已成功编码到: {output_path}")

        if compress and not public_key_file:
            orig_size = file_size
            comp_size = os.path.getsize(output_path)
            ratio = (1 - comp_size / orig_size) * 100 if orig_size > 0 else 0
            print(f"压缩效果: {orig_size}字节 -> {comp_size}字节, 节省: {ratio:.2f}%")

    except Exception as e:
        print(f"\n编码过程中出错: {str(e)}")

def decode_file(input_path, output_path, threads=None, salt=None, private_key_file=None):
    """解码文件（按长度前缀读取）"""
    if threads is None:
        threads = os.cpu_count() or 4

    print(f"使用 {threads} 个线程进行解码...")
    if salt:
        print(f"去盐处理: {salt}")
    if private_key_file:
        print(f"使用RSA私钥解密: {private_key_file}")

    try:
        file_size = os.path.getsize(input_path)
        processed = 0
        lock = threading.Lock()

        with open(input_path, 'rb') as f_in, \
             open(output_path, 'wb') as f_out, \
             concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:

            raw_data = f_in.read()
            offset = 0
            futures = []

            while offset + LENGTH_PREFIX_SIZE <= len(raw_data):
                length_str = raw_data[offset:offset + LENGTH_PREFIX_SIZE]
                chunk_len = int(length_str.decode())
                offset += LENGTH_PREFIX_SIZE

                if offset + chunk_len > len(raw_data):
                    break
                chunk_data = raw_data[offset:offset + chunk_len]
                offset += chunk_len

                future = executor.submit(
                    decode_chunk,
                    chunk_data,
                    salt,
                    private_key_file
                )
                futures.append(future)

                with lock:
                    processed = offset
                    percent = min((processed / file_size) * 100, 100)
                    print(f"\r进度: {percent:.1f}%", end='', flush=True)

            for future in futures:
                decoded_chunk = future.result()
                if decoded_chunk:
                    f_out.write(decoded_chunk)

        print(f"\n文件已成功解码到: {output_path}")

    except Exception as e:
        print(f"\n解码过程中出错: {str(e)}")

def generate_rsa_keys(key_size=2048, public_key_file="public.pem", private_key_file="private.pem"):
    """生成RSA密钥对"""
    if not CRYPTO_AVAILABLE:
        print("错误: PyCryptodome模块未安装，无法生成密钥")
        print("请使用以下命令安装: pip install pycryptodome")
        sys.exit(1)

    try:
        key = RSA.generate(key_size)
        private_key = key.export_key()
        public_key = key.publickey().export_key()

        with open(private_key_file, "wb") as f:
            f.write(private_key)
        with open(public_key_file, "wb") as f:
            f.write(public_key)

        print(f"RSA密钥对已生成:")
        print(f"  公钥: {public_key_file}")
        print(f"  私钥: {private_key_file}")
        print(f"密钥大小: {key_size}位")
        print("警告: 请妥善保管私钥文件，不要泄露!")
    except Exception as e:
        print(f"生成RSA密钥失败: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="文件Base64编码/解码工具",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""使用示例:
1. 生成RSA密钥对:
   python %(prog)s genkeys -s 4096 -pub public.pem -priv private.pem

2. 编码文件(加盐+加密+压缩):
   python %(prog)s encode input.dat output.b64 -c -s "MySecretSalt" -e public.pem

3. 解码文件(去盐+解密):
   python %(prog)s decode output.b64 restored.dat -s "MySecretSalt" -d private.pem

4. 仅加盐编码:
   python %(prog)s encode input.jpg output.b64 -s "SimpleSalt"

5. 仅加密编码:
   python %(prog)s encode document.pdf output.b64 -e public.pem

6. 仅压缩编码:
   python %(prog)s encode video.mp4 output.b64 -c

7. 基本解码:
   python %(prog)s decode output.b64 restored_file

注意事项:
- 加盐值在编码和解码时必须一致
- 加密需要公钥文件，解密需要私钥文件
- 私钥必须严格保密"""
    )

    parser.add_argument('-v', '--version', action='store_true',
                       help='显示完整的程序版本信息')

    subparsers = parser.add_subparsers(dest='command', required=False, title="可用命令")

    encode_parser = subparsers.add_parser('encode', help='编码文件')
    encode_parser.add_argument('input', help='输入文件路径')
    encode_parser.add_argument('output', help='输出文件路径')
    encode_parser.add_argument('-c', '--compress', action='store_true',
                              help='启用压缩')
    encode_parser.add_argument('-t', '--threads', type=int,
                              help='指定线程数 (默认使用CPU核心数)')
    encode_parser.add_argument('-s', '--salt', type=str,
                              help='加盐值 (字符串)')
    encode_parser.add_argument('-e', '--encrypt', type=str,
                              help='RSA公钥文件路径 (启用加密)')

    decode_parser = subparsers.add_parser('decode', help='解码文件')
    decode_parser.add_argument('input', help='输入文件路径')
    decode_parser.add_argument('output', help='输出文件路径')
    decode_parser.add_argument('-t', '--threads', type=int,
                              help='指定线程数 (默认使用CPU核心数)')
    decode_parser.add_argument('-s', '--salt', type=str,
                              help='盐值 (与编码时相同)')
    decode_parser.add_argument('-d', '--decrypt', type=str,
                              help='RSA私钥文件路径 (启用解密)')

    keygen_parser = subparsers.add_parser('genkeys', help='生成RSA密钥对')
    keygen_parser.add_argument('-s', '--size', type=int, default=2048,
                              help='密钥大小 (默认: 2048)')
    keygen_parser.add_argument('-pub', '--public', type=str, default="public.pem",
                              help='公钥输出文件 (默认: public.pem)')
    keygen_parser.add_argument('-priv', '--private', type=str, default="private.pem",
                              help='私钥输出文件 (默认: private.pem)')

    args = parser.parse_args()

    if args.version:
        print_full_header()
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    print_version_line()

    if args.command == 'encode':
        encode_file(
            args.input,
            args.output,
            args.compress,
            args.threads,
            args.salt,
            args.encrypt
        )
    elif args.command == 'decode':
        decode_file(
            args.input,
            args.output,
            args.threads,
            args.salt,
            args.decrypt
        )
    elif args.command == 'genkeys':
        generate_rsa_keys(
            args.size,
            args.public,
            args.private
        )

if __name__ == "__main__":
    main()