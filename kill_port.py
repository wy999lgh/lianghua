#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""终止占用指定端口的进程"""
import subprocess
import sys

def kill_port(port):
    try:
        # 查找占用端口的进程
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[4]
                    print(f"找到占用端口 {port} 的进程: PID={pid}")
                    
                    # 终止进程
                    subprocess.run(
                        ['taskkill', '/F', '/PID', pid],
                        capture_output=True
                    )
                    print(f"已终止进程 {pid}")
                    
        print(f"端口 {port} 已释放")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python kill_port.py <端口号>")
        sys.exit(1)
    
    port = sys.argv[1]
    kill_port(port)