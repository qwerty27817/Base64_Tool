<h1>Base64文件编解码工具</h1>
<h6>一个完全基于AI的，针对所有文件的Base64编解码，支持盐值，RSA非对称加密，内含RSA密钥生成工具</h6>
<p>AI真的太好用了你们知道吗()</p>
<p>版权信息是随便写的，不必在意</p>
<p>ver.txt存储了当前的版本描述，比如文件内容是Release 1.0.0 那么在--version中就会显示</p>
<blockquote>Base64编解码程序 版本 Release 1.0.0<br>本软件及其附属部分未经许可不得篡改<br>版权没有 QWERTY27817 2025 ,No Right Reserved<br>软件使用AI生成,AI真的太好用了你们知道吗</blockquote>
<h2>使用方法</h2>
<p>--help里面都写了，什么？你说你不想看？那好吧</p>
<p>使用这个工具，你必须要有Python环境</p>
<a href="https://www.python.org/" title="Python官网">点击这里前往Python官网下载</a>
<p>推荐把Python添加到环境变量中</p>
<p>安装好Python后，使用</p>
<code>base64_tool.py --version</code>
<p>查看当前版本，使用</p>
<code>base64_tool.py --help查看帮助</code>
<p>工具主要命令有encode,decode,genkeys</p>
<p>encode作用：编码文件</p>
<p>encode有5个选项，-h,-c,-t,-s,-e</p>
<p>直接上程序输出，懒得写了</p>
<blockquote>
  usage: base64_tool.py encode [-h] [-c] [-t THREADS] [-s SALT] [-e ENCRYPT] input output<br><br>
  positional arguments:<br>
  input                 输入文件路径<br>
  output                输出文件路径
<br>
<br>options:
<br>  -h, --help            show this help message and exit
<br>  -c, --compress        启用压缩
<br>  -t, --threads THREADS
<br>                        指定线程数 (默认使用CPU核心数)
<br>  -s, --salt SALT       加盐值 (字符串)
<br>  -e, --encrypt ENCRYPT
<br>                        RSA公钥文件路径 (启用加密)
</blockquote>
<p>decode基本一样</p>
<blockquote>
  usage: base64_tool.py decode [-h] [-t THREADS] [-s SALT] [-d DECRYPT] input output
<br>
<br>positional arguments:
<br>  input                 输入文件路径
<br>  output                输出文件路径
<br>
<br>options:
<br>  -h, --help            show this help message and exit
<br>  -t, --threads THREADS
<br>                        指定线程数 (默认使用CPU核心数)
<br>  -s, --salt SALT       盐值 (与编码时相同)
<br>  -d, --decrypt DECRYPT
<br>                        RSA私钥文件路径 (启用解密)
</blockquote>
<p>genkeys用来生成RSA密钥对，具体也是直接放输出</p>
<blockquote>
  usage: base64_tool.py genkeys [-h] [-s SIZE] [-pub PUBLIC] [-priv PRIVATE]
<br>
<br>options:
<br>  -h, --help            show this help message and exit
<br>  -s, --size SIZE       密钥大小 (默认: 2048)
<br>  -pub, --public PUBLIC
<br>                        公钥输出文件 (默认: public.pem)
<br>  -priv, --private PRIVATE
<br>                        私钥输出文件 (默认: private.pem)
</blockquote>
<p>但其实genkeys可以无参运行，直接运行会在当前shell所在目录生成private.pem和public.pem，密钥大小为2048位</p>
<p>同时虽然可以，但是不推荐在工具本体以外的shell目录运行，因为版本号抓取的是当前shell目录的ver.txt而不是工具目录的ver.txt，幸好AI做了异常捕捉，会输出未知版本，目前正在与AI交涉，让这个Bug消失</p>
