#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端服务主入口
"""

import uvicorn

from api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
