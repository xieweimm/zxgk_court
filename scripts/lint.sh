#!/bin/bash
# 快速代码格式化检查

echo "运行代码格式化检查..."

# 检查是否安装了black
if ! command -v black &> /dev/null
then
    echo "错误: black 未安装，请运行 pip install black"
    exit 1
fi

# 运行black
echo "格式化Python代码..."
black src/ tests/ --line-length 88

echo "完成!"
