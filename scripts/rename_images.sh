#!/bin/bash

if [ $# -ne 2 ]; then
    echo "사용법: $0 <폴더경로> <파일명접두사>"
    echo "예시: $0 ./images photo"
    exit 1
fi

FOLDER="$1"
PREFIX="$2"

if [ ! -d "$FOLDER" ]; then
    echo "오류: 폴더를 찾을 수 없습니다 - $FOLDER"
    exit 1
fi

counter=1

for file in "$FOLDER"/*.{jpg,jpeg,png,gif,bmp,JPG,JPEG,PNG,GIF,BMP} 2>/dev/null; do
    if [ -f "$file" ]; then
        ext="${file##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
        new_name=$(printf "%s/%s-%04d.%s" "$FOLDER" "$PREFIX" "$counter" "$ext")
        
        if [ "$file" != "$new_name" ]; then
            mv "$file" "$new_name"
            echo "변경: $(basename "$file") -> $(basename "$new_name")"
        fi
        ((counter++))
    fi
done

echo "완료: $((counter-1))개 파일 이름 변경됨"