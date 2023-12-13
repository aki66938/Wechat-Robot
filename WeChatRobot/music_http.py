import os
import http.server
import socketserver
import threading
from my_ip import get_public_ip

class HttpServer:
    '''
    http实例开关
    '''
    def __init__(self, port=8000, directory='.'):
        self.port = port
        self.directory = directory
        self.httpd = None
        self.thread = None
        self.ip_update_thread = None
        self.current_ip = None

    def start(self):
        if self.httpd is not None:
            content = "HTTP服务已经在干活了，别催了！！！"
            return content

        class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path):
                # 覆写 translate_path 方法
                path = super().translate_path(path)
                rel_path = os.path.relpath(path, os.getcwd())
                return os.path.join(self.server.directory, rel_path)

        self.httpd = socketserver.TCPServer(("", self.port), HttpRequestHandler)
        self.httpd.directory = self.directory  # 设置目录
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        self.current_ip = get_public_ip()  # 初始IP获取
        self.start_ip_update_timer()  # 开始定时更新IP地址

        content = "http://{self.current_ip}:{self.port}"
        return content

    def start_ip_update_timer(self):
        # 每10分钟重新获取一次IP地址
        self.ip_update_thread = threading.Timer(600, self.update_ip)
        self.ip_update_thread.daemon = True
        self.ip_update_thread.start()

    def update_ip(self):
        self.current_ip = get_public_ip()
        self.start_ip_update_timer()  # 重新启动定时器

    def stop(self):
        if self.httpd is None:
            content = "HTTP罢工不干了，自己找找原因！"
            return content

        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join()  # 等待线程结束
        self.httpd = None
        self.thread = None
        if self.ip_update_thread:
            self.ip_update_thread.cancel()  # 停止IP更新定时器
        self.ip_update_thread = None
        content = "欺负我只是个HTTP，不给你放歌听了(˚ ˃̣̣̥᷄⌓˂̣̣̥᷅ )" 
        return content
